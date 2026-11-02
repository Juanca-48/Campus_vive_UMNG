from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.extensions import db
from app.models import Usuario
from app.services import sesion

bp = Blueprint("auth", __name__)

CLAVE_MIN = 8


def _destino_seguro(destino):
    return destino if destino and destino.startswith("/") and not destino.startswith("//") else None


@bp.route("/login", methods=["GET", "POST"])
def login():
    siguiente = _destino_seguro(request.values.get("next"))
    if sesion.get_usuario():
        return redirect(sesion.destino_tras_ingreso(siguiente))

    correo = ""
    if request.method == "POST":
        correo = request.form.get("correo", "").strip().lower()
        usuario = sesion.autenticar(correo, request.form.get("clave", ""))
        if usuario:
            primer_ingreso = usuario.ultimo_ingreso is None
            sesion.iniciar_sesion(usuario)
            nombre = usuario.nombre.split()[0]
            flash(f"¡Bienvenido, {nombre}!" if primer_ingreso else f"¡Hola de nuevo, {nombre}!", "success")
            return redirect(sesion.destino_tras_ingreso(siguiente))
        flash("Correo o contraseña incorrectos.", "danger")
    return render_template("auth/login.html", next=siguiente or "", correo=correo)


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    if sesion.get_usuario():
        return redirect(sesion.destino_tras_ingreso())

    datos = {"nombre": "", "correo": ""}
    if request.method == "POST":
        datos = {
            "nombre": request.form.get("nombre", "").strip(),
            "correo": request.form.get("correo", "").strip().lower(),
        }
        clave = request.form.get("clave", "")
        errores = []
        if not datos["nombre"]:
            errores.append("Escribe tu nombre.")
        if not datos["correo"].endswith(sesion.DOMINIO_INSTITUCIONAL):
            errores.append(f"Usa tu correo institucional ({sesion.DOMINIO_INSTITUCIONAL}).")
        elif Usuario.query.filter_by(correo=datos["correo"]).first():
            errores.append("Ya existe una cuenta con ese correo. Inicia sesión.")
        if len(clave) < CLAVE_MIN:
            errores.append(f"La contraseña debe tener al menos {CLAVE_MIN} caracteres.")
        elif clave != request.form.get("clave2", ""):
            errores.append("Las contraseñas no coinciden.")

        if not errores:
            usuario = Usuario(nombre=datos["nombre"], correo=datos["correo"])
            usuario.set_clave(clave)
            db.session.add(usuario)
            db.session.commit()
            sesion.iniciar_sesion(usuario)
            flash("Cuenta creada. Cuéntanos tus intereses para recomendarte actividades.", "success")
            return redirect(url_for("onboarding.bienvenida"))
        for e in errores:
            flash(e, "danger")
    return render_template("auth/registro.html", datos=datos, clave_min=CLAVE_MIN)


@bp.route("/logout")
def logout():
    sesion.cerrar_sesion()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("auth.login"))
