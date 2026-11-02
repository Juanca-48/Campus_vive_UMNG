# Campus Vive · UMNG

> **Encuentra tu lugar en la universidad.**
> Plataforma web para que los estudiantes de la Universidad Militar Nueva Granada descubran,
> ubiquen y se inscriban en las actividades extracurriculares del campus.

Proyecto del curso **Gestión Integral de Proyectos** — equipo *4 Frames Startup*.

---

## El problema

La UMNG tiene una oferta amplia de grupos culturales, artísticos, deportivos y recreativos, pero la
información está dispersa entre carteleras, redes sociales de cada grupo y el voz a voz. En una
consulta a estudiantes de primeros semestres:

- **70 %** no sabe dónde consultar toda la oferta.
- **60 %** no conoce claramente cómo inscribirse.
- La mayoría termina preguntándole a otra persona.

El resultado es baja participación pese a la oferta, estudiantes desconectados de la vida
universitaria (un factor asociado a la deserción) y un equipo de Bienestar que difunde por muchos
canales sin saber qué funciona.

**Es un problema de descubrimiento, no de oferta:** no hace falta crear más actividades, sino hacer
visibles las que ya existen.

## La solución

Campus Vive es una **aplicación web responsive** (celular y computador) que funciona como un sistema
de recomendación, no como un simple directorio:

| | |
|---|---|
| **Descubre** | Catálogo de grupos de cultura, deporte, artes y recreación, con filtros y búsqueda. |
| **Personaliza** | El estudiante elige sus intereses y recibe actividades recomendadas. |
| **Conoce** | Horarios, responsable, lugar, nivel y cupos disponibles de cada grupo. |
| **Inscríbete** | Solicitud de inscripción en un paso y seguimiento en *Mis actividades*. |
| **Calendario** | Festivales, torneos y muestras abiertas a la comunidad. |
| **Ubica** | Mapa interactivo del campus Calle 100 *(en desarrollo)*. |

Para **Bienestar Universitario** incluye un panel de administración que centraliza la gestión y
genera datos de participación que hoy la universidad no tiene reunidos.

**Modelo de negocio:** B2B2C. La UMNG adquiere la plataforma con una licencia anual y los
estudiantes la usan gratis.

## Funcionalidades

### Estudiante
- Registro e inicio de sesión con correo institucional `@unimilitar.edu.co`.
- Recorrido de bienvenida en 4 pasos para elegir intereses; solo se muestra en el **primer ingreso**.
- Inicio con actividades destacadas, recomendaciones según sus intereses y próximos eventos.
- Catálogo con filtros por categoría y búsqueda, ficha de cada actividad y solicitud de inscripción.
- *Mis actividades*: estado de cada solicitud (pendiente, aprobada o rechazada) y opción de cancelarla.

### Administrador (Bienestar Universitario) — `/admin`
- **Resumen:** indicadores y solicitudes pendientes por aprobar.
- **Actividades:** crear, editar y eliminar actividades; gestionar sus inscritos (agregar, aprobar,
  rechazar o retirar estudiantes) respetando los cupos.
- **Calendario:** crear, editar y eliminar eventos, opcionalmente ligados a una actividad.
- **Usuarios:** registro de todos los perfiles con sus intereses, actividades, fecha de registro y
  último ingreso.

## Tecnología

| Capa | Herramienta |
|---|---|
| Interfaz | HTML, CSS, JavaScript, Bootstrap 5, Bootstrap Icons |
| Servidor | Python · Flask (plantillas Jinja2) |
| Datos | Flask-SQLAlchemy · SQLite en desarrollo, MySQL en producción |
| Seguridad | Contraseñas con hash (Werkzeug), sesión firmada, control de acceso por rol |

Se eligió una web app en lugar de una app nativa para llegar a más usuarios con menos tiempo de
desarrollo, dentro del plazo de 16 semanas del proyecto.

## Cómo ejecutarlo

Requisitos: **Python 3.10+** y Git.

```bash
git clone https://github.com/Juanca-48/Campus_vive_UMNG.git
cd Campus_vive_UMNG

python -m venv .venv
.venv\Scripts\activate            # Windows   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

flask --app run crear-admin        # crea la cuenta de Bienestar (pide una contraseña)
python run.py                      # abre http://127.0.0.1:5000
```

- La base de datos (SQLite) se crea sola en `instance/campus_vive.db` y se llena con actividades y
  eventos de ejemplo la primera vez. Cada integrante tiene su propia base local; no se sube al repositorio.
- Los estudiantes se registran desde la pantalla de inicio de sesión.
- La cuenta de administrador por defecto es `bienestar@unimilitar.edu.co`; para otro correo:
  `flask --app run crear-admin --correo nombre@unimilitar.edu.co`.

### Usar MySQL

```sql
CREATE DATABASE campus_vive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```powershell
$env:DATABASE_URL = "mysql+pymysql://usuario:clave@localhost/campus_vive"
flask --app run init-db
flask --app run crear-admin
```

### Variables de entorno

| Variable | Uso | Por defecto |
|---|---|---|
| `DATABASE_URL` | Conexión a la base de datos | SQLite en `instance/` |
| `SECRET_KEY` | Firma de las sesiones. **Cámbiala al publicar.** | clave de desarrollo |

### Pruebas

```bash
python -m unittest discover tests
```

## Estructura

```
app/
  __init__.py      fábrica de la aplicación, filtros de plantilla
  models.py        tablas: usuario, interes, actividad, inscripcion, evento
  cli.py           comandos init-db y crear-admin
  data/mock.py     categorías, novedades y datos de ejemplo
  services/        lógica: catálogo (actividades/eventos) y sesión (acceso, intereses, inscripciones)
  routes/          main (estudiante) · onboarding · auth · admin
  templates/       vistas Jinja2
  static/          estilos (campus.css) y JavaScript
tests/             pruebas de flujo
```

## Estado y próximos pasos

- [x] Interfaz basada en los mockups del pitch
- [x] Registro, inicio de sesión y recorrido de bienvenida
- [x] Inscripciones con control de cupos
- [x] Panel de administración (actividades, calendario, inscritos, usuarios)
- [ ] Mapa interactivo del campus Calle 100 (a la espera del plano)
- [ ] Fotos de actividades subidas desde el panel
- [ ] Protección CSRF en formularios antes del despliegue
- [ ] Despliegue en la nube con MySQL

**Fases futuras:** módulo de Apoyo y Desarrollo Estudiantil, notificaciones, analítica de
participación para Bienestar e integración con sistemas institucionales.

## Equipo — 4 Frames Startup

- Juliana Bonilla Calderón
- Alejandra Bernal Castro
- Paula Romero Rojas
- Juan Camilo Niño

Universidad Militar Nueva Granada · 2026
