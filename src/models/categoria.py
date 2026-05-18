"""Modelo Categoria: taxonomía simple para clasificar prompts."""


class Categoria:
    """Categoría temática asignable a un Prompt."""

    def __init__(self, nombre="", descripcion=""):
        """Inicializa una Categoria.

        :param nombre: Nombre visible de la categoría.
        :param descripcion: Descripción libre, opcional.
        """
        self.nombre = nombre
        self.descripcion = descripcion

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID o None si aún no está persistida.
        """
        return self.__dict__.get("__oid__")


def desasociar_prompts_de_categoria(srp, categoria_oid):
    """Pone a None la categoría de todos los prompts que la referenciaban.

    Evita el borrado en cascada de prompts: la eliminación de una
    categoría no debe destruir contenido del usuario.

    :param srp: Instancia de Sirope.
    :param categoria_oid: OID de la categoría que va a desaparecer.
    :return: Número de prompts actualizados.
    """
    from .prompt import Prompt
    try:
        prompts = list(srp.filter(Prompt, lambda p: p.categoria_oid == categoria_oid))
        for p in prompts:
            p.categoria_oid = None
            srp.save(p)
        return len(prompts)
    except Exception:
        return 0
