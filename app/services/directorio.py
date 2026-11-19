"""Directorio institucional: datos académicos del estudiante (código, carrera, semestre).

Se consulta en cada ingreso y se copian al usuario, así se mantienen sincronizados.
shortcut: los datos son inventados a partir del correo (siempre los mismos para el mismo
correo). Cuando haya acceso a la base de datos o API de la UMNG, reemplazar `consultar`.
"""
import hashlib

CARRERAS = [
    "Derecho", "Ingeniería en Multimedia", "Ingeniería Civil", "Ingeniería Industrial",
    "Ingeniería Mecatrónica", "Ingeniería en Telecomunicaciones", "Administración de Empresas",
    "Contaduría Pública", "Economía", "Relaciones Internacionales y Estudios Políticos",
]


def consultar(correo):
    """Devuelve {"codigo", "carrera", "semestre", "foto"} del estudiante, o None si no existe.

    "foto" es la URL de la foto del carné; en los datos de prueba no hay (se muestran iniciales).
    """
    n = int(hashlib.sha256(correo.lower().encode()).hexdigest(), 16)
    return {
        "codigo": str(1800000 + n % 200000),
        "carrera": CARRERAS[n // 7 % len(CARRERAS)],
        "semestre": n // 11 % 10 + 1,
        "foto": None,
    }
