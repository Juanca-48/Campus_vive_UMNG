import os
from pathlib import Path

EN_VERCEL = bool(os.environ.get("VERCEL"))  # Vercel define esta variable en sus servidores
CLAVE_DESARROLLO = "dev-campus-vive"


class Config:
    # `or` y no un valor por defecto: una variable definida pero vacía cuenta como no definida.
    SECRET_KEY = os.environ.get("SECRET_KEY") or CLAVE_DESARROLLO
    # Desarrollo: SQLite en instance/campus_vive.db.
    # MySQL: DATABASE_URL=mysql+pymysql://usuario:clave@host:puerto/bd  (con TLS: ...?ssl_ca=certs/ca.pem)
    # ssl_ca=certs/... se vuelve ruta absoluta: no depende de la carpeta desde donde arranque Vercel.
    SQLALCHEMY_DATABASE_URI = (os.environ.get("DATABASE_URL") or "sqlite:///campus_vive.db").replace(
        "ssl_ca=certs/", f"ssl_ca={(Path(__file__).parent / 'certs').as_posix()}/")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # En Vercel cada servidor se congela entre peticiones: se revisa la conexión antes de usarla.
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 280}
    # La cookie de sesión no viaja en formularios enviados desde otros sitios (freno a CSRF).
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = EN_VERCEL  # solo por HTTPS en producción
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # Vercel no acepta cuerpos de más de 4,5 MB


def revisar_produccion(app):
    """En Vercel no se arranca con la clave de desarrollo ni con SQLite (el disco es de solo lectura)."""
    if not EN_VERCEL or app.testing:
        return
    faltan = [nombre for nombre, falta in [
        ("SECRET_KEY", app.config["SECRET_KEY"] == CLAVE_DESARROLLO),
        ("DATABASE_URL", app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite")),
    ] if falta]
    if faltan:
        raise RuntimeError("Configura en Vercel las variables de entorno: " + ", ".join(faltan))
