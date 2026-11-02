from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.routes.auth import _destino_seguro
from app.services import catalogo, sesion

bp = Blueprint("onboarding", __name__)


@bp.route("/bienvenida", methods=["GET", "POST"])
@sesion.login_requerido
def bienvenida():
    usuario = sesion.get_usuario()
    # Solo se muestra en el primer ingreso; después los intereses se cambian en /personaliza.
    if usuario.onboarding_completo or usuario.es_admin:
        return redirect(url_for("main.inicio"))

    if request.method == "POST":
        sesion.set_intereses(request.form.getlist("intereses"))
        flash(f"¡Todo listo, {usuario.nombre.split()[0]}! Estas son tus recomendaciones.", "success")
        return redirect(_destino_seguro(request.form.get("next")) or url_for("main.inicio"))

    # El paso "Descubre grupos" filtra en el cliente según los intereses marcados.
    return render_template(
        "onboarding/bienvenida.html",
        actividades=catalogo.get_recomendadas(None, limite=len(catalogo.get_actividades())),
    )
