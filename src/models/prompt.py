"""Modelo Prompt y utilidades de persistencia e integridad referencial.

Un Prompt representa el texto principal con el que se interactúa con un
modelo de IA. Mantiene relaciones con Categoria, Usuario (autor),
Evaluacion (1 a N), Comentario (1 a N) y Coleccion (N a N).
"""

from datetime import datetime


class Prompt:
    """Representa un prompt creado por un usuario.

    Almacena título, contenido, categoría opcional, autor, fecha de
    creación y una lista de tags libres.
    """

    def __init__(self, titulo="", contenido="", categoria_oid=None,
                 usuario_oid=None, tags=None):
        """Inicializa un Prompt nuevo.

        :param titulo: Título corto y descriptivo.
        :param contenido: Texto del prompt.
        :param categoria_oid: OID de la Categoria asociada (o None).
        :param usuario_oid: OID del Usuario autor.
        :param tags: Lista de etiquetas (cadenas).
        """
        self.titulo = titulo
        self.contenido = contenido
        self.categoria_oid = categoria_oid
        self.usuario_oid = usuario_oid
        self.fecha_creacion = datetime.utcnow().isoformat()
        self.tags = list(tags) if tags else []

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID de Sirope o None si aún no se ha guardado.
        """
        return self.__dict__.get("__oid__")


def cargar_prompt(srp, oid):
    """Carga un Prompt y comprueba que existe.

    :param srp: Instancia de Sirope.
    :param oid: OID del Prompt.
    :return: Objeto Prompt o None.
    """
    try:
        if oid is None:
            return None
        return srp.load(oid)
    except Exception:
        return None


def borrar_prompt_en_cascada(srp, prompt):
    """Elimina un prompt junto a evaluaciones, comentarios y referencias.

    También retira el OID del prompt de cualquier colección que lo
    contenga, manteniendo la integridad referencial.

    :param srp: Instancia de Sirope.
    :param prompt: Prompt a eliminar.
    :return: True si la operación tuvo éxito.
    """
    from .evaluacion import Evaluacion
    from .comentario import Comentario
    from .coleccion import Coleccion

    try:
        prompt_oid = prompt.oid

        evaluaciones = list(
            srp.filter(Evaluacion, lambda e: e.prompt_oid == prompt_oid)
        )
        for ev in evaluaciones:
            srp.delete(ev.oid)

        comentarios = list(
            srp.filter(Comentario, lambda c: c.prompt_oid == prompt_oid)
        )
        for com in comentarios:
            srp.delete(com.oid)

        colecciones = list(
            srp.filter(Coleccion, lambda c: prompt_oid in (c.prompt_oids or []))
        )
        for col in colecciones:
            col.prompt_oids = [o for o in col.prompt_oids if o != prompt_oid]
            srp.save(col)

        srp.delete(prompt_oid)
        return True
    except Exception:
        return False


def buscar_prompts(srp, termino=None):
    """Devuelve una lista de prompts, filtrando opcionalmente por término.

    El término se compara con el título y con las tags (case insensitive).

    :param srp: Instancia de Sirope.
    :param termino: Texto a buscar (opcional).
    :return: Lista de Prompts ordenados por fecha de creación descendente.
    """
    from .prompt import Prompt
    try:
        if termino:
            t = termino.strip().lower()
            resultado = list(srp.filter(
                Prompt,
                lambda p: t in (p.titulo or "").lower()
                or any(t in (tag or "").lower() for tag in (p.tags or []))
            ))
        else:
            resultado = list(srp.load_all(Prompt))
        resultado.sort(key=lambda p: p.fecha_creacion, reverse=True)
        return resultado
    except Exception:
        return []
