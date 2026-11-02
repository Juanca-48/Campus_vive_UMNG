"""Acceso al catálogo de actividades y eventos.

Devuelve diccionarios con la forma que usan las plantillas (act.cat,
act.ubicacion.nombre, act.horario como lista...), así las vistas no dependen
de los modelos.
"""
from sqlalchemy import func

from app.data import mock
from app.extensions import db
from app.models import ESTADO_APROBADA, ESTADO_PENDIENTE, Actividad, Evento, Inscripcion

_CATEGORIAS = {c["slug"]: c for c in mock.CATEGORIAS}


def _conteos():
    """{actividad_id: {estado: n}} en una sola consulta."""
    filas = (db.session.query(Inscripcion.actividad_id, Inscripcion.estado, func.count())
             .group_by(Inscripcion.actividad_id, Inscripcion.estado).all())
    conteos = {}
    for actividad_id, estado, n in filas:
        conteos.setdefault(actividad_id, {})[estado] = n
    return conteos


def _a_dict(a, conteos):
    c = conteos.get(a.id, {})
    ocupados = c.get(ESTADO_APROBADA, 0) + c.get(ESTADO_PENDIENTE, 0)  # las pendientes reservan cupo
    cat = _CATEGORIAS[a.categoria]
    return {
        "id": a.id, "slug": a.slug, "nombre": a.nombre, "categoria": a.categoria, "cat": cat,
        "icono": cat["icono"], "descripcion": a.descripcion, "detalle": a.detalle, "nivel": a.nivel,
        "cupos_total": a.cupos_total, "cupos_disponibles": max(a.cupos_total - ocupados, 0),
        "miembros": c.get(ESTADO_APROBADA, 0), "pendientes": c.get(ESTADO_PENDIENTE, 0),
        "horario": [h for h in a.horario.splitlines() if h.strip()],
        "responsable": a.responsable, "ubicacion": {"nombre": a.lugar, "sede": a.sede},
        "etiqueta": a.etiqueta, "destacada": a.destacada,
    }


def get_categorias():
    return mock.CATEGORIAS


def get_categoria(slug):
    return _CATEGORIAS.get(slug)


def get_actividades(categoria=None):
    consulta = Actividad.query.order_by(Actividad.nombre)
    if categoria:
        consulta = consulta.filter_by(categoria=categoria)
    conteos = _conteos()
    return [_a_dict(a, conteos) for a in consulta]


def get_actividad(slug):
    a = Actividad.query.filter_by(slug=slug).first()
    return _a_dict(a, _conteos()) if a else None


def get_actividad_por_id(actividad_id):
    a = db.session.get(Actividad, actividad_id)
    return _a_dict(a, _conteos()) if a else None


def get_destacadas():
    return [a for a in get_actividades() if a["destacada"]]


def get_recomendadas(intereses, limite=4):
    """Recomendación inicial: coincidencia por categoría, ordenada por popularidad."""
    actividades = get_actividades()
    if intereses:
        actividades = [a for a in actividades if a["categoria"] in intereses] or actividades
    return sorted(actividades, key=lambda a: a["miembros"], reverse=True)[:limite]


def get_eventos():
    eventos = Evento.query.order_by(Evento.fecha, Evento.hora).all()
    return [{"id": e.id, "nombre": e.nombre, "fecha": e.fecha, "hora": e.hora, "lugar": e.lugar,
             "categoria": e.categoria, "cat": _CATEGORIAS[e.categoria], "actividad": e.actividad}
            for e in eventos]


def get_novedades():
    return sorted(mock.NOVEDADES, key=lambda n: n["fecha"], reverse=True)


def sembrar_si_vacio():
    """Carga las actividades y eventos de ejemplo la primera vez que arranca la app."""
    if Actividad.query.first():
        return
    ubicaciones = {u["id"]: u for u in mock.UBICACIONES}
    for a in mock.ACTIVIDADES:
        u = ubicaciones[a["ubicacion_id"]]
        # Se conserva el id del ejemplo para no romper inscripciones previas.
        db.session.add(Actividad(
            id=a["id"], slug=a["slug"], nombre=a["nombre"], categoria=a["categoria"],
            descripcion=a["descripcion"], detalle=a["detalle"], nivel=a["nivel"],
            cupos_total=a["cupos_total"], horario="\n".join(a["horario"]),
            responsable=a["responsable"], lugar=u["nombre"], sede=u["sede"],
            etiqueta=a["etiqueta"], destacada=a["destacada"],
        ))
    for e in mock.EVENTOS:
        db.session.add(Evento(nombre=e["nombre"], fecha=e["fecha"], hora=e["hora"],
                              lugar=e["lugar"], categoria=e["categoria"]))
    db.session.commit()
