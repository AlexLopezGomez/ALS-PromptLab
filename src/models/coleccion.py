"""Modelo Coleccion: agrupación temática de prompts pertenecientes a un usuario."""


class Coleccion:
    """Conjunto ordenado de Prompts agrupados por un usuario."""

    def __init__(self, nombre="", descripcion="", usuario_oid=None,
                 prompt_oids=None, publica=False):
        """Inicializa una Coleccion.

        :param nombre: Nombre visible de la colección.
        :param descripcion: Descripción libre.
        :param usuario_oid: OID del usuario propietario.
        :param prompt_oids: Lista inicial de OIDs de prompts.
        :param publica: Si es True, otros usuarios podrán verla.
        """
        self.nombre = nombre
        self.descripcion = descripcion
        self.usuario_oid = usuario_oid
        self.prompt_oids = list(prompt_oids) if prompt_oids else []
        self.publica = bool(publica)

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID o None si aún no está persistida.
        """
        return self.__dict__.get("__oid__")


def colecciones_de_usuario(srp, usuario_oid):
    """Devuelve las colecciones pertenecientes a un usuario.

    :param srp: Instancia de Sirope.
    :param usuario_oid: OID del usuario propietario.
    :return: Lista de Colecciones.
    """
    try:
        return list(srp.filter(Coleccion, lambda c: c.usuario_oid == usuario_oid))
    except Exception:
        return []


def colecciones_publicas(srp, excluir_usuario_oid=None):
    """Devuelve las colecciones marcadas como públicas.

    :param srp: Instancia de Sirope.
    :param excluir_usuario_oid: OID a excluir (típicamente el del usuario actual).
    :return: Lista de Colecciones públicas de otros usuarios.
    """
    try:
        return list(srp.filter(
            Coleccion,
            lambda c: c.publica and c.usuario_oid != excluir_usuario_oid
        ))
    except Exception:
        return []
