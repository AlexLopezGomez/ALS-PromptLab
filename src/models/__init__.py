"""Paquete de modelos de dominio de PromptLab.

Reúne las clases de dominio (Usuario, Prompt, Evaluacion, Comentario,
Coleccion y Categoria) así como sus funciones auxiliares de
persistencia e integridad referencial.
"""

from .usuario import Usuario
from .prompt import Prompt
from .evaluacion import Evaluacion
from .comentario import Comentario
from .coleccion import Coleccion
from .categoria import Categoria

__all__ = [
    "Usuario",
    "Prompt",
    "Evaluacion",
    "Comentario",
    "Coleccion",
    "Categoria",
]
