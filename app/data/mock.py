"""Categorías fijas y datos semilla.

ACTIVIDADES y EVENTOS solo se cargan en la base de datos la primera vez
(catalogo.sembrar_si_vacio); después se gestionan desde el panel de admin.
Sus campos cupos_disponibles y miembros ya no se usan: se calculan de las inscripciones.
"""
from datetime import date, time

CATEGORIAS = [
    {"slug": "cultura", "nombre": "Cultura", "color": "pink", "icono": "bi-emoji-laughing"},
    {"slug": "deporte", "nombre": "Deporte", "color": "yellow", "icono": "bi-dribbble"},
    {"slug": "artes", "nombre": "Artes", "color": "blue", "icono": "bi-palette"},
    {"slug": "recreacion", "nombre": "Recreación", "color": "green", "icono": "bi-tree"},
]

UBICACIONES = [
    {"id": 1, "nombre": "Bloque A - Auditorio", "sede": "Calle 100"},
    {"id": 2, "nombre": "Canchas deportivas", "sede": "Calle 100"},
    {"id": 3, "nombre": "Edificio de Cultura, 2.º piso", "sede": "Calle 100"},
    {"id": 4, "nombre": "Lab. de Medios Audiovisuales", "sede": "Calle 100"},
    {"id": 5, "nombre": "Sala de Yoga", "sede": "Calle 100"},
    {"id": 6, "nombre": "Aula de Música", "sede": "Calle 100"},
    {"id": 7, "nombre": "Coliseo", "sede": "Calle 100"},
    {"id": 8, "nombre": "Punto de encuentro: Plazoleta Central", "sede": "Varias sedes"},
]

