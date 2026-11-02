import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-campus-vive")
    # Desarrollo: SQLite en instance/campus_vive.db.
    # MySQL: DATABASE_URL=mysql+pymysql://usuario:clave@localhost/campus_vive
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///campus_vive.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
