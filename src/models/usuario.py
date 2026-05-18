"""Modelo de Usuario y utilidades asociadas para PromptLab.

Define la clase Usuario, compatible con Flask-Login mediante UserMixin,
y funciones auxiliares para localizarlo en Sirope y aplicar las reglas
de integridad referencial al borrar una cuenta.
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Usuario(UserMixin):
    """Representa a una persona registrada en PromptLab.

    El email actúa como identificador funcional (único) y el OID asignado
    por Sirope tras el primer save como identificador interno.
    """

    def __init__(self, email="", nombre="", password=""):
        """Inicializa un Usuario con datos básicos.

        :param email: Correo electrónico, usado como identificador funcional.
        :param nombre: Nombre visible del usuario.
        :param password: Contraseña en texto plano (se almacena hasheada).
        """
        self.email = email
        self.nombre = nombre
        self.password_hash = ""
        self.fecha_registro = datetime.utcnow().isoformat()
        if password:
            self.set_password(password)

    @property
    def oid(self):
        """Devuelve el OID asignado por Sirope.

        :return: OID de Sirope o None si aún no se ha guardado.
        """
        return self.__dict__.get("__oid__")

    def set_password(self, password):
        """Calcula y almacena el hash seguro de la contraseña.

        :param password: Contraseña en texto plano.
        :return: None.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Comprueba si la contraseña en texto plano coincide con el hash.

        :param password: Contraseña a verificar.
        :return: True si coincide, False en caso contrario.
        """
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        """Identificador único usado por Flask-Login.

        :return: Cadena segura derivada del OID de Sirope.
        """
        from sirope_config import get_sirope
        srp = get_sirope()
        return srp.safe_from_oid(self.oid)


def buscar_por_email(srp, email):
    """Busca un Usuario por su email.

    :param srp: Instancia de Sirope.
    :param email: Email a localizar.
    :return: Usuario o None si no existe.
    """
    try:
        return srp.find_first(Usuario, lambda u: u.email == email)
    except Exception:
        return None


def cargar_por_safe_oid(srp, safe_oid_str):
    """Carga un Usuario a partir de su OID seguro (Flask-Login).

    :param srp: Instancia de Sirope.
    :param safe_oid_str: Cadena segura proveniente de `get_id`.
    :return: Usuario o None si no se encuentra.
    """
    try:
        oid = srp.oid_from_safe(safe_oid_str)
        if oid is None:
            return None
        return srp.load(oid)
    except Exception:
        return None


def borrar_usuario_en_cascada(srp, usuario):
    """Elimina un usuario y todo contenido asociado.

    Borra sus prompts (y en cascada evaluaciones/comentarios sobre ellos),
    sus colecciones y sus comentarios/evaluaciones realizados sobre
    prompts de otros usuarios.

    :param srp: Instancia de Sirope.
    :param usuario: Usuario a eliminar.
    :return: True si la operación se completó correctamente.
    """
    from .prompt import Prompt, borrar_prompt_en_cascada
    from .evaluacion import Evaluacion
    from .comentario import Comentario
    from .coleccion import Coleccion

    try:
        usuario_oid = usuario.oid

        prompts_usuario = list(
            srp.filter(Prompt, lambda p: p.usuario_oid == usuario_oid)
        )
        for prompt in prompts_usuario:
            borrar_prompt_en_cascada(srp, prompt)

        colecciones = list(
            srp.filter(Coleccion, lambda c: c.usuario_oid == usuario_oid)
        )
        for col in colecciones:
            srp.delete(col.oid)

        evaluaciones = list(
            srp.filter(Evaluacion, lambda e: e.usuario_oid == usuario_oid)
        )
        for ev in evaluaciones:
            srp.delete(ev.oid)

        comentarios = list(
            srp.filter(Comentario, lambda c: c.usuario_oid == usuario_oid)
        )
        for com in comentarios:
            srp.delete(com.oid)

        srp.delete(usuario_oid)
        return True
    except Exception:
        return False
