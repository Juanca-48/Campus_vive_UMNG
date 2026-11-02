"""Panel de Bienestar Universitario: actividades, calendario, inscritos y usuarios."""
import re
import unicodedata
from datetime import date, time

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import (ESTADO_APROBADA, ESTADO_PENDIENTE, ESTADO_RECHAZADA, ROL_ESTUDIANTE,
                        Actividad, Evento, Inscripcion, Usuario)
from app.routes.auth import _destino_seguro
from app.services import catalogo, sesion

bp = Blueprint("admin", __name__)

ACCIONES = {"aprobar": ESTADO_APROBADA, "rechazar": ESTADO_RECHAZADA, "pendiente": ESTADO_PENDIENTE}
NIVELES = ["Todos los niveles", "Principiante", "Intermedio", "Avanzado"]
ETIQUETAS = ["", "Popular", "Nuevo"]


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


# --- resumen -----------------------------------------------------------------------

@bp.route("/")
def panel():
    actividades = catalogo.get_actividades()
    pendientes = (Inscripcion.query.filter_by(estado=ESTADO_PENDIENTE)
                  .order_by(Inscripcion.creada_en).all())
    resumen = {
        "estudiantes": Usuario.query.filter_by(rol=ROL_ESTUDIANTE).count(),
        "pendientes": len(pendientes),
        "actividades": len(actividades),
        "eventos": Evento.query.filter(Evento.fecha >= date.today()).count(),
    }
    return render_template("admin/panel.html", pendientes=pendientes, resumen=resumen)


# --- actividades -------------------------------------------------------------------

@bp.route("/actividades")
def actividades():
    return render_template("admin/actividades.html", actividades=catalogo.get_actividades())


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
    if errores:
        return errores

    actividad.nombre = nombre
    actividad.slug = _slug(nombre, excluir_id=actividad.id)
    actividad.categoria = f["categoria"]
    actividad.descripcion = f.get("descripcion", "").strip()[:255]
    actividad.detalle = f.get("detalle", "").strip()
    actividad.nivel = f.get("nivel") if f.get("nivel") in NIVELES else NIVELES[0]
    actividad.cupos_total = cupos
    actividad.horario = "\n".join(h.strip() for h in f.get("horario", "").splitlines() if h.strip())
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
    return render_template("admin/actividad_form.html", actividad=actividad, form=request.form,
                           niveles=NIVELES, etiquetas=ETIQUETAS)


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
