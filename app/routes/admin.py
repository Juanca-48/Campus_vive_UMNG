"""Panel de Bienestar Universitario: actividades, calendario, inscritos y usuarios."""

import csv
import io
import re
import unicodedata
import uuid
from datetime import date, time

from flask import Blueprint, Response, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import (ESTADO_APROBADA, ESTADO_PENDIENTE, ESTADO_RECHAZADA, ROL_ESTUDIANTE,
                        Actividad, Evento, Inscripcion, Usuario)
from app.routes.auth import _destino_seguro
from app.services import catalogo, sesion

bp = Blueprint("admin", __name__)

ACCIONES = {"aprobar": ESTADO_APROBADA, "rechazar": ESTADO_RECHAZADA, "pendiente": ESTADO_PENDIENTE}
ETIQUETAS = ["", "Popular", "Nuevo"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
HORAS = [f"{h:02d}:{m:02d}" for h in range(6, 23) for m in (0, 30)][:-1]  # 06:00 … 22:00
FOTO_MAX = 2 * 1024 * 1024


@bp.before_request
@sesion.admin_requerido
def exigir_admin():
    return None


def _volver(por_defecto):
    return redirect(_destino_seguro(request.form.get("volver")) or por_defecto)


def _slug(texto, excluir_id=None):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    base = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-") or "actividad"
    slug, n = base, 2
    while Actividad.query.filter(Actividad.slug == slug, Actividad.id != excluir_id).first():
        slug, n = f"{base}-{n}", n + 1
    return slug


# --- resumen y estadísticas --------------------------------------------------------

def _estadisticas():
    actividades = catalogo.get_actividades()
    for a in actividades:
        ocupados = a["cupos_total"] - a["cupos_disponibles"]
        a["ocupacion_pct"] = round(ocupados / a["cupos_total"] * 100) if a["cupos_total"] else 0

    ranking = sorted(actividades, key=lambda a: (a["miembros"], a["pendientes"], a["ocupacion_pct"]), reverse=True)
    mas_concurridas = ranking[:3]
    menos_concurridas = sorted(actividades, key=lambda a: (a["miembros"], a["pendientes"], a["ocupacion_pct"]))[:3]

    total_aprobados = sum(a["miembros"] for a in actividades)
    total_pendientes = sum(a["pendientes"] for a in actividades)

    por_categoria = []
    for cat in catalogo.get_categorias():
        grupo = [a for a in actividades if a["categoria"] == cat["slug"]]
        aprobados = sum(a["miembros"] for a in grupo)
        pendientes = sum(a["pendientes"] for a in grupo)
        por_categoria.append({
            **cat,
            "actividades": len(grupo),
            "aprobados": aprobados,
            "pendientes": pendientes,
            "porcentaje": round(aprobados / total_aprobados * 100) if total_aprobados else 0,
        })

    return {
        "ranking": ranking,
        "mas_concurridas": mas_concurridas,
        "menos_concurridas": menos_concurridas,
        "por_categoria": por_categoria,
        "total_aprobados": total_aprobados,
        "total_pendientes": total_pendientes,
    }


@bp.route("/")
def panel():
    stats = _estadisticas()
    pendientes = (Inscripcion.query.filter_by(estado=ESTADO_PENDIENTE)
                  .order_by(Inscripcion.creada_en).all())
    resumen = {
        "estudiantes": Usuario.query.filter_by(rol=ROL_ESTUDIANTE).count(),
        "pendientes": len(pendientes),
        "actividades": len(stats["ranking"]),
        "eventos": Evento.query.filter(Evento.fecha >= date.today()).count(),
        "aprobados": stats["total_aprobados"],
    }
    return render_template("admin/panel.html", pendientes=pendientes, resumen=resumen, stats=stats)


@bp.route("/reporte.csv")
def reporte_csv():
    stats = _estadisticas()
    estudiantes = Usuario.query.filter_by(rol=ROL_ESTUDIANTE).count()
    eventos_prox = Evento.query.filter(Evento.fecha >= date.today()).count()
    inscripciones = Inscripcion.query.order_by(Inscripcion.creada_en.desc()).all()

    salida = io.StringIO()
    writer = csv.writer(salida)

    # 1. Resumen general
    writer.writerow(["REPORTE GENERAL - CAMPUS VIVE UMNG"])
    writer.writerow(["Fecha de generacion", date.today().isoformat()])
    writer.writerow(["Estudiantes registrados", estudiantes])
    writer.writerow(["Actividades activas", len(stats["ranking"])])
    writer.writerow(["Inscripciones aprobadas", stats["total_aprobados"]])
    writer.writerow(["Solicitudes pendientes", stats["total_pendientes"]])
    writer.writerow(["Proximos eventos", eventos_prox])
    if stats["mas_concurridas"]:
        top = stats["mas_concurridas"][0]
        low = stats["menos_concurridas"][0]
        writer.writerow(["Actividad mas concurrida", f"{top['nombre']} ({top['miembros']} aprobados)"])
        writer.writerow(["Actividad menos concurrida", f"{low['nombre']} ({low['miembros']} aprobados)"])
    writer.writerow([])

    # 2. Estadisticas por actividad (de mayor a menor concurrencia)
    writer.writerow(["ESTADISTICAS POR ACTIVIDAD (MAS A MENOS CONCURRIDAS)"])
    writer.writerow(["Actividad", "Categoria", "Responsable", "Lugar", "Sede",
                     "Aprobados", "Pendientes", "Cupos totales", "Cupos disponibles", "Ocupacion (%)"])
    for a in stats["ranking"]:
        writer.writerow([
            a["nombre"], a["cat"]["nombre"], a["responsable"],
            a["ubicacion"]["nombre"], a["ubicacion"]["sede"],
            a["miembros"], a["pendientes"], a["cupos_total"],
            a["cupos_disponibles"], f"{a['ocupacion_pct']}%",
        ])
    writer.writerow([])

    # 3. Resumen por categoria
    writer.writerow(["RESUMEN POR CATEGORIA"])
    writer.writerow(["Categoria", "Cantidad de actividades", "Aprobados", "Pendientes", "Participacion (%)"])
    for c in stats["por_categoria"]:
        writer.writerow([c["nombre"], c["actividades"], c["aprobados"], c["pendientes"], f"{c['porcentaje']}%"])
    writer.writerow([])

    # 4. Detalle de inscripciones
    writer.writerow(["DETALLE DE INSCRIPCIONES"])
    writer.writerow(["Actividad", "Estudiante", "Correo", "Codigo", "Carrera", "Semestre",
                     "Estado", "Fecha de solicitud"])
    for ins in inscripciones:
        u = ins.usuario
        writer.writerow([
            ins.actividad.nombre, u.nombre, u.correo, u.codigo or "", u.carrera or "", u.semestre or "",
            ins.estado, ins.creada_en.strftime("%Y-%m-%d %H:%M"),
        ])

    contenido = salida.getvalue().encode("utf-8-sig")  # BOM para que Excel lea bien tildes y ñ
    nombre_archivo = f"reporte_campus_vive_{date.today().isoformat()}.csv"
    return Response(
        contenido,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={nombre_archivo}"},
    )


# --- actividades -------------------------------------------------------------------

@bp.route("/actividades")
def actividades():
    return render_template("admin/actividades.html", actividades=catalogo.get_actividades())


# --- horario: se guarda como texto, una franja por línea en 24 h ("Lunes 16:00 – 18:00") ---------

_FRANJA = re.compile(r"^(\S+) (\d{2}:\d{2}) – (\d{2}:\d{2})$")


def _leer_horario(texto):
    """(días, desde, hasta) si el horario cabe en los selectores (mismas horas todos los días);
    None si no (texto libre o rangos distintos), para no reescribirlo sin querer."""
    dias, rangos = [], set()
    for linea in filter(None, (l.strip() for l in (texto or "").splitlines())):
        m = _FRANJA.match(linea)
        if not m or m[1] not in DIAS:
            return None
        dias.append(m[1])
        rangos.add((m[2], m[3]))
    if not rangos:
        return ([], "", "")
    rango = rangos.pop()
    return (dias, *rango) if not rangos and set(rango) <= set(HORAS) else None


def _horario_del_form(actividad, errores):
    """Texto del horario según los selectores; None = conservar el actual."""
    f = request.form
    dias = [d for d in DIAS if d in f.getlist("dias")]
    desde, hasta = f.get("desde", ""), f.get("hasta", "")
    if not dias:
        # Sin días: si el horario actual era editable con los selectores, se vacía; si era texto libre, se conserva.
        return "" if _leer_horario(actividad.horario) is not None else None
    if desde not in HORAS or hasta not in HORAS or hasta <= desde:
        errores.append("Elige el horario: la hora de fin debe ser posterior a la de inicio.")
        return None
    return "\n".join(f"{d} {desde} – {hasta}" for d in dias)


# --- foto opcional ------------------------------------------------------------------------------

def _leer_foto(errores):
    """(bytes, extensión, tipo MIME) de la foto subida, o None. El tipo se mira en el contenido, no en el nombre."""
    archivo = request.files.get("foto")
    if not archivo or not archivo.filename:
        return None
    datos = archivo.read(FOTO_MAX + 1)
    if len(datos) > FOTO_MAX:
        errores.append("La foto pesa más de 2 MB; redúcela antes de subirla.")
        return None
    if datos.startswith(b"\xff\xd8\xff"):
        return datos, "jpg", "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return datos, "png", "image/png"
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return datos, "webp", "image/webp"
    errores.append("La foto debe ser JPG, PNG o WEBP.")
    return None


def _guardar_actividad(actividad):
    """Valida el formulario y copia los datos en `actividad`. Devuelve la lista de errores."""
    f = request.form
    errores = []
    nombre = f.get("nombre", "").strip()
    if not nombre:
        errores.append("El nombre es obligatorio.")
    if not catalogo.get_categoria(f.get("categoria")):
        errores.append("Elige una categoría válida.")
    try:
        cupos = int(f.get("cupos_total", ""))
        if not 1 <= cupos <= 1000:
            raise ValueError
    except ValueError:
        errores.append("Los cupos deben ser un número entre 1 y 1000.")
        cupos = actividad.cupos_total
    punto = None  # vacío = la actividad aún no tiene lugar en el mapa
    if f.get("mapa_x") or f.get("mapa_y"):
        try:
            punto = (round(float(f["mapa_x"]), 1), round(float(f["mapa_y"]), 1))
            if not all(0 <= c <= 100 for c in punto):
                raise ValueError
        except (KeyError, ValueError):
            errores.append("El punto del mapa no es válido; vuelve a marcarlo.")
    horario = _horario_del_form(actividad, errores)
    foto = _leer_foto(errores)
    if errores:
        return errores

    actividad.nombre = nombre
    actividad.slug = _slug(nombre, excluir_id=actividad.id)
    actividad.categoria = f["categoria"]
    actividad.descripcion = f.get("descripcion", "").strip()[:255]
    actividad.detalle = f.get("detalle", "").strip()
    if punto:
        actividad.mapa_x, actividad.mapa_y = punto
    actividad.cupos_total = cupos
    if horario is not None:
        actividad.horario = horario
    if foto:  # nombre nuevo en cada subida para que la caché del navegador no muestre la vieja
        datos, ext, actividad.imagen_tipo = foto
        actividad.imagen, actividad.imagen_datos = f"{uuid.uuid4().hex[:16]}.{ext}", datos
    elif "quitar_foto" in f:
        actividad.imagen = actividad.imagen_tipo = actividad.imagen_datos = None
    actividad.responsable = f.get("responsable", "").strip()
    actividad.lugar = f.get("lugar", "").strip()
    actividad.sede = f.get("sede", "").strip() or "Calle 100"
    actividad.etiqueta = f.get("etiqueta") if f.get("etiqueta") in ETIQUETAS[1:] else None
    actividad.destacada = "destacada" in f
    return []


@bp.route("/actividades/nueva", methods=["GET", "POST"])
@bp.route("/actividades/<int:actividad_id>/editar", methods=["GET", "POST"])
def actividad_form(actividad_id=None):
    actividad = db.get_or_404(Actividad, actividad_id) if actividad_id else Actividad(cupos_total=20)
    if request.method == "POST":
        errores = _guardar_actividad(actividad)
        if not errores:
            if actividad_id is None:
                db.session.add(actividad)
            db.session.commit()
            flash(f"Actividad «{actividad.nombre}» guardada.", "success")
            return redirect(url_for("admin.actividades"))
        db.session.rollback()
        for e in errores:
            flash(e, "danger")
    # Punto a mostrar: el recién marcado si el envío falló; si no, el guardado o el de ejemplo.
    f = request.form
    punto = (f["mapa_x"], f["mapa_y"]) if f.get("mapa_x") and f.get("mapa_y") else catalogo.punto_mapa(actividad)
    # Horario a mostrar: lo enviado si falló; si no, el guardado leído en días y horas.
    if f:
        horario = (f.getlist("dias"), f.get("desde", ""), f.get("hasta", ""))
    else:
        horario = _leer_horario(actividad.horario)
    return render_template("admin/actividad_form.html", actividad=actividad, form=f,
                           etiquetas=ETIQUETAS, punto=punto, dias=DIAS, horas=HORAS,
                           horario=horario or ([], "", ""),
                           horario_libre=actividad.horario if _leer_horario(actividad.horario) is None else None,
                           foto_actual=catalogo.url_foto(actividad))


@bp.route("/actividades/<int:actividad_id>/eliminar", methods=["POST"])
def actividad_eliminar(actividad_id):
    actividad = db.get_or_404(Actividad, actividad_id)
    for evento in actividad.eventos:
        evento.actividad_id = None  # el evento sigue en el calendario, sin vínculo
    db.session.delete(actividad)  # borra también sus inscripciones
    db.session.commit()
    flash(f"Actividad «{actividad.nombre}» eliminada junto con sus inscripciones.", "info")
    return redirect(url_for("admin.actividades"))


# --- inscritos de una actividad ----------------------------------------------------------

@bp.route("/actividades/<int:actividad_id>/inscritos", methods=["GET", "POST"])
def inscritos(actividad_id):
    actividad = db.get_or_404(Actividad, actividad_id)
    if request.method == "POST":
        usuario = db.session.get(Usuario, request.form.get("usuario_id", type=int) or 0)
        info = catalogo.get_actividad_por_id(actividad_id)
        if not usuario:
            flash("Elige un estudiante.", "danger")
        elif any(i.usuario_id == usuario.id for i in actividad.inscripciones):
            flash(f"{usuario.nombre} ya está en esta actividad.", "info")
        elif info["cupos_disponibles"] == 0:
            flash("No quedan cupos. Aumenta los cupos o retira a alguien primero.", "warning")
        else:
            db.session.add(Inscripcion(usuario_id=usuario.id, actividad_id=actividad_id,
                                       estado=ESTADO_APROBADA))
            db.session.commit()
            flash(f"{usuario.nombre} agregado a {actividad.nombre}.", "success")
        return redirect(url_for("admin.inscritos", actividad_id=actividad_id))

    inscritos_ids = {i.usuario_id for i in actividad.inscripciones}
    disponibles = [u for u in Usuario.query.filter_by(rol=ROL_ESTUDIANTE).order_by(Usuario.nombre)
                   if u.id not in inscritos_ids]
    return render_template(
        "admin/inscritos.html", actividad=actividad, info=catalogo.get_actividad_por_id(actividad_id),
        inscripciones=sorted(actividad.inscripciones, key=lambda i: i.usuario.nombre),
        disponibles=disponibles,
    )


@bp.route("/inscripciones/<int:inscripcion_id>/<accion>", methods=["POST"])
def cambiar_estado(inscripcion_id, accion):
    inscripcion = db.get_or_404(Inscripcion, inscripcion_id)
    nombre = inscripcion.usuario.nombre
    if accion == "quitar":
        db.session.delete(inscripcion)
        mensaje = f"{nombre} fue retirado de {inscripcion.actividad.nombre}."
    elif accion in ACCIONES:
        inscripcion.estado = ACCIONES[accion]
        mensaje = f"Solicitud de {nombre} marcada como {inscripcion.estado.lower()}."
    else:
        abort(404)
    db.session.commit()
    flash(mensaje, "success")
    return _volver(url_for("admin.panel"))


# --- calendario (eventos) ----------------------------------------------------------------

@bp.route("/eventos")
def eventos():
    return render_template("admin/eventos.html", eventos=catalogo.get_eventos())


@bp.route("/eventos/nuevo", methods=["GET", "POST"])
@bp.route("/eventos/<int:evento_id>/editar", methods=["GET", "POST"])
def evento_form(evento_id=None):
    evento = db.get_or_404(Evento, evento_id) if evento_id else Evento()
    if request.method == "POST":
        f = request.form
        errores = []
        try:
            fecha = date.fromisoformat(f.get("fecha", ""))
            hora = time.fromisoformat(f.get("hora", ""))
        except ValueError:
            errores.append("Fecha u hora inválida.")
        if not f.get("nombre", "").strip() or not f.get("lugar", "").strip():
            errores.append("El nombre y el lugar son obligatorios.")
        actividad = db.session.get(Actividad, f.get("actividad_id", type=int) or 0)
        categoria = actividad.categoria if actividad else f.get("categoria")
        if not catalogo.get_categoria(categoria):
            errores.append("Elige una categoría o una actividad.")
        if not errores:
            evento.nombre, evento.lugar = f["nombre"].strip(), f["lugar"].strip()
            evento.fecha, evento.hora, evento.categoria = fecha, hora, categoria
            evento.actividad_id = actividad.id if actividad else None
            if evento_id is None:
                db.session.add(evento)
            db.session.commit()
            flash(f"Evento «{evento.nombre}» guardado en el calendario.", "success")
            return redirect(url_for("admin.eventos"))
        for e in errores:
            flash(e, "danger")
    return render_template("admin/evento_form.html", evento=evento, form=request.form,
                           actividades=Actividad.query.order_by(Actividad.nombre).all())


@bp.route("/eventos/<int:evento_id>/eliminar", methods=["POST"])
def evento_eliminar(evento_id):
    evento = db.get_or_404(Evento, evento_id)
    db.session.delete(evento)
    db.session.commit()
    flash(f"Evento «{evento.nombre}» eliminado del calendario.", "info")
    return redirect(url_for("admin.eventos"))


# --- registro de usuarios ------------------------------------------------------------------

@bp.route("/usuarios")
def usuarios():
    return render_template("admin/usuarios.html",
                           usuarios=Usuario.query.order_by(Usuario.creado_en.desc()).all())
