# Campus Vive · UMNG

Plataforma web para que los estudiantes de la UMNG descubran, ubiquen y se inscriban en actividades
extracurriculares (cultura, deporte, artes y recreación).

Stack: HTML/CSS/JS + Bootstrap 5 · Flask · Flask-SQLAlchemy (SQLite en desarrollo, MySQL en producción).

## Ejecutar en local

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
flask --app run crear-admin      # cuenta de Bienestar (pide la contraseña)
python run.py                    # http://127.0.0.1:5000
```

Las tablas se crean solas al arrancar. Por defecto se usa SQLite en `instance/campus_vive.db`.

### Usar MySQL

```sql
CREATE DATABASE campus_vive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```bash
set DATABASE_URL=mysql+pymysql://usuario:clave@localhost/campus_vive    # PowerShell: $env:DATABASE_URL="..."
flask --app run init-db
flask --app run crear-admin
```

## Flujo de acceso

1. La primera pantalla es **/login**; todas las vistas del estudiante exigen sesión.
2. **Registro** solo con correo `@unimilitar.edu.co` y contraseña de 8+ caracteres (se guarda con hash).
3. Primer ingreso → recorrido **/bienvenida** (intereses). Al terminarlo se marca
   `usuario.onboarding_completo` y no se vuelve a mostrar; los intereses se cambian luego en **/personaliza**.
4. El administrador (rol `admin`) entra directo a **/admin**.

## Panel de administración (`/admin`)

| Pestaña | Qué permite |
|---|---|
| Resumen | Indicadores y solicitudes pendientes (aprobar / rechazar / retirar) |
| Actividades | Crear, editar y eliminar actividades; ver y gestionar sus **inscritos** (agregar estudiantes, aprobar, rechazar, retirar) |
| Calendario | Crear, editar y eliminar eventos; opcionalmente ligados a una actividad |
| Usuarios | Registro de todos los perfiles: rol, intereses, actividades, fecha de registro y último ingreso |

Las solicitudes pendientes y aprobadas ocupan cupo; los miembros son las aprobadas.

## Modelo de datos

| Tabla | Campos principales |
|---|---|
| `usuario` | nombre, correo (único), clave_hash, rol (`estudiante`/`admin`), onboarding_completo, creado_en, ultimo_ingreso |
| `interes` | usuario_id → usuario, categoria (slug) |
| `actividad` | slug, nombre, categoria, descripcion, detalle, nivel, cupos_total, horario (una franja por línea), responsable, lugar, sede, etiqueta, destacada |
| `inscripcion` | usuario_id → usuario, actividad_id → actividad, estado (Pendiente/Aprobada/Rechazada), creada_en |
| `evento` | nombre, fecha, hora, lugar, categoria, actividad_id → actividad (opcional) |

En el primer arranque se cargan las actividades y eventos de ejemplo de `app/data/mock.py`.
Las categorías y las novedades siguen fijas en ese archivo.

## Pruebas

```bash
python -m unittest discover tests
```

## Estructura

```
app/
  __init__.py        fábrica de la app, filtros de fecha y registro de blueprints
  models.py          modelos SQLAlchemy
  cli.py             comandos init-db y crear-admin
  data/mock.py       categorías, novedades y datos semilla
  services/
    catalogo.py      acceso a actividades, eventos y novedades
    sesion.py        autenticación, intereses, inscripciones y guardas de acceso
  routes/            main · onboarding · auth · admin
  templates/         Jinja2 (base, parciales y una carpeta por blueprint)
  static/            css/campus.css (identidad visual) y js/
docs/                presentación y documento del proyecto
```

## Pendiente

- Mapa del campus (`/mapa`) a la espera del plano.
- Protección CSRF en formularios (Flask-WTF) antes de publicar.
- Fotos de actividades: falta un campo `imagen` en `actividad` y subirla desde el panel
  (la plantilla ya la muestra si existe). La portada usa `app/static/img/hero-campus.jpg` si existe.
