"""Rutas para crear y borrar comentarios sobre prompts."""

from flask import Blueprint, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from sirope_config import get_sirope, oid_from_safe
from models.comentario import Comentario
from models.prompt import cargar_prompt

bp = Blueprint("comentarios", __name__, url_prefix="/comentarios")


@bp.route("/nuevo/<prompt_safe>", methods=["POST"])
@login_required
def nuevo(prompt_safe):
    """Añade un comentario a un prompt.

    :param prompt_safe: OID seguro del Prompt comentado.
    :return: Redirección al detalle del prompt.
    """
    srp = get_sirope()
    prompt_oid = oid_from_safe(srp, prompt_safe)
    prompt = cargar_prompt(srp, prompt_oid)
    if not prompt:
        abort(404)

    texto = (request.form.get("texto") or "").strip()
    if not texto:
        flash("El comentario no puede estar vacío.", "error")
        return redirect(url_for("prompts.detalle", safe=prompt_safe))

    try:
        com = Comentario(prompt_oid=prompt.oid,
                         usuario_oid=current_user.oid, texto=texto)
        srp.save(com)
        flash("Comentario publicado.", "success")
    except Exception:
        flash("No se pudo publicar el comentario.", "error")

    return redirect(url_for("prompts.detalle", safe=prompt_safe))


@bp.route("/<safe>/borrar", methods=["POST"])
@login_required
def borrar(safe):
    """Borra un comentario. Permitido al autor o al autor del prompt.

    :param safe: OID seguro del Comentario.
    :return: Redirección al detalle del prompt asociado.
    """
    srp = get_sirope()
    oid = oid_from_safe(srp, safe)
    try:
        com = srp.load(oid) if oid else None
    except Exception:
        com = None
    if not com:
        abort(404)

    prompt = cargar_prompt(srp, com.prompt_oid)
    prompt_safe = srp.safe_from_oid(com.prompt_oid) if com.prompt_oid else None

    autor_prompt = prompt.usuario_oid if prompt else None
    if (com.usuario_oid != current_user.oid
            and autor_prompt != current_user.oid):
        flash("No tienes permiso para borrar este comentario.", "error")
        if prompt_safe:
            return redirect(url_for("prompts.detalle", safe=prompt_safe))
        return redirect(url_for("prompts.lista"))

    try:
        srp.delete(com.oid)
        flash("Comentario eliminado.", "success")
    except Exception:
        flash("No se pudo eliminar el comentario.", "error")

    if prompt_safe:
        return redirect(url_for("prompts.detalle", safe=prompt_safe))
    return redirect(url_for("prompts.lista"))
