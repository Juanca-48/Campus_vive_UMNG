from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.services import catalogo, sesion

bp = Blueprint("main", __name__)


@bp.before_request
def exigir_ingreso():
    # Todas las vistas del estudiante requieren sesión y el recorrido inicial completo.
    return sesion.exigir_estudiante_listo()


@bp.route("/")
def inicio():
    return render_template(
        "main/inicio.html",
        destacadas=catalogo.get_destacadas(),
        recomendadas=catalogo.get_recomendadas(sesion.get_intereses()),
        eventos=catalogo.get_eventos()[:2],
    )


@bp.route("/descubre")
def descubre():
    return render_template(
        "main/descubre.html",
        actividades=catalogo.get_actividades(),
        categoria_activa=request.args.get("categoria", "todos"),
    )


@bp.route("/actividad/<slug>")
def actividad(slug):
    act = catalogo.get_actividad(slug)
    if not act:
        abort(404)
    return render_template(
        "main/actividad.html",
        act=act,
        inscrito=sesion.esta_inscrito(act["id"]),
        relacionadas=[a for a in catalogo.get_actividades(act["categoria"]) if a["id"] != act["id"]][:3],
    )


@bp.route("/actividad/<slug>/inscribir", methods=["POST"])
def inscribir(slug):
    act = catalogo.get_actividad(slug)
    if not act:
        abort(404)
    if act["cupos_disponibles"] == 0:
        flash("Este grupo no tiene cupos disponibles por ahora.", "warning")
    elif sesion.inscribir(act["id"]):
        flash(f"¡Listo! Tu solicitud para {act['nombre']} fue enviada.", "success")
    else:
        flash(f"Ya tienes una solicitud para {act['nombre']}.", "info")
    return redirect(url_for("main.actividad", slug=slug))


@bp.route("/personaliza", methods=["GET", "POST"])
def personaliza():
    if request.method == "POST":
        sesion.set_intereses(request.form.getlist("intereses"))
        flash("Tus intereses fueron actualizados.", "success")
        return redirect(url_for("main.inicio"))
    return render_template("main/personaliza.html", intereses=sesion.get_intereses())


@bp.route("/mis-actividades")
def mis_actividades():
    inscripciones = [
        {"estado": i.estado, "actividad_id": i.actividad_id,
         "act": catalogo.get_actividad_por_id(i.actividad_id)}
        for i in sesion.get_inscripciones()
    ]
    return render_template(
        "main/mis_actividades.html",
        inscripciones=[i for i in inscripciones if i["act"]],
    )


@bp.route("/mis-actividades/<int:actividad_id>/cancelar", methods=["POST"])
def cancelar(actividad_id):
    sesion.cancelar_inscripcion(actividad_id)
    flash("Solicitud cancelada.", "info")
    return redirect(url_for("main.mis_actividades"))


@bp.route("/calendario")
def calendario():
    return render_template("main/calendario.html", eventos=catalogo.get_eventos())


@bp.route("/mapa")
def mapa():
    return render_template("main/mapa.html")


@bp.route("/novedades")
def novedades():
    return render_template("main/novedades.html", novedades=catalogo.get_novedades())
