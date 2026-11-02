"""Modelo de datos: usuarios, intereses, actividades, inscripciones y eventos.

Las categorías son fijas (app/data/mock.py) y se guardan por su slug.
"""
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db

ROL_ESTUDIANTE = "estudiante"
ROL_ADMIN = "admin"

ESTADO_PENDIENTE = "Pendiente"
ESTADO_APROBADA = "Aprobada"
ESTADO_RECHAZADA = "Rechazada"


def _ahora():
    return datetime.now(timezone.utc)


class Usuario(db.Model):
    __tablename__ = "usuario"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(160), unique=True, nullable=False, index=True)
    clave_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=ROL_ESTUDIANTE)
    # False hasta que el estudiante elige sus intereses en el recorrido inicial.
    onboarding_completo = db.Column(db.Boolean, nullable=False, default=False)
    creado_en = db.Column(db.DateTime(timezone=True), nullable=False, default=_ahora)
    ultimo_ingreso = db.Column(db.DateTime(timezone=True))

    intereses = db.relationship("Interes", backref="usuario", cascade="all, delete-orphan")
    inscripciones = db.relationship(
        "Inscripcion", backref="usuario", cascade="all, delete-orphan",
        order_by="Inscripcion.creada_en.desc()",
    )

    def set_clave(self, clave):
        self.clave_hash = generate_password_hash(clave)

    def verificar_clave(self, clave):
        return check_password_hash(self.clave_hash, clave)

    @property
    def es_admin(self):
        return self.rol == ROL_ADMIN

    @property
    def categorias_interes(self):
        return [i.categoria for i in self.intereses]


class Interes(db.Model):
    __tablename__ = "interes"
    __table_args__ = (db.UniqueConstraint("usuario_id", "categoria"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    categoria = db.Column(db.String(30), nullable=False)


class Actividad(db.Model):
    __tablename__ = "actividad"

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(140), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(30), nullable=False)
    descripcion = db.Column(db.String(255), nullable=False, default="")
    detalle = db.Column(db.Text, nullable=False, default="")
    nivel = db.Column(db.String(40), nullable=False, default="Todos los niveles")
    cupos_total = db.Column(db.Integer, nullable=False, default=20)
    horario = db.Column(db.Text, nullable=False, default="")  # una franja por línea
    responsable = db.Column(db.String(120), nullable=False, default="")
    lugar = db.Column(db.String(120), nullable=False, default="")
    sede = db.Column(db.String(60), nullable=False, default="Calle 100")
    etiqueta = db.Column(db.String(20))  # "Popular", "Nuevo" o vacío
    destacada = db.Column(db.Boolean, nullable=False, default=False)
    creada_en = db.Column(db.DateTime(timezone=True), nullable=False, default=_ahora)

    inscripciones = db.relationship("Inscripcion", backref="actividad", cascade="all, delete-orphan")
    eventos = db.relationship("Evento", backref="actividad")


class Evento(db.Model):
    __tablename__ = "evento"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.Time, nullable=False)
    lugar = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(30), nullable=False)
    actividad_id = db.Column(db.Integer, db.ForeignKey("actividad.id", ondelete="SET NULL"))


class Inscripcion(db.Model):
    __tablename__ = "inscripcion"
    __table_args__ = (db.UniqueConstraint("usuario_id", "actividad_id"),)

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    actividad_id = db.Column(db.Integer, db.ForeignKey("actividad.id"), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default=ESTADO_PENDIENTE)
    creada_en = db.Column(db.DateTime(timezone=True), nullable=False, default=_ahora)
