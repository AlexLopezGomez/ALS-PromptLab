"""Configuración y utilidades de acceso a Sirope sobre Redis.

Este módulo expone una única función `get_sirope` que devuelve una
instancia de Sirope conectada a Redis. Se usa desde rutas y modelos
para evitar duplicar la lógica de conexión.
"""

import os
import redis
import sirope


def get_sirope():
    """Crea una instancia de Sirope conectada a Redis.

    Prioriza REDIS_URL (formato Railway/Heroku). Si no existe, usa
    REDIS_HOST, REDIS_PORT y REDIS_DB para desarrollo local.

    :return: Instancia de :class:`sirope.Sirope` lista para usarse.
    """
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        cliente_redis = redis.from_url(redis_url)
    else:
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        db = int(os.environ.get("REDIS_DB", "0"))
        cliente_redis = redis.Redis(host=host, port=port, db=db)
    return sirope.Sirope(cliente_redis)


def safe_oid(srp, obj):
    """Devuelve la representación segura para URL del OID de un objeto.

    :param srp: Instancia de Sirope.
    :param obj: Objeto previamente persistido con OID.
    :return: Cadena segura para usar en URLs.
    """
    return srp.safe_from_oid(obj.__dict__["__oid__"])


def oid_from_safe(srp, cadena):
    """Recupera un OID a partir de su representación segura.

    :param srp: Instancia de Sirope.
    :param cadena: Cadena devuelta previamente por `safe_from_oid`.
    :return: OID interpretable por Sirope, o None si la cadena no es válida.
    """
    try:
        return srp.oid_from_safe(cadena)
    except Exception:
        return None
