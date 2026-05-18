"""Punto de entrada de la aplicación PromptLab.

Define la fábrica de la aplicación Flask, registra los blueprints,
configura Flask-Login, define el dashboard, los manejadores de error
y la ruta raíz.
"""

import os
from datetime import datetime

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user, login_required

from sirope_config import get_sirope
from models.usuario import Usuario, cargar_por_safe_oid
from models.prompt import Prompt
from models.coleccion import Coleccion
from models.categoria import Categoria

from routes.auth import bp as bp_auth
from routes.prompts import bp as bp_prompts
from routes.evaluaciones import bp as bp_evaluaciones
from routes.comentarios import bp as bp_comentarios
from routes.colecciones import bp as bp_colecciones
from routes.categorias import bp as bp_categorias


def crear_app():
    """Construye y configura la aplicación Flask.

    :return: Instancia configurada de :class:`flask.Flask`.
    """
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "promptlab-dev-secret-change-me"
    )

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor inicia sesión para continuar."
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def cargar_usuario(user_id):
        """Carga el usuario actual a partir del ID almacenado en la sesión.

        :param user_id: Identificador serializado (safe OID).
        :return: Usuario o None.
        """
        srp = get_sirope()
        return cargar_por_safe_oid(srp, user_id)

    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_prompts)
    app.register_blueprint(bp_evaluaciones)
    app.register_blueprint(bp_comentarios)
    app.register_blueprint(bp_colecciones)
    app.register_blueprint(bp_categorias)

    @app.route("/")
    def index():
        """Ruta raíz: redirige al dashboard si hay sesión, si no al login.

        :return: Redirección HTTP.
        """
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return redirect(url_for("auth.login"))

    @app.route("/dashboard")
    @login_required
    def dashboard():
        """Panel resumen del usuario con accesos rápidos.

        :return: Render del dashboard.
        """
        srp = get_sirope()
        try:
            mis_prompts = list(srp.filter(
                Prompt, lambda p: p.usuario_oid == current_user.oid
            ))
        except Exception:
            mis_prompts = []
        try:
            mis_colecciones = list(srp.filter(
                Coleccion, lambda c: c.usuario_oid == current_user.oid
            ))
        except Exception:
            mis_colecciones = []
        try:
            ultimos = list(srp.load_all(Prompt))
        except Exception:
            ultimos = []
        ultimos.sort(key=lambda p: getattr(p, "fecha_creacion", ""), reverse=True)
        ultimos = ultimos[:5]

        ultimos_items = [
            {"prompt": p, "safe": srp.safe_from_oid(p.oid)} for p in ultimos
        ]

        return render_template(
            "dashboard.html",
            num_prompts=len(mis_prompts),
            num_colecciones=len(mis_colecciones),
            ultimos=ultimos_items,
        )

    @app.errorhandler(404)
    def err_404(_e):
        """Manejador para páginas no encontradas.

        :param _e: Excepción original (ignorada).
        :return: Render de la plantilla 404 con código 404.
        """
        return render_template("errores/404.html"), 404

    @app.errorhandler(500)
    def err_500(_e):
        """Manejador para errores internos del servidor.

        :param _e: Excepción original (ignorada).
        :return: Render de la plantilla 500 con código 500.
        """
        return render_template("errores/500.html"), 500

    @app.template_filter("fechabonita")
    def fechabonita(valor):
        """Filtro Jinja que convierte una fecha ISO en formato legible.

        :param valor: Cadena ISO 8601 o datetime.
        :return: Cadena con formato 'YYYY-MM-DD HH:MM'.
        """
        if not valor:
            return ""
        try:
            if isinstance(valor, datetime):
                dt = valor
            else:
                dt = datetime.fromisoformat(valor)
            return dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            return str(valor)

    return app


app = crear_app()


if __name__ == "__main__":
    app.run(debug=True)
