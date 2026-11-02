"""Usuario autenticado, sus intereses e inscripciones.

La cookie de sesión solo guarda el id del usuario; todo lo demás se lee de la
base de datos en cada petición (g.usuario).
"""
from datetime import datetime, timezone
from functools import wraps

from flask import flash, g, redirect, request, session, url_for

from app.extensions import db
from app.models import Inscripcion, Interes, Usuario
from app.services import catalogo

DOMINIO_INSTITUCIONAL = "@unimilitar.edu.co"


def cargar_usuario():
    """Se ejecuta antes de cada petición (registrado en create_app)."""
    usuario_id = session.get("usuario_id")
    g.usuario = db.session.get(Usuario, usuario_id) if usuario_id else None


def get_usuario():
    return g.get("usuario")


def autenticar(correo, clave):
    usuario = Usuario.query.filter_by(correo=correo).first()
    if usuario and usuario.verificar_clave(clave):
        return usuario
    return None


def iniciar_sesion(usuario):
    session.clear()  # evita reutilizar una sesión previa (fijación de sesión)
    session["usuario_id"] = usuario.id
    usuario.ultimo_ingreso = datetime.now(timezone.utc)
    db.session.commit()
    g.usuario = usuario


def cerrar_sesion():
    session.clear()


def destino_tras_ingreso(siguiente=None):
    """Admin → panel; estudiante nuevo → recorrido inicial; el resto → donde iba o Inicio."""
    usuario = get_usuario()
    if not usuario.es_admin and not usuario.onboarding_completo:
        return url_for("onboarding.bienvenida")
    if siguiente:
        return siguiente
    return url_for("admin.panel") if usuario.es_admin else url_for("main.inicio")


# --- intereses ---------------------------------------------------------------

def get_intereses():
    usuario = get_usuario()
    return usuario.categorias_interes if usuario else []


def set_intereses(slugs):
    usuario = get_usuario()
    validos = {c["slug"] for c in catalogo.get_categorias()}
    usuario.intereses = [Interes(categoria=s) for s in dict.fromkeys(slugs) if s in validos]
    usuario.onboarding_completo = True
    db.session.commit()


# --- inscripciones -------------------------------------------------------------

def get_inscripciones():
    usuario = get_usuario()
    return usuario.inscripciones if usuario else []


def esta_inscrito(actividad_id):
    return any(i.actividad_id == actividad_id for i in get_inscripciones())


def inscribir(actividad_id):
    if esta_inscrito(actividad_id):
        return False
    db.session.add(Inscripcion(usuario_id=get_usuario().id, actividad_id=actividad_id))
    db.session.commit()
    return True


def cancelar_inscripcion(actividad_id):
    Inscripcion.query.filter_by(usuario_id=get_usuario().id, actividad_id=actividad_id).delete()
    db.session.commit()


# --- protección de vistas -------------------------------------------------------

def exigir_estudiante_listo():
    """Guarda para las vistas del estudiante: sesión iniciada y recorrido inicial hecho.

    Devuelve una redirección o None si puede continuar.
    """
    usuario = get_usuario()
    if not usuario:
        flash("Inicia sesión con tu correo institucional para continuar.", "info")
        return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
    if not usuario.es_admin and not usuario.onboarding_completo:
        return redirect(url_for("onboarding.bienvenida"))
    return None


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not get_usuario():
            flash("Inicia sesión con tu correo institucional para continuar.", "info")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return vista(*args, **kwargs)
    return envoltura


def admin_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = get_usuario()
        if not usuario:
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        if not usuario.es_admin:
            flash("Esta sección es solo para Bienestar Universitario.", "warning")
            return redirect(url_for("main.inicio"))
        return vista(*args, **kwargs)
    return envoltura
