"""Pruebas de flujo.  Ejecutar:  python -m unittest discover tests"""
import io
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import inspect, text

from app import _migrar_datos_viejos, create_app
from app.extensions import db
from app.models import ROL_ADMIN, Actividad, Evento, Inscripcion, Usuario
from app.services import directorio
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class CampusViveTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.fotos = tempfile.TemporaryDirectory()  # las fotos subidas en pruebas no tocan static/
        self.app.config["CARPETA_FOTOS"] = Path(self.fotos.name)
        self.ctx = self.app.app_context()
        self.ctx.push()
        admin = Usuario(nombre="Bienestar", correo="admin@unimilitar.edu.co", rol=ROL_ADMIN)
        admin.set_clave("adminclave")
        db.session.add(admin)
        db.session.commit()
        self.c = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.fotos.cleanup()

    def registrar(self, nombre, correo, onboarding=True):
        self.c.post("/registro", data={"nombre": nombre, "correo": correo,
                                       "clave": "12345678", "clave2": "12345678"})
        if onboarding:
            self.c.post("/bienvenida", data={"intereses": ["artes"]})
        self.c.get("/logout")

    def login(self, correo, clave="12345678"):
        return self.c.post("/login", data={"correo": correo, "clave": clave})

    def test_login_es_la_primera_pantalla_y_bienvenida_solo_una_vez(self):
        self.assertIn("/login", self.c.get("/").headers["Location"])
        self.registrar("Ana", "ana@unimilitar.edu.co")
        r = self.login("ana@unimilitar.edu.co")
        self.assertEqual(r.headers["Location"], "/")  # segundo ingreso: sin bienvenida
        self.assertEqual(self.c.get("/bienvenida").headers["Location"], "/")

    def test_estudiante_no_entra_al_panel(self):
        self.registrar("Ana", "ana@unimilitar.edu.co")
        self.login("ana@unimilitar.edu.co")
        self.assertEqual(self.c.get("/admin/usuarios").headers["Location"], "/")

    def test_crud_actividad_y_slug_unico(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        datos = {"nombre": "Ajedrez Ágil", "categoria": "recreacion", "cupos_total": "2",
                 "dias": ["Martes", "Lunes"], "desde": "12:00", "hasta": "14:30"}
        self.c.post("/admin/actividades/nueva", data=datos)
        self.c.post("/admin/actividades/nueva", data=datos)
        slugs = [a.slug for a in Actividad.query.filter_by(nombre="Ajedrez Ágil")]
        self.assertEqual(sorted(slugs), ["ajedrez-agil", "ajedrez-agil-2"])

        a = Actividad.query.filter_by(slug="ajedrez-agil").one()
        self.assertEqual(a.horario, "Lunes 12:00 – 14:30\nMartes 12:00 – 14:30")  # 24 h, orden de la semana
        r = self.c.post(f"/admin/actividades/{a.id}/editar", data={**datos, "cupos_total": "0"})
        self.assertIn("entre 1 y 1000", r.get_data(as_text=True))
        self.c.post(f"/admin/actividades/{a.id}/editar", data={**datos, "nombre": "Ajedrez", "destacada": "on"})
        db.session.refresh(a)
        self.assertEqual((a.nombre, a.slug, a.destacada), ("Ajedrez", "ajedrez", True))

    def test_agregar_y_quitar_inscritos_respeta_cupos(self):
        self.registrar("Ana", "ana@unimilitar.edu.co")
        self.registrar("Beto", "beto@unimilitar.edu.co")
        ana, beto = Usuario.query.filter_by(rol="estudiante").order_by(Usuario.nombre).all()
        self.login("admin@unimilitar.edu.co", "adminclave")
        self.c.post("/admin/actividades/nueva", data={"nombre": "Coro chico", "categoria": "cultura", "cupos_total": "1"})
        act = Actividad.query.filter_by(nombre="Coro chico").one()

        self.c.post(f"/admin/actividades/{act.id}/inscritos", data={"usuario_id": ana.id})
        r = self.c.post(f"/admin/actividades/{act.id}/inscritos", data={"usuario_id": beto.id},
                        follow_redirects=True)
        self.assertIn("No quedan cupos", r.get_data(as_text=True))
        self.assertEqual([i.usuario_id for i in act.inscripciones], [ana.id])

        ins = act.inscripciones[0]
        self.c.post(f"/admin/inscripciones/{ins.id}/quitar", data={"volver": "//evil.com"})
        self.assertEqual(Inscripcion.query.count(), 0)

    def test_evento_toma_categoria_de_actividad_y_sobrevive_al_borrarla(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        act = Actividad.query.filter_by(slug="fotografia").one()
        r = self.c.post("/admin/eventos/nuevo", data={"nombre": "Mal", "lugar": "X", "fecha": "31-02-2026",
                                                       "hora": "10:00", "categoria": "deporte"})
        self.assertIn("Fecha u hora inválida", r.get_data(as_text=True))
        self.c.post("/admin/eventos/nuevo", data={"nombre": "Salida foto", "lugar": "Plazoleta",
                                                  "fecha": "2026-12-01", "hora": "09:30",
                                                  "categoria": "deporte", "actividad_id": act.id})
        ev = Evento.query.filter_by(nombre="Salida foto").one()
        self.assertEqual(ev.categoria, "artes")
        self.assertIn("Salida foto", self.c.get("/calendario").get_data(as_text=True))

        self.c.post(f"/admin/actividades/{act.id}/eliminar")
        db.session.refresh(ev)
        self.assertIsNone(ev.actividad_id)

    def test_registro_de_usuarios_lista_todos(self):
        self.registrar("Ana", "ana@unimilitar.edu.co")
        self.registrar("Nuevo", "nuevo@unimilitar.edu.co", onboarding=False)
        self.login("admin@unimilitar.edu.co", "adminclave")
        html = self.c.get("/admin/usuarios").get_data(as_text=True)
        for texto in ("ana@unimilitar.edu.co", "nuevo@unimilitar.edu.co", "admin@unimilitar.edu.co",
                      "Sin completar bienvenida"):
            self.assertIn(texto, html)

    def test_mapa_marca_la_actividad_aunque_se_renombre(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        self.c.post("/admin/actividades/1/editar",
                    data={"nombre": "Fútbol Mixto", "categoria": "deporte", "cupos_total": "20"})
        html = self.c.get("/mapa?actividad=futbol-mixto").get_data(as_text=True)
        self.assertIn("left: 25.2%; top: 60.0%", html)
        self.assertNotIn("cv-mapa-pin", self.c.get("/mapa").get_data(as_text=True))
        self.assertIn("img/actividades/futbol-umng.jpg",  # la foto también sobrevive al renombre
                      self.c.get("/actividad/futbol-mixto").get_data(as_text=True))

    def test_admin_ubica_la_actividad_en_el_mapa(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        self.assertIn('id="mapaAdmin"', self.c.get("/admin/actividades/nueva").get_data(as_text=True))

        datos = {"nombre": "Ajedrez", "categoria": "recreacion", "cupos_total": "10"}
        r = self.c.post("/admin/actividades/nueva", data={**datos, "mapa_x": "150", "mapa_y": "20"})
        self.assertIn("punto del mapa no es válido", r.get_data(as_text=True))
        self.c.post("/admin/actividades/nueva", data={**datos, "mapa_x": "40.04", "mapa_y": "22.5"})
        a = Actividad.query.filter_by(slug="ajedrez").one()
        self.assertEqual((a.mapa_x, a.mapa_y), (40.0, 22.5))
        self.c.get("/logout")

        self.registrar("Ana", "ana@unimilitar.edu.co")
        self.login("ana@unimilitar.edu.co")
        self.assertIn("left: 40.0%; top: 22.5%", self.c.get("/mapa?actividad=ajedrez").get_data(as_text=True))

    def test_bd_vieja_se_actualiza_al_arrancar(self):
        # Simula una BD de antes: columna obligatoria que ya no está en el modelo y horario en 12 h.
        db.session.execute(text("ALTER TABLE actividad ADD COLUMN nivel VARCHAR(40) NOT NULL DEFAULT 'x'"))
        a = db.session.get(Actividad, 2)
        a.horario = "Martes 2:00 p.m. – 4:00 p.m.\nViernes 12:00 m. – 12:30 p.m.\nSábados (salida) 7:00 a.m."
        db.session.commit()
        _migrar_datos_viejos()
        self.assertNotIn("nivel", [c["name"] for c in inspect(db.engine).get_columns("actividad")])
        self.assertEqual(db.session.get(Actividad, 2).horario,
                         "Martes 14:00 – 16:00\nViernes 12:00 – 12:30\nSábados (salida) 07:00")
        _migrar_datos_viejos()  # una segunda vez no cambia nada
        self.assertIn("Martes 14:00 – 16:00", db.session.get(Actividad, 2).horario)

    def test_horas_en_24h(self):
        self.registrar("Ana", "ana@unimilitar.edu.co")
        self.login("ana@unimilitar.edu.co")
        self.assertIn("17:00", self.c.get("/calendario").get_data(as_text=True))  # Festival Cultural
        self.assertIn("Lunes 18:00 – 20:00", self.c.get("/actividad/danza-contemporanea").get_data(as_text=True))

    def test_horario_con_selectores(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        base = {"categoria": "cultura", "cupos_total": "10"}
        # Danza (id 5): mismas horas lunes y jueves → los selectores vienen marcados.
        form = self.c.get("/admin/actividades/5/editar").get_data(as_text=True)
        self.assertIn('value="Lunes" class="visually-hidden" checked', form)
        self.assertIn('<option value="18:00" selected>', form)
        # Fin antes del inicio → error y no se guarda.
        r = self.c.post("/admin/actividades/5/editar", data={**base, "nombre": "Danza Contemporánea",
                        "dias": ["Lunes"], "desde": "18:00", "hasta": "17:00"})
        self.assertIn("posterior a la de inicio", r.get_data(as_text=True))
        # Yoga (id 7) tiene horas distintas por día y Explora (id 4) texto libre: sin días se conservan.
        for id_, nombre in [(7, "Yoga y Bienestar"), (4, "Explora Naturaleza")]:
            antes = db.session.get(Actividad, id_).horario
            self.assertIn("Horario actual", self.c.get(f"/admin/actividades/{id_}/editar").get_data(as_text=True))
            self.c.post(f"/admin/actividades/{id_}/editar", data={**base, "nombre": nombre})
            self.assertEqual(db.session.get(Actividad, id_).horario, antes)

    def test_foto_opcional_de_actividad(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        datos = {"nombre": "Ajedrez", "categoria": "recreacion", "cupos_total": "10"}
        r = self.c.post("/admin/actividades/nueva", data={**datos, "foto": (io.BytesIO(b"<script>"), "x.jpg")},
                        content_type="multipart/form-data")
        self.assertIn("JPG, PNG o WEBP", r.get_data(as_text=True))  # se mira el contenido, no el nombre
        self.c.post("/admin/actividades/nueva", content_type="multipart/form-data",
                    data={**datos, "foto": (io.BytesIO(b"\xff\xd8\xff" + b"0" * 50), "mi foto.jpg")})
        a = Actividad.query.filter_by(slug="ajedrez").one()
        self.assertRegex(a.imagen, r"^subidas/[0-9a-f]{16}\.jpg$")
        primera = Path(self.fotos.name) / a.imagen
        self.assertTrue(primera.exists())

        self.c.post(f"/admin/actividades/{a.id}/editar", content_type="multipart/form-data",
                    data={**datos, "foto": (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 50), "otra.png")})
        db.session.refresh(a)
        self.assertTrue(a.imagen.endswith(".png"))
        self.assertFalse(primera.exists())  # la foto reemplazada se borra
        self.c.post(f"/admin/actividades/{a.id}/editar", data={**datos, "quitar_foto": "on"})
        db.session.refresh(a)
        self.assertIsNone(a.imagen)
        self.assertEqual(list(Path(self.fotos.name, "subidas").iterdir()), [])
        # Sin foto subida, las de ejemplo siguen saliendo.
        self.assertIn("img/actividades/danza-contemporanea.jpg",
                      self.c.get("/admin/actividades/5/editar").get_data(as_text=True))

    def test_bienvenida_muestra_el_mapa_con_un_marcador_por_lugar(self):
        self.registrar("Ana", "ana@unimilitar.edu.co", onboarding=False)
        self.login("ana@unimilitar.edu.co")
        html = self.c.get("/bienvenida").get_data(as_text=True)
        self.assertEqual(html.count('class="cv-mapa-pin"'), 5)  # 10 actividades en 5 lugares
        self.assertIn('aria-label="Coro UMNG, Fotografía, Guitarra Acústica"', html)
        self.assertIn('data-categorias="cultura artes"', html)  # para filtrar por intereses

    def test_datos_academicos_se_sincronizan_al_ingresar(self):
        self.registrar("Ana", "ana@unimilitar.edu.co")
        ana = Usuario.query.filter_by(correo="ana@unimilitar.edu.co").one()
        esperado = directorio.consultar("ana@unimilitar.edu.co")
        self.assertEqual((ana.codigo, ana.carrera, ana.semestre),
                         (esperado["codigo"], esperado["carrera"], esperado["semestre"]))
        self.assertTrue(1 <= ana.semestre <= 10)

        ana.carrera = "Desactualizada"
        db.session.commit()
        self.login("ana@unimilitar.edu.co")
        db.session.refresh(ana)
        self.assertEqual(ana.carrera, esperado["carrera"])  # el ingreso la vuelve a traer
        self.c.get("/logout")

        self.login("admin@unimilitar.edu.co", "adminclave")
        self.assertIsNone(Usuario.query.filter_by(rol=ROL_ADMIN).one().codigo)
        self.assertIn(ana.codigo, self.c.get("/admin/usuarios").get_data(as_text=True))

    def test_perfil_muestra_datos_y_foto(self):
        self.registrar("Ana María Rojas", "ana@unimilitar.edu.co")
        self.login("ana@unimilitar.edu.co")
        ana = Usuario.query.filter_by(correo="ana@unimilitar.edu.co").one()
        html = self.c.get("/perfil").get_data(as_text=True)
        for texto in (ana.codigo, ana.carrera, "AM", 'href="/perfil"'):
            self.assertIn(texto, html)
        ana.foto = "https://fotos.ejemplo/ana.jpg"
        db.session.commit()
        self.assertIn('src="https://fotos.ejemplo/ana.jpg"', self.c.get("/perfil").get_data(as_text=True))

    def test_reporte_csv(self):
        self.login("admin@unimilitar.edu.co", "adminclave")
        r = self.c.get("/admin/reporte.csv")
        self.assertEqual(r.mimetype, "text/csv")
        self.assertIn("Fútbol UMNG", r.get_data().decode("utf-8-sig"))


if __name__ == "__main__":
    unittest.main()
