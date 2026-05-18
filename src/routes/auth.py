"""Rutas de autenticación: registro, inicio y cierre de sesión."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from sirope_config import get_sirope
from models.usuario import Usuario, buscar_por_email

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Inicia sesión de un usuario existente.

    :return: Render del formulario o redirección al dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Email y contraseña son obligatorios.", "error")
            return render_template("auth/login.html")

        srp = get_sirope()
        usuario = buscar_por_email(srp, email)
        if not usuario or not usuario.check_password(password):
            flash("Credenciales incorrectas.", "error")
            return render_template("auth/login.html")

        login_user(usuario)
        flash(f"Bienvenido, {usuario.nombre}.", "success")
        destino = request.args.get("next") or url_for("dashboard")
        return redirect(destino)

    return render_template("auth/login.html")


@bp.route("/registro", methods=["GET", "POST"])
def registro():
    """Registra un nuevo usuario en la plataforma.

    :return: Render del formulario o redirección al dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        nombre = (request.form.get("nombre") or "").strip()
        password = request.form.get("password") or ""
        password2 = request.form.get("password2") or ""

        if not email or not nombre or not password:
            flash("Todos los campos son obligatorios.", "error")
            return render_template("auth/registro.html",
                                   email=email, nombre=nombre)
        if password != password2:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("auth/registro.html",
                                   email=email, nombre=nombre)
        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("auth/registro.html",
                                   email=email, nombre=nombre)

        srp = get_sirope()
        if buscar_por_email(srp, email):
            flash("Ya existe una cuenta con ese email.", "error")
            return render_template("auth/registro.html",
                                   email=email, nombre=nombre)

        try:
            usuario = Usuario(email=email, nombre=nombre, password=password)
            srp.save(usuario)
        except Exception:
            flash("No se ha podido crear la cuenta. Inténtalo de nuevo.", "error")
            return render_template("auth/registro.html",
                                   email=email, nombre=nombre)

        login_user(usuario)
        flash("Cuenta creada correctamente.", "success")
        return redirect(url_for("dashboard"))

    return render_template("auth/registro.html")


@bp.route("/logout")
@login_required
def logout():
    """Cierra la sesión del usuario actual.

    :return: Redirección a la página de login.
    """
    logout_user()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("auth.login"))
