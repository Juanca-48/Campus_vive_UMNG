"""Comandos de consola:  flask --app run <comando>"""
import click

from app.extensions import db
from app.models import ROL_ADMIN, Usuario


def registrar_comandos(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea las tablas que falten."""
        db.create_all()
        click.echo("Tablas creadas.")

    @app.cli.command("crear-admin")
    @click.option("--correo", default="bienestar@unimilitar.edu.co", show_default=True)
    @click.option("--nombre", default="Bienestar Universitario", show_default=True)
    @click.password_option("--clave", help="Contraseña (si no se indica, se pide por consola).")
    def crear_admin(correo, nombre, clave):
        """Crea o actualiza una cuenta de administrador (Bienestar)."""
        correo = correo.strip().lower()
        usuario = Usuario.query.filter_by(correo=correo).first()
        if usuario is None:
            usuario = Usuario(correo=correo, nombre=nombre)
            db.session.add(usuario)
        usuario.rol = ROL_ADMIN
        usuario.set_clave(clave)
        db.session.commit()
        click.echo(f"Administrador listo: {correo}")
