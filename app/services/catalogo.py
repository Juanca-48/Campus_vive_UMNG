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

# Puntos iniciales de las actividades de ejemplo, en % sobre img/mapas/campus_general.jpg.
# Se usan mientras el admin no ubique la actividad en el mapa (Actividad.mapa_x / mapa_y).
_CANCHA_1, _CANCHA_2, _GIMNASIO = (25.2, 60.0), (33.2, 59.0), (28.5, 16.4)
_ARTES, _FOTO = (65.3, 52.6), (54.8, 31.4)
PUNTOS_MAPA = {
    1: _CANCHA_1,   # Fútbol UMNG
    2: _CANCHA_2,   # Teatro en Escena
    3: _ARTES,      # Arte & Color
    4: _ARTES,      # Explora Naturaleza
    5: _GIMNASIO,   # Danza Contemporánea
    6: _FOTO,       # Fotografía
    7: _GIMNASIO,   # Yoga y Bienestar
    8: _FOTO,       # Guitarra Acústica
    9: _CANCHA_2,   # Baloncesto
    10: _FOTO,      # Coro UMNG
}

# Fotos de ejemplo en static/img/actividades/ (créditos en CREDITOS.md), por id de actividad.
# La que suba el admin (Actividad.imagen) tiene prioridad; sin ninguna se ve el degradado.
FOTOS = {
    1: "futbol-umng.jpg", 2: "teatro-en-escena.jpg", 3: "arte-y-color.jpg", 4: "explora-naturaleza.jpg",
    5: "danza-contemporanea.jpg", 6: "fotografia.jpg", 7: "yoga-y-bienestar.jpg", 8: "guitarra-acustica.jpg",
    9: "baloncesto.jpg", 10: "coro-umng.jpg",
}


def _conteos():
    """{actividad_id: {estado: n}} en una sola consulta."""
    filas = (db.session.query(Inscripcion.actividad_id, Inscripcion.estado, func.count())
             .group_by(Inscripcion.actividad_id, Inscripcion.estado).all())
    conteos = {}
    for actividad_id, estado, n in filas:
        conteos.setdefault(actividad_id, {})[estado] = n
    return conteos


def punto_mapa(a):
    """(x, y) en % del lugar de la actividad: el que eligió el admin o el de ejemplo; None si no hay."""
    if a.mapa_x is not None and a.mapa_y is not None:
        return (a.mapa_x, a.mapa_y)
    return PUNTOS_MAPA.get(a.id)


def _a_dict(a, conteos):
    c = conteos.get(a.id, {})
    ocupados = c.get(ESTADO_APROBADA, 0) + c.get(ESTADO_PENDIENTE, 0)  # las pendientes reservan cupo
    cat = _CATEGORIAS[a.categoria]
    return {
        "id": a.id, "slug": a.slug, "nombre": a.nombre, "categoria": a.categoria, "cat": cat,
        "icono": cat["icono"], "descripcion": a.descripcion, "detalle": a.detalle,
        "cupos_total": a.cupos_total, "cupos_disponibles": max(a.cupos_total - ocupados, 0),
        "miembros": c.get(ESTADO_APROBADA, 0), "pendientes": c.get(ESTADO_PENDIENTE, 0),
        "horario": [h for h in a.horario.splitlines() if h.strip()],
        "responsable": a.responsable, "ubicacion": {"nombre": a.lugar, "sede": a.sede},
        "punto_mapa": punto_mapa(a), "imagen": a.imagen or FOTOS.get(a.id),
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
            descripcion=a["descripcion"], detalle=a["detalle"],
            cupos_total=a["cupos_total"], horario="\n".join(a["horario"]),
            responsable=a["responsable"], lugar=u["nombre"], sede=u["sede"],
            etiqueta=a["etiqueta"], destacada=a["destacada"],
        ))
    for e in mock.EVENTOS:
        db.session.add(Evento(nombre=e["nombre"], fecha=e["fecha"], hora=e["hora"],
                              lugar=e["lugar"], categoria=e["categoria"]))
    db.session.commit()
