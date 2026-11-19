from datetime import timedelta, timezone

from flask import Flask, render_template
from sqlalchemy import inspect, text

from config import Config
from app import models  # noqa: F401  (registra los modelos antes de create_all)
from app.cli import registrar_comandos
from app.extensions import db
from app.services import catalogo, sesion


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    with app.app_context():
        db.create_all()  # solo crea las tablas que falten
        _agregar_columnas_faltantes()
        catalogo.sembrar_si_vacio()
    registrar_comandos(app)
    app.before_request(sesion.cargar_usuario)

    from app.routes.main import bp as main_bp
    from app.routes.onboarding import bp as onboarding_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.admin import bp as admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_globals():
        return {"categorias": catalogo.get_categorias(), "usuario": sesion.get_usuario()}

    @app.template_filter("mes")
    def mes(fecha):
        return MESES[fecha.month - 1]

    @app.template_filter("fecha_larga")
    def fecha_larga(fecha):
        return f"{fecha.day} de {MESES_LARGOS[fecha.month - 1]} de {fecha.year}"

    @app.template_filter("local")
    def local(momento, formato):
        # SQLite devuelve las fechas sin zona; se guardan en UTC. Colombia no tiene horario de verano.
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)
        return momento.astimezone(BOGOTA).strftime(formato)

    @app.template_filter("hora")
    def hora(t):
        sufijo = "a.m." if t.hour < 12 else "p.m."
        return f"{(t.hour % 12) or 12}:{t.minute:02d} {sufijo}"

    @app.errorhandler(404)
    def no_encontrado(_):
        return render_template("404.html"), 404

    return app


def _agregar_columnas_faltantes():
    """create_all no modifica tablas existentes: agrega las columnas nuevas (que admiten nulo)
    para no tener que borrar la base de datos local cada vez que el modelo crece."""
    inspector = inspect(db.engine)
    for tabla in db.metadata.sorted_tables:
        existentes = {c["name"] for c in inspector.get_columns(tabla.name)}
        for col in tabla.columns:
            if col.name not in existentes and col.nullable:
                tipo = col.type.compile(db.engine.dialect)
                db.session.execute(text(f"ALTER TABLE {tabla.name} ADD COLUMN {col.name} {tipo}"))
    db.session.commit()


BOGOTA = timezone(timedelta(hours=-5))
MESES = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
                "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
