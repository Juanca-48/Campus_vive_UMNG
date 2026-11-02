"""Pruebas de flujo.  Ejecutar:  python -m unittest discover tests"""
import unittest

from app import create_app
from app.extensions import db
from app.models import ROL_ADMIN, Actividad, Evento, Inscripcion, Usuario
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class CampusViveTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
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
                 "horario": "Lunes 2 p.m.\n\nMartes 2 p.m."}
        self.c.post("/admin/actividades/nueva", data=datos)
        self.c.post("/admin/actividades/nueva", data=datos)
        slugs = [a.slug for a in Actividad.query.filter_by(nombre="Ajedrez Ágil")]
        self.assertEqual(sorted(slugs), ["ajedrez-agil", "ajedrez-agil-2"])

        a = Actividad.query.filter_by(slug="ajedrez-agil").one()
        self.assertEqual(a.horario, "Lunes 2 p.m.\nMartes 2 p.m.")
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


if __name__ == "__main__":
    unittest.main()
