"""Modelo Evaluacion: registro de la prueba de un Prompt con un modelo IA.

Cada evaluación recoge el modelo usado, la respuesta obtenida, una
puntuación (1-5) y notas libres del evaluador.
"""

from datetime import datetime


class Evaluacion:
    """Evaluación realizada por un usuario sobre un Prompt concreto."""

    def __init__(self, prompt_oid=None, usuario_oid=None, modelo="",
                 respuesta="", puntuacion=0, notas=""):
        """Inicializa una Evaluacion.

        :param prompt_oid: OID del Prompt evaluado.
        :param usuario_oid: OID del Usuario que realiza la evaluación.
        :param modelo: Identificador del modelo de IA usado.
        :param respuesta: Texto de respuesta obtenido del modelo.
        :param puntuacion: Valor entero entre 1 y 5.
        :param notas: Observaciones libres del evaluador.
        """
        self.prompt_oid = prompt_oid
        self.usuario_oid = usuario_oid
        self.modelo = modelo
        self.respuesta = respuesta
        try:
            self.puntuacion = max(1, min(5, int(puntuacion)))
        except (ValueError, TypeError):
            self.puntuacion = 1
        self.notas = notas
        self.fecha = datetime.utcnow().isoformat()

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID o None si aún no está persistida.
        """
        return self.__dict__.get("__oid__")


def evaluaciones_de_prompt(srp, prompt_oid):
    """Recupera todas las evaluaciones de un Prompt.

    :param srp: Instancia de Sirope.
    :param prompt_oid: OID del Prompt.
    :return: Lista de Evaluaciones ordenada por fecha descendente.
    """
    try:
        lst = list(srp.filter(Evaluacion, lambda e: e.prompt_oid == prompt_oid))
        lst.sort(key=lambda e: e.fecha, reverse=True)
        return lst
    except Exception:
        return []
