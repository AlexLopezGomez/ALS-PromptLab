# PromptLab

Aplicación web para gestionar, organizar y evaluar prompts de IA. Práctica de
la asignatura **ALS** desarrollada con **Flask**, **Jinja2**, **Flask-Login** y
**Sirope** sobre **Redis**.

## Entidades

La aplicación gestiona cinco entidades además del usuario:

- **Prompt**: texto principal con título, contenido, categoría y etiquetas.
- **Categoria**: clasificación temática de los prompts.
- **Coleccion**: agrupación de prompts creada por un usuario.
- **Comentario**: comentario libre asociado a un prompt.
- **Evaluacion**: puntuación numérica de 1 a 5 con texto opcional.

Cada entidad tiene su propio módulo en `models/` y su blueprint en `routes/`.

## Requisitos

- Python 3.10 o superior.
- Redis en ejecución local (por defecto en `localhost:6379`).
- Paquetes Python listados en `requirements.txt`:
  - `flask`
  - `flask-login`
  - `sirope`
  - `redis`
  - `werkzeug`

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate          # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

En una terminal, arranca Redis:

```bash
redis-server
```

En otra terminal, dentro del directorio del proyecto:

```bash
flask run
```

La aplicación quedará accesible en `http://127.0.0.1:5000/`.

### Variables de entorno opcionales

- `SECRET_KEY`: clave secreta de Flask (por defecto, valor de desarrollo).
- `REDIS_HOST`: host de Redis (por defecto `localhost`).
- `REDIS_PORT`: puerto de Redis (por defecto `6379`).
- `REDIS_DB`: número de base de datos de Redis (por defecto `0`).

## Datos de demostración (opcional)

Para poblar la base de datos con usuarios, prompts, categorías, colecciones,
comentarios y evaluaciones de ejemplo, ejecuta desde el directorio `src/`:

```bash
python seed.py
```

El script es idempotente: si ya existe algún dato, lo omite sin duplicarlo.
Tras ejecutarlo puedes iniciar sesión con cualquiera de estas cuentas:

| Email           | Contraseña |
|-----------------|------------|
| ana@demo.com    | demo1234   |
| luis@demo.com   | demo1234   |

## Uso

1. Regístrate en `/auth/registro` o usa una cuenta de demostración (ver arriba).
2. Desde el dashboard puedes crear prompts, colecciones y categorías.
3. Cualquier usuario autenticado puede comentar y evaluar prompts de otros.
4. El autor de un prompt o comentario puede borrarlo; al eliminar un prompt
   se eliminan en cascada sus evaluaciones, comentarios y referencias en
   colecciones.

## Estructura del proyecto

```
src/
├── app.py                  # Fábrica Flask, rutas raíz y manejadores de error
├── sirope_config.py        # Conexión a Sirope/Redis y utilidades de OID
├── main.py                 # Punto de entrada alternativo
├── requirements.txt
├── models/                 # Una clase por entidad
├── routes/                 # Un blueprint por entidad
├── templates/              # Plantillas Jinja2 organizadas por entidad
└── static/css/             # Hojas de estilo
```
