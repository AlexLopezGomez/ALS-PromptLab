"""Rutas para gestionar evaluaciones de prompts."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from sirope_config import get_sirope, oid_from_safe, safe_oid
from models.evaluacion import Evaluacion
from models.prompt import cargar_prompt

bp = Blueprint("evaluaciones", __name__, url_prefix="/evaluaciones")


def _cargar_eval(srp, safe):
    """Carga una Evaluacion desde su OID seguro o aborta con 404.

    :param srp: Instancia de Sirope.
    :param safe: OID seguro.
    :return: Evaluacion cargada.
    """
    oid = oid_from_safe(srp, safe)
    try:
        ev = srp.load(oid) if oid else None
    except Exception:
        ev = None
    if not ev:
        abort(404)
    return ev


@bp.route("/nuevo/<prompt_safe>", methods=["GET", "POST"])
@login_required
def nuevo(prompt_safe):
    """Crea una evaluación nueva para un prompt.

    :param prompt_safe: OID seguro del Prompt evaluado.
    :return: Render del formulario o redirección al detalle del prompt.
    """
    srp = get_sirope()
    prompt_oid = oid_from_safe(srp, prompt_safe)
    prompt = cargar_prompt(srp, prompt_oid)
    if not prompt:
        abort(404)

    if request.method == "POST":
        modelo = (request.form.get("modelo") or "").strip()
        respuesta = (request.form.get("respuesta") or "").strip()
        puntuacion = request.form.get("puntuacion") or "0"
        notas = (request.form.get("notas") or "").strip()

        if not modelo or not respuesta:
            flash("Modelo y respuesta son obligatorios.", "error")
            return render_template("evaluaciones/form.html",
                                   prompt=prompt, prompt_safe=prompt_safe,
                                   evaluacion=None,
                                   form={"modelo": modelo, "respuesta": respuesta,
                                         "puntuacion": puntuacion, "notas": notas})
        try:
            ev = Evaluacion(prompt_oid=prompt.oid,
                            usuario_oid=current_user.oid,
                            modelo=modelo, respuesta=respuesta,
                            puntuacion=puntuacion, notas=notas)
            srp.save(ev)
        except Exception:
            flash("No se pudo guardar la evaluación.", "error")
            return redirect(url_for("prompts.detalle", safe=prompt_safe))

        flash("Evaluación añadida.", "success")
        return redirect(url_for("prompts.detalle", safe=prompt_safe))

    return render_template("evaluaciones/form.html",
                           prompt=prompt, prompt_safe=prompt_safe,
                           evaluacion=None, form={})


@bp.route("/<safe>/editar", methods=["GET", "POST"])
@login_required
def editar(safe):
    """Edita una evaluación existente; solo el autor original.

    :param safe: OID seguro de la Evaluacion.
    :return: Render del formulario o redirección al detalle del prompt.
    """
    srp = get_sirope()
    ev = _cargar_eval(srp, safe)
    if ev.usuario_oid != current_user.oid:
        flash("No tienes permiso para editar esta evaluación.", "error")
        return redirect(url_for("prompts.detalle",
                                safe=srp.safe_from_oid(ev.prompt_oid)))

    prompt = cargar_prompt(srp, ev.prompt_oid)
    if not prompt:
        flash("El prompt asociado ya no existe.", "error")
        return redirect(url_for("prompts.lista"))
    prompt_safe = srp.safe_from_oid(prompt.oid)

    if request.method == "POST":
        modelo = (request.form.get("modelo") or "").strip()
        respuesta = (request.form.get("respuesta") or "").strip()
        puntuacion = request.form.get("puntuacion") or "0"
        notas = (request.form.get("notas") or "").strip()

        if not modelo or not respuesta:
            flash("Modelo y respuesta son obligatorios.", "error")
            return render_template("evaluaciones/form.html",
                                   prompt=prompt, prompt_safe=prompt_safe,
                                   evaluacion=ev, safe=safe,
                                   form={"modelo": modelo, "respuesta": respuesta,
                                         "puntuacion": puntuacion, "notas": notas})

        try:
            ev.modelo = modelo
            ev.respuesta = respuesta
            try:
                ev.puntuacion = max(1, min(5, int(puntuacion)))
            except (ValueError, TypeError):
                ev.puntuacion = 1
            ev.notas = notas
            srp.save(ev)
        except Exception:
            flash("No se pudo actualizar la evaluación.", "error")
            return redirect(url_for("prompts.detalle", safe=prompt_safe))

        flash("Evaluación actualizada.", "success")
        return redirect(url_for("prompts.detalle", safe=prompt_safe))

    form = {
        "modelo": ev.modelo,
        "respuesta": ev.respuesta,
        "puntuacion": ev.puntuacion,
        "notas": ev.notas,
    }
    return render_template("evaluaciones/form.html",
                           prompt=prompt, prompt_safe=prompt_safe,
                           evaluacion=ev, safe=safe, form=form)


@bp.route("/<safe>/borrar", methods=["POST"])
@login_required
def borrar(safe):
    """Elimina una evaluación; solo el autor original.

    :param safe: OID seguro de la Evaluacion.
    :return: Redirección al detalle del prompt.
    """
    srp = get_sirope()
    ev = _cargar_eval(srp, safe)
    prompt_safe = srp.safe_from_oid(ev.prompt_oid) if ev.prompt_oid else None
    if ev.usuario_oid != current_user.oid:
        flash("No tienes permiso para borrar esta evaluación.", "error")
        if prompt_safe:
            return redirect(url_for("prompts.detalle", safe=prompt_safe))
        return redirect(url_for("prompts.lista"))

    try:
        srp.delete(ev.oid)
        flash("Evaluación eliminada.", "success")
    except Exception:
        flash("No se pudo eliminar la evaluación.", "error")

    if prompt_safe:
        return redirect(url_for("prompts.detalle", safe=prompt_safe))
    return redirect(url_for("prompts.lista"))
