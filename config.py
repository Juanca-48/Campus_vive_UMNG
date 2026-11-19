import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-campus-vive")
    # Desarrollo: SQLite en instance/campus_vive.db.
    # MySQL: DATABASE_URL=mysql+pymysql://usuario:clave@localhost/campus_vive
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///campus_vive.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Fotos de actividades; las que sube el admin van en la subcarpeta subidas/ (fuera de git).
    CARPETA_FOTOS = Path(__file__).parent / "app" / "static" / "img" / "actividades"
