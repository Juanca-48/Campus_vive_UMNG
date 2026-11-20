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
| **Conoce** | Foto, horarios, responsable, lugar y cupos disponibles de cada grupo. |
| **Inscríbete** | Solicitud de inscripción en un paso y seguimiento en *Mis actividades*. |
| **Calendario** | Festivales, torneos y muestras abiertas a la comunidad. |
| **Ubica** | Mapa del campus Calle 100 con el punto de cada actividad (*Cómo llegar*). |

Para **Bienestar Universitario** incluye un panel de administración que centraliza la gestión y
genera datos de participación que hoy la universidad no tiene reunidos.

**Modelo de negocio:** B2B2C. La UMNG adquiere la plataforma con una licencia anual y los
estudiantes la usan gratis.

## Funcionalidades

### Estudiante
- Registro e inicio de sesión con correo institucional `@unimilitar.edu.co`.
- Recorrido de bienvenida en 4 pasos (saludo, intereses, grupos recomendados y mapa del campus);
  solo se muestra en el **primer ingreso**.
- Inicio con actividades destacadas, recomendaciones según sus intereses y próximos eventos.
- Catálogo con filtros por categoría y búsqueda, ficha de cada actividad y solicitud de inscripción.
- Mapa del campus: cada actividad marca su lugar sobre la foto aérea de la sede.
- *Mis actividades*: estado de cada solicitud (pendiente, aprobada o rechazada) y opción de cancelarla.
- *Mi perfil* (botón del avatar): código, carrera y semestre, intereses y actividades. Los datos
  académicos se sincronizan en cada ingreso con el directorio de la universidad; por ahora es un
  directorio de prueba con datos inventados.

### Administrador (Bienestar Universitario) — `/admin`
- **Resumen:** indicadores, actividades más y menos concurridas, participación por categoría,
  solicitudes pendientes por aprobar y **reporte descargable en CSV**.
- **Actividades:** crear, editar y eliminar actividades, con días y horas por selectores (formato
  24 h), foto opcional y ubicación marcada con un clic en el mapa; gestionar sus inscritos (agregar,
  aprobar, rechazar o retirar estudiantes) respetando los cupos.
- **Calendario:** crear, editar y eliminar eventos, opcionalmente ligados a una actividad.
- **Usuarios:** registro de todos los perfiles con código, carrera, semestre, intereses,
  actividades, fecha de registro y último ingreso.

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
- Al arrancar, la app agrega a la base las columnas nuevas que falten, así que no hay que borrarla
  cuando cambia el modelo.
- Las fotos que sube el administrador se guardan en la base de datos (máximo 2 MB por foto;
  conviene subirlas ya livianas).
- Los estudiantes se registran desde la pantalla de inicio de sesión.
- La cuenta de administrador por defecto es `bienestar@unimilitar.edu.co`; para otro correo:
  `flask --app run crear-admin --correo nombre@unimilitar.edu.co`.

### Usar MySQL

```sql
CREATE DATABASE campus_vive CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

```powershell
$env:DATABASE_URL = "mysql+pymysql://usuario:clave@localhost/campus_vive"
flask --app run crear-admin        # las tablas se crean solas al arrancar
```

### Variables de entorno

| Variable | Uso | Por defecto |
|---|---|---|
| `DATABASE_URL` | Conexión a la base de datos | SQLite en `instance/` |
| `SECRET_KEY` | Firma de las sesiones. **Obligatoria en Vercel.** | clave de desarrollo |

## Publicar en Vercel

En Vercel el disco es de solo lectura, así que los datos viven en un **MySQL en la nube (Aiven)**.
Si en Vercel falta `SECRET_KEY` o `DATABASE_URL`, la app no arranca y lo dice en el registro.

1. **Base de datos en Aiven.** Crea un servicio MySQL (plan gratuito). En su página de conexión
   copia host, puerto, usuario y contraseña, y descarga el **certificado CA**. Guárdalo en el
   proyecto como `certs/ca.pem` y súbelo al repositorio (es un certificado público, no una clave).
2. **Arma la `DATABASE_URL`** (la conexión va cifrada con ese certificado):
   ```
   mysql+pymysql://USUARIO:CONTRASEÑA@HOST:PUERTO/defaultdb?ssl_ca=certs/ca.pem
   ```
3. **Crea las tablas y la cuenta de Bienestar** desde tu PC, apuntando a Aiven:
   ```powershell
   $env:DATABASE_URL = "mysql+pymysql://...?ssl_ca=certs/ca.pem"
   flask --app run crear-admin        # crea tablas, datos de ejemplo y el admin
   ```
4. **Proyecto en Vercel.** *Add New → Project*, importa el repositorio de GitHub. Vercel reconoce
   Flask solo (entrada `index.py`, Python 3.14 por `.python-version`, dependencias de
   `requirements.txt`). En *Environment Variables* agrega:
   - `DATABASE_URL`: la del paso 2.
   - `SECRET_KEY`: una clave larga al azar, por ejemplo la que imprime
     `python -c "import secrets; print(secrets.token_hex(32))"`.
5. **Deploy.** Cada `push` a `main` vuelve a publicar.

Los archivos de `public/` (estilos, JS e imágenes) los sirve la CDN de Vercel; Flask los sirve en
local desde la misma carpeta. `.vercelignore` deja fuera pruebas, documentos y la base local.

### Pruebas

```bash
python -m unittest discover tests
```

## Estructura

```
app/
  __init__.py      fábrica de la aplicación, filtros de plantilla y actualización de la base
  models.py        tablas: usuario, interes, actividad, inscripcion, evento
  cli.py           comando crear-admin
  data/mock.py     categorías, novedades y datos de ejemplo
  services/        catálogo (actividades/eventos), sesión (acceso, intereses, inscripciones)
                   y directorio (datos académicos del estudiante)
  routes/          main (estudiante) · onboarding · auth · admin
  templates/       vistas Jinja2
public/static/     estilos (campus.css), JavaScript e imágenes (mapa, fotos de actividades)
config.py          configuración y controles para producción
index.py           entrada para Vercel (run.py es la de uso local)
tests/             pruebas de flujo
```

Las fotos de ejemplo de las actividades son de Wikimedia Commons con licencia libre; autores y
licencias en la página **Créditos de fotos** (`/creditos`, enlazada al pie de cada página).

## Estado y próximos pasos

- [x] Interfaz basada en los mockups del pitch
- [x] Registro, inicio de sesión y recorrido de bienvenida
- [x] Inscripciones con control de cupos
- [x] Panel de administración (actividades, calendario, inscritos, usuarios)
- [x] Estadísticas de participación y reporte CSV
- [x] Mapa del campus con la ubicación de cada actividad
- [x] Fotos de actividades (de ejemplo y subidas desde el panel)
- [x] Perfil del estudiante con datos académicos sincronizados (directorio de prueba)
- [x] Página de créditos de las fotos
- [x] Listo para Vercel + MySQL en Aiven (conexión cifrada, cookies seguras)
- [ ] Conectar el directorio real de la universidad
- [ ] Protección CSRF completa con tokens (hoy la cookie `SameSite=Lax` frena los envíos desde otros sitios)

**Fases futuras:** módulo de Apoyo y Desarrollo Estudiantil, notificaciones, analítica de
participación para Bienestar e integración con sistemas institucionales.

## Equipo — 4 Frames Startup

- Juliana Bonilla Calderón
- Alejandra Bernal Castro
- Paula Romero Rojas
- Juan Camilo Niño

Universidad Militar Nueva Granada · 2026