ACTIVIDADES = [
    {
        "id": 1, "slug": "futbol-umng", "nombre": "Fútbol UMNG", "categoria": "deporte",
        "icono": "bi-dribbble",
        "descripcion": "Entrena, compite y vive la pasión por el fútbol junto a otros estudiantes.",
        "detalle": "Entrenamientos técnicos y tácticos con miras a los torneos interfacultades "
                   "y universitarios. Se requiere certificado médico vigente.",
        "nivel": "Avanzado", "cupos_total": 30, "cupos_disponibles": 12, "miembros": 45,
        "horario": ["Lunes 4:00 p.m. – 6:00 p.m.", "Miércoles 4:00 p.m. – 6:00 p.m."],
        "responsable": "Prof. Andrés Gómez", "ubicacion_id": 2,
        "etiqueta": "Popular", "destacada": True,
    },
    {
        "id": 2, "slug": "teatro-en-escena", "nombre": "Teatro en Escena", "categoria": "cultura",
        "icono": "bi-emoji-laughing",
        "descripcion": "Explora tu creatividad y forma parte de nuestras puestas en escena.",
        "detalle": "Taller de actuación, expresión corporal y montaje de obras que se presentan "
                   "cada semestre en el auditorio.",
        "nivel": "Todos los niveles", "cupos_total": 25, "cupos_disponibles": 8, "miembros": 28,
        "horario": ["Martes 2:00 p.m. – 4:00 p.m.", "Jueves 2:00 p.m. – 4:00 p.m."],
        "responsable": "Mtra. Laura Restrepo", "ubicacion_id": 1,
        "etiqueta": "Popular", "destacada": False,
    },
    {
        "id": 3, "slug": "arte-y-color", "nombre": "Arte & Color", "categoria": "artes",
        "icono": "bi-palette",
        "descripcion": "Comparte tu talento y aprende nuevas técnicas en un ambiente creativo.",
        "detalle": "Pintura, acuarela e ilustración. Los materiales básicos los aporta Bienestar.",
        "nivel": "Principiante", "cupos_total": 20, "cupos_disponibles": 6, "miembros": 22,
        "horario": ["Viernes 10:00 a.m. – 12:00 m."],
        "responsable": "Prof. Camila Ortiz", "ubicacion_id": 3,
        "etiqueta": "Nuevo", "destacada": False,
    },
    {
        "id": 4, "slug": "explora-naturaleza", "nombre": "Explora Naturaleza", "categoria": "recreacion",
        "icono": "bi-tree",
        "descripcion": "Salidas, caminatas y actividades al aire libre para conectar con la naturaleza.",
        "detalle": "Caminatas ecológicas mensuales y actividades de integración al aire libre.",
        "nivel": "Todos los niveles", "cupos_total": 40, "cupos_disponibles": 15, "miembros": 31,
        "horario": ["Sábados (salida mensual) 7:00 a.m."],
        "responsable": "Coord. Felipe Rojas", "ubicacion_id": 8,
        "etiqueta": "Popular", "destacada": False,
    },
    {
        "id": 5, "slug": "danza-contemporanea", "nombre": "Danza Contemporánea", "categoria": "cultura",
        "icono": "bi-people",
        "descripcion": "Movimiento, expresión y técnica para quienes aman bailar.",
        "detalle": "Técnica contemporánea, improvisación y creación coreográfica.",
        "nivel": "Intermedio", "cupos_total": 24, "cupos_disponibles": 18, "miembros": 20,
        "horario": ["Lunes 6:00 p.m. – 8:00 p.m.", "Jueves 6:00 p.m. – 8:00 p.m."],
        "responsable": "Mtra. Daniela Suárez", "ubicacion_id": 3,
        "etiqueta": None, "destacada": True,
    },
    {
        "id": 6, "slug": "fotografia", "nombre": "Fotografía", "categoria": "artes",
        "icono": "bi-camera",
        "descripcion": "Aprende composición, luz y edición para contar historias con imágenes.",
        "detalle": "Fundamentos de fotografía digital y salidas fotográficas por el campus.",
        "nivel": "Principiante", "cupos_total": 15, "cupos_disponibles": 15, "miembros": 12,
        "horario": ["Miércoles 10:00 a.m. – 12:00 m."],
        "responsable": "Prof. Sergio Méndez", "ubicacion_id": 4,
        "etiqueta": "Nuevo", "destacada": True,
    },
    {
        "id": 7, "slug": "yoga-y-bienestar", "nombre": "Yoga y Bienestar", "categoria": "recreacion",
        "icono": "bi-flower1",
        "descripcion": "Respira, estírate y desconéctate del estrés académico.",
        "detalle": "Sesiones de yoga, respiración y meditación guiada.",
        "nivel": "Todos los niveles", "cupos_total": 20, "cupos_disponibles": 20, "miembros": 35,
        "horario": ["Martes 7:00 a.m. – 8:00 a.m.", "Viernes 12:00 m. – 1:00 p.m."],
        "responsable": "Inst. Mariana León", "ubicacion_id": 5,
        "etiqueta": None, "destacada": True,
    },
    {
        "id": 8, "slug": "guitarra-acustica", "nombre": "Guitarra Acústica", "categoria": "artes",
        "icono": "bi-music-note-beamed",
        "descripcion": "Desde tus primeros acordes hasta tocar en los eventos del campus.",
        "detalle": "Clases grupales por niveles. Se recomienda traer instrumento propio.",
        "nivel": "Principiante", "cupos_total": 12, "cupos_disponibles": 10, "miembros": 16,
        "horario": ["Jueves 4:00 p.m. – 6:00 p.m."],
        "responsable": "Prof. Julián Cárdenas", "ubicacion_id": 6,
        "etiqueta": None, "destacada": True,
    },
    {
        "id": 9, "slug": "baloncesto", "nombre": "Baloncesto", "categoria": "deporte",
        "icono": "bi-trophy",
        "descripcion": "Equipo mixto de baloncesto: entrenamientos y torneos internos.",
        "detalle": "Fundamentos, juego en equipo y preparación física.",
        "nivel": "Intermedio", "cupos_total": 20, "cupos_disponibles": 0, "miembros": 20,
        "horario": ["Martes 4:00 p.m. – 6:00 p.m.", "Viernes 4:00 p.m. – 6:00 p.m."],
        "responsable": "Prof. Ricardo Peña", "ubicacion_id": 7,
        "etiqueta": None, "destacada": False,
    },
    {
        "id": 10, "slug": "coro-umng", "nombre": "Coro UMNG", "categoria": "cultura",
        "icono": "bi-music-note-list",
        "descripcion": "Canta en el coro institucional y participa en los conciertos del año.",
        "detalle": "Técnica vocal, ensamble y repertorio coral. Audición inicial sencilla.",
        "nivel": "Todos los niveles", "cupos_total": 30, "cupos_disponibles": 9, "miembros": 21,
        "horario": ["Miércoles 2:00 p.m. – 4:00 p.m."],
        "responsable": "Mtro. Esteban Vargas", "ubicacion_id": 1,
        "etiqueta": None, "destacada": False,
    },
]

EVENTOS = [
    {"id": 1, "nombre": "Festival Cultural UMNG", "fecha": date(2026, 11, 20), "hora": time(17, 0),
     "lugar": "Plazoleta Central", "categoria": "cultura"},
    {"id": 2, "nombre": "Torneo Interfacultades", "fecha": date(2026, 11, 23), "hora": time(8, 0),
     "lugar": "Complejo Deportivo", "categoria": "deporte"},
    {"id": 3, "nombre": "Muestra de Arte & Color", "fecha": date(2026, 11, 27), "hora": time(15, 0),
     "lugar": "Edificio de Cultura", "categoria": "artes"},
    {"id": 4, "nombre": "Caminata ecológica", "fecha": date(2026, 12, 5), "hora": time(7, 0),
     "lugar": "Plazoleta Central (salida)", "categoria": "recreacion"},
]

NOVEDADES = [
    {"id": 1, "titulo": "Abiertas las inscripciones del segundo semestre",
     "resumen": "Ya puedes solicitar tu cupo en todos los grupos de cultura y deporte.",
     "fecha": date(2026, 11, 2)},
    {"id": 2, "titulo": "Nuevo grupo de Fotografía",
     "resumen": "Bienestar abre un grupo de fotografía para principiantes con 15 cupos.",
     "fecha": date(2026, 10, 28)},
    {"id": 3, "titulo": "Convocatoria Festival Cultural",
     "resumen": "¿Cantas, bailas o actúas? Inscribe tu número para el Festival Cultural UMNG.",
     "fecha": date(2026, 10, 20)},
]
