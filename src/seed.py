"""Pobla la base de datos Redis con datos de demostración.

Crea dos usuarios, categorías, prompts con tags, colecciones,
comentarios y evaluaciones para poder explorar la aplicación
sin necesidad de introducir datos manualmente.

Uso:
    python seed.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from sirope_config import get_sirope
from models.usuario import Usuario, buscar_por_email
from models.categoria import Categoria
from models.prompt import Prompt
from models.coleccion import Coleccion
from models.comentario import Comentario
from models.evaluacion import Evaluacion


USUARIOS = [
    {"email": "ana@demo.com",   "nombre": "Ana García",   "password": "demo1234"},
    {"email": "luis@demo.com",  "nombre": "Luis Martín",  "password": "demo1234"},
]

CATEGORIAS = [
    {"nombre": "Redacción",      "descripcion": "Prompts para escribir textos y artículos"},
    {"nombre": "Código",         "descripcion": "Prompts orientados a programación"},
    {"nombre": "Brainstorming",  "descripcion": "Generación de ideas y creatividad"},
    {"nombre": "Traducción",     "descripcion": "Prompts para traducir contenido"},
]

PROMPTS = [
    {
        "titulo": "Resumen ejecutivo",
        "contenido": "Resume el siguiente texto en tres puntos clave, usando lenguaje formal y directo:\n\n{texto}",
        "categoria": "Redacción",
        "autor": "ana@demo.com",
        "tags": ["resumen", "formal", "ejecutivo"],
    },
    {
        "titulo": "Revisión de código Python",
        "contenido": "Revisa el siguiente fragmento de código Python, identifica errores, sugiere mejoras de legibilidad y añade type hints donde falten:\n\n```python\n{codigo}\n```",
        "categoria": "Código",
        "autor": "ana@demo.com",
        "tags": ["python", "review", "refactor"],
    },
    {
        "titulo": "Generador de nombres de producto",
        "contenido": "Propón diez nombres originales y memorables para un producto de {sector}. Los nombres deben ser cortos (máximo dos palabras), sonoros y fáciles de pronunciar en español.",
        "categoria": "Brainstorming",
        "autor": "luis@demo.com",
        "tags": ["nombres", "marketing", "creatividad"],
    },
    {
        "titulo": "Traducción técnica EN→ES",
        "contenido": "Traduce al español el siguiente fragmento técnico manteniendo los términos del sector sin españolizar si son más claros en inglés:\n\n{texto_en}",
        "categoria": "Traducción",
        "autor": "luis@demo.com",
        "tags": ["traducción", "técnico", "inglés"],
    },
    {
        "titulo": "Email profesional de seguimiento",
        "contenido": "Redacta un email de seguimiento después de una reunión. Debe ser conciso, recordar los puntos acordados y proponer un próximo paso concreto. Contexto: {contexto}",
        "categoria": "Redacción",
        "autor": "ana@demo.com",
        "tags": ["email", "profesional", "seguimiento"],
    },
    {
        "titulo": "Explicar concepto a no técnicos",
        "contenido": "Explica {concepto} a alguien sin conocimientos técnicos usando una analogía cotidiana. Usa un tono amigable y no más de cuatro párrafos.",
        "categoria": "Redacción",
        "autor": "luis@demo.com",
        "tags": ["divulgación", "analogía", "explicación"],
    },
]

COLECCIONES = [
    {
        "nombre": "Mis prompts de escritura",
        "descripcion": "Prompts que uso para redactar documentos profesionales",
        "propietario": "ana@demo.com",
        "prompts": ["Resumen ejecutivo", "Email profesional de seguimiento"],
        "publica": True,
    },
    {
        "nombre": "Toolkit de desarrollo",
        "descripcion": "Prompts útiles para tareas de programación y documentación",
        "propietario": "luis@demo.com",
        "prompts": ["Revisión de código Python", "Explicar concepto a no técnicos"],
        "publica": True,
    },
]

COMENTARIOS = [
    {"prompt": "Resumen ejecutivo",        "autor": "luis@demo.com", "texto": "Muy útil para informes de dirección, lo uso cada semana."},
    {"prompt": "Revisión de código Python","autor": "luis@demo.com", "texto": "Le añadí la instrucción de seguir PEP 8 y mejora bastante."},
    {"prompt": "Generador de nombres",     "autor": "ana@demo.com",  "texto": "Funciona genial para startups. Le paso el sector y el target y da resultados muy creativos."},
    {"prompt": "Revisión de código Python","autor": "ana@demo.com",  "texto": "¿Has probado a pedir también que genere los tests unitarios?"},
]

EVALUACIONES = [
    {"prompt": "Resumen ejecutivo",         "autor": "luis@demo.com", "modelo": "GPT-4o",        "puntuacion": 5, "respuesta": "Tres puntos bien estructurados y con registro formal.", "notas": "Perfecto para presentaciones a comité."},
    {"prompt": "Revisión de código Python", "autor": "ana@demo.com",  "modelo": "Claude 3.5",    "puntuacion": 4, "respuesta": "Detectó tres bugs y sugirió type hints en todas las funciones.", "notas": "Muy completo, aunque a veces es demasiado verboso."},
    {"prompt": "Generador de nombres",      "autor": "ana@demo.com",  "modelo": "GPT-4o",        "puntuacion": 4, "respuesta": "Propuso: Nexio, Lumera, Vortex, Zephyr, Orbit...", "notas": "Buena variedad, algunos ya están registrados como marcas."},
    {"prompt": "Email profesional de seguimiento", "autor": "luis@demo.com", "modelo": "Gemini 1.5", "puntuacion": 3, "respuesta": "Email correcto pero algo genérico.", "notas": "Necesita más contexto para personalizar bien."},
]


def main():
    srp = get_sirope()

    print("Creando usuarios...")
    usuarios = {}
    for datos in USUARIOS:
        existente = buscar_por_email(srp, datos["email"])
        if existente:
            print(f"  · {datos['email']} ya existe, se omite.")
            usuarios[datos["email"]] = existente
        else:
            u = Usuario(email=datos["email"], nombre=datos["nombre"], password=datos["password"])
            srp.save(u)
            usuarios[datos["email"]] = u
            print(f"  + {datos['email']} creado.")

    print("Creando categorías...")
    categorias = {}
    existentes = {c.nombre: c for c in srp.load_all(Categoria)}
    for datos in CATEGORIAS:
        if datos["nombre"] in existentes:
            print(f"  · '{datos['nombre']}' ya existe, se omite.")
            categorias[datos["nombre"]] = existentes[datos["nombre"]]
        else:
            cat = Categoria(nombre=datos["nombre"], descripcion=datos["descripcion"])
            srp.save(cat)
            categorias[datos["nombre"]] = cat
            print(f"  + '{datos['nombre']}' creada.")

    print("Creando prompts...")
    prompts_map = {}
    existentes_p = {p.titulo: p for p in srp.load_all(Prompt)}
    for datos in PROMPTS:
        if datos["titulo"] in existentes_p:
            print(f"  · '{datos['titulo']}' ya existe, se omite.")
            prompts_map[datos["titulo"]] = existentes_p[datos["titulo"]]
        else:
            cat_oid = categorias[datos["categoria"]].oid if datos["categoria"] in categorias else None
            autor_oid = usuarios[datos["autor"]].oid
            p = Prompt(
                titulo=datos["titulo"],
                contenido=datos["contenido"],
                categoria_oid=cat_oid,
                usuario_oid=autor_oid,
                tags=datos["tags"],
            )
            srp.save(p)
            prompts_map[datos["titulo"]] = p
            print(f"  + '{datos['titulo']}' creado.")

    print("Creando colecciones...")
    existentes_c = {c.nombre: c for c in srp.load_all(Coleccion)}
    for datos in COLECCIONES:
        if datos["nombre"] in existentes_c:
            print(f"  · '{datos['nombre']}' ya existe, se omite.")
        else:
            prop_oid = usuarios[datos["propietario"]].oid
            p_oids = [prompts_map[t].oid for t in datos["prompts"] if t in prompts_map]
            col = Coleccion(
                nombre=datos["nombre"],
                descripcion=datos["descripcion"],
                usuario_oid=prop_oid,
                prompt_oids=p_oids,
                publica=datos["publica"],
            )
            srp.save(col)
            print(f"  + '{datos['nombre']}' creada.")

    print("Creando comentarios...")
    for datos in COMENTARIOS:
        titulo = datos["prompt"]
        if titulo not in prompts_map:
            continue
        com = Comentario(
            prompt_oid=prompts_map[titulo].oid,
            usuario_oid=usuarios[datos["autor"]].oid,
            texto=datos["texto"],
        )
        srp.save(com)
        print(f"  + Comentario en '{titulo}'.")

    print("Creando evaluaciones...")
    for datos in EVALUACIONES:
        titulo = datos["prompt"]
        if titulo not in prompts_map:
            continue
        ev = Evaluacion(
            prompt_oid=prompts_map[titulo].oid,
            usuario_oid=usuarios[datos["autor"]].oid,
            modelo=datos["modelo"],
            respuesta=datos["respuesta"],
            puntuacion=datos["puntuacion"],
            notas=datos["notas"],
        )
        srp.save(ev)
        print(f"  + Evaluación en '{titulo}' ({datos['puntuacion']}/5).")

    print()
    print("Seed completado. Puedes iniciar sesión con:")
    for u in USUARIOS:
        print(f"  Email: {u['email']}  |  Contraseña: {u['password']}")


if __name__ == "__main__":
    main()
