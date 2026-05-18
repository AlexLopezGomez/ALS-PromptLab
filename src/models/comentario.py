"""Modelo Comentario: aportación de discusión sobre un Prompt."""

from datetime import datetime


class Comentario:
    """Comentario textual de un usuario sobre un Prompt."""

    def __init__(self, prompt_oid=None, usuario_oid=None, texto=""):
        """Inicializa un Comentario.

        :param prompt_oid: OID del Prompt comentado.
        :param usuario_oid: OID del Usuario autor del comentario.
        :param texto: Contenido del comentario.
        """
        self.prompt_oid = prompt_oid
        self.usuario_oid = usuario_oid
        self.texto = texto
        self.fecha = datetime.utcnow().isoformat()

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID o None si aún no está persistido.
        """
        return self.__dict__.get("__oid__")


def comentarios_de_prompt(srp, prompt_oid):
    """Recupera todos los comentarios de un Prompt ordenados por fecha.

    :param srp: Instancia de Sirope.
    :param prompt_oid: OID del Prompt.
    :return: Lista de Comentarios.
    """
    try:
        lst = list(srp.filter(Comentario, lambda c: c.prompt_oid == prompt_oid))
        lst.sort(key=lambda c: c.fecha)
        return lst
    except Exception:
        return []
