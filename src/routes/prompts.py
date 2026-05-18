"""Rutas relativas a Prompts: listado, creación, edición y borrado."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from sirope_config import get_sirope, oid_from_safe, safe_oid
from models.prompt import (
    Prompt, cargar_prompt, borrar_prompt_en_cascada, buscar_prompts,
)
from models.categoria import Categoria
from models.usuario import Usuario
from models.evaluacion import evaluaciones_de_prompt
from models.comentario import comentarios_de_prompt

bp = Blueprint("prompts", __name__, url_prefix="/prompts")


def _safe(srp, obj):
    """Atajo para obtener el OID seguro de un objeto.

    :param srp: Instancia de Sirope.
    :param obj: Objeto persistido.
    :return: Cadena segura del OID.
    """
    return safe_oid(srp, obj)


def _cargar_o_404(srp, safe):
    """Carga un Prompt desde un OID seguro o aborta con 404.

    :param srp: Instancia de Sirope.
    :param safe: OID seguro.
    :return: Prompt encontrado.
    """
    oid = oid_from_safe(srp, safe)
    prompt = cargar_prompt(srp, oid)
    if not prompt:
        abort(404)
    return prompt


@bp.route("/")
def lista():
    """Lista de prompts con buscador opcional.

    :return: Render de la lista de prompts.
    """
    srp = get_sirope()
    termino = request.args.get("q", "").strip()
    prompts = buscar_prompts(srp, termino if termino else None)

    categorias_map = {}
    autores_map = {}
    try:
        for c in srp.load_all(Categoria):
            categorias_map[srp.safe_from_oid(c.oid)] = c
        for u in srp.load_all(Usuario):
            autores_map[srp.safe_from_oid(u.oid)] = u
    except Exception:
        pass

    items = []
    for p in prompts:
        cat = categorias_map.get(srp.safe_from_oid(p.categoria_oid)) if p.categoria_oid else None
        autor = autores_map.get(srp.safe_from_oid(p.usuario_oid)) if p.usuario_oid else None
        items.append({
            "prompt": p,
            "safe": _safe(srp, p),
            "categoria": cat,
            "autor": autor,
        })
    return render_template("prompts/lista.html", items=items, termino=termino,
                           titulo="Explorar prompts", solo_mios=False)


@bp.route("/mis-prompts")
@login_required
def mis_prompts():
    """Lista los prompts creados por el usuario actual.

    :return: Render de la lista de prompts del usuario.
    """
    srp = get_sirope()
    try:
        prompts = list(srp.filter(Prompt, lambda p: p.usuario_oid == current_user.oid))
    except Exception:
        prompts = []
    prompts.sort(key=lambda p: p.fecha_creacion, reverse=True)

    categorias_map = {}
    try:
        for c in srp.load_all(Categoria):
            categorias_map[srp.safe_from_oid(c.oid)] = c
    except Exception:
        pass

    items = []
    for p in prompts:
        cat = categorias_map.get(srp.safe_from_oid(p.categoria_oid)) if p.categoria_oid else None
        items.append({
            "prompt": p,
            "safe": _safe(srp, p),
            "categoria": cat,
            "autor": current_user,
        })
    return render_template("prompts/lista.html", items=items, termino="",
                           titulo="Mis prompts", solo_mios=True)


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
def nuevo():
    """Crea un Prompt nuevo asociado al usuario actual.

    :return: Render del formulario o redirección al detalle.
    """
    srp = get_sirope()
    try:
        categorias = list(srp.load_all(Categoria))
    except Exception:
        categorias = []
    categorias_lst = [(srp.safe_from_oid(c.oid), c) for c in categorias]

    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        contenido = (request.form.get("contenido") or "").strip()
        categoria_safe = request.form.get("categoria_oid") or ""
        tags_raw = request.form.get("tags") or ""

        if not titulo or not contenido:
            flash("Título y contenido son obligatorios.", "error")
            return render_template("prompts/form.html",
                                   categorias=categorias_lst,
                                   prompt=None,
                                   form={"titulo": titulo, "contenido": contenido,
                                         "categoria_oid": categoria_safe,
                                         "tags": tags_raw})

        categoria_oid = oid_from_safe(srp, categoria_safe) if categoria_safe else None
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
        try:
            p = Prompt(titulo=titulo, contenido=contenido,
                       categoria_oid=categoria_oid,
                       usuario_oid=current_user.oid, tags=tags)
            srp.save(p)
        except Exception:
            flash("No se pudo guardar el prompt.", "error")
            return redirect(url_for("prompts.lista"))

        flash("Prompt creado correctamente.", "success")
        return redirect(url_for("prompts.detalle", safe=_safe(srp, p)))

    return render_template("prompts/form.html", categorias=categorias_lst,
                           prompt=None, form={})


@bp.route("/<safe>")
def detalle(safe):
    """Muestra el detalle completo de un Prompt.

    :param safe: OID seguro del Prompt.
    :return: Render de la vista de detalle.
    """
    srp = get_sirope()
    prompt = _cargar_o_404(srp, safe)

    autor = None
    if prompt.usuario_oid:
        try:
            autor = srp.load(prompt.usuario_oid)
        except Exception:
            autor = None

    categoria = None
    if prompt.categoria_oid:
        try:
            categoria = srp.load(prompt.categoria_oid)
        except Exception:
            categoria = None

    evaluaciones = evaluaciones_de_prompt(srp, prompt.oid)
    comentarios = comentarios_de_prompt(srp, prompt.oid)

    eval_items = []
    for ev in evaluaciones:
        ev_autor = None
        if ev.usuario_oid:
            try:
                ev_autor = srp.load(ev.usuario_oid)
            except Exception:
                ev_autor = None
        eval_items.append({
            "ev": ev,
            "safe": srp.safe_from_oid(ev.oid),
            "autor": ev_autor,
            "es_mia": (current_user.is_authenticated
                       and ev.usuario_oid == current_user.oid),
        })

    com_items = []
    for com in comentarios:
        com_autor = None
        if com.usuario_oid:
            try:
                com_autor = srp.load(com.usuario_oid)
            except Exception:
                com_autor = None
        puede_borrar = current_user.is_authenticated and (
            com.usuario_oid == current_user.oid
            or prompt.usuario_oid == current_user.oid
        )
        com_items.append({
            "com": com,
            "safe": srp.safe_from_oid(com.oid),
            "autor": com_autor,
            "puede_borrar": puede_borrar,
        })

    es_autor = (current_user.is_authenticated
                and prompt.usuario_oid == current_user.oid)

    return render_template("prompts/detalle.html",
                           prompt=prompt, safe=safe,
                           autor=autor, categoria=categoria,
                           evaluaciones=eval_items, comentarios=com_items,
                           es_autor=es_autor)


@bp.route("/<safe>/editar", methods=["GET", "POST"])
@login_required
def editar(safe):
    """Edita un Prompt existente. Solo el autor puede hacerlo.

    :param safe: OID seguro del Prompt.
    :return: Render del formulario o redirección al detalle.
    """
    srp = get_sirope()
    prompt = _cargar_o_404(srp, safe)
    if prompt.usuario_oid != current_user.oid:
        flash("No tienes permiso para editar este prompt.", "error")
        return redirect(url_for("prompts.detalle", safe=safe))

    try:
        categorias = list(srp.load_all(Categoria))
    except Exception:
        categorias = []
    categorias_lst = [(srp.safe_from_oid(c.oid), c) for c in categorias]
    categoria_actual_safe = (srp.safe_from_oid(prompt.categoria_oid)
                             if prompt.categoria_oid else "")

    if request.method == "POST":
        titulo = (request.form.get("titulo") or "").strip()
        contenido = (request.form.get("contenido") or "").strip()
        categoria_safe = request.form.get("categoria_oid") or ""
        tags_raw = request.form.get("tags") or ""

        if not titulo or not contenido:
            flash("Título y contenido son obligatorios.", "error")
            return render_template("prompts/form.html",
                                   categorias=categorias_lst,
                                   prompt=prompt, safe=safe,
                                   form={"titulo": titulo, "contenido": contenido,
                                         "categoria_oid": categoria_safe,
                                         "tags": tags_raw})

        try:
            prompt.titulo = titulo
            prompt.contenido = contenido
            prompt.categoria_oid = (oid_from_safe(srp, categoria_safe)
                                    if categoria_safe else None)
            prompt.tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
            srp.save(prompt)
        except Exception:
            flash("No se pudieron guardar los cambios.", "error")
            return redirect(url_for("prompts.detalle", safe=safe))

        flash("Prompt actualizado.", "success")
        return redirect(url_for("prompts.detalle", safe=safe))

    form = {
        "titulo": prompt.titulo,
        "contenido": prompt.contenido,
        "categoria_oid": categoria_actual_safe,
        "tags": ", ".join(prompt.tags or []),
    }
    return render_template("prompts/form.html",
                           categorias=categorias_lst,
                           prompt=prompt, safe=safe, form=form)


@bp.route("/<safe>/confirmar-borrar")
@login_required
def confirmar_borrar(safe):
    """Pantalla de confirmación previa al borrado de un prompt.

    :param safe: OID seguro del Prompt.
    :return: Render de la página de confirmación.
    """
    srp = get_sirope()
    prompt = _cargar_o_404(srp, safe)
    if prompt.usuario_oid != current_user.oid:
        flash("No tienes permiso para borrar este prompt.", "error")
        return redirect(url_for("prompts.detalle", safe=safe))
    return render_template("prompts/confirmar_borrar.html",
                           prompt=prompt, safe=safe)


@bp.route("/<safe>/borrar", methods=["POST"])
@login_required
def borrar(safe):
    """Elimina un Prompt y todo su contenido relacionado en cascada.

    :param safe: OID seguro del Prompt.
    :return: Redirección a la lista de prompts del usuario.
    """
    srp = get_sirope()
    prompt = _cargar_o_404(srp, safe)
    if prompt.usuario_oid != current_user.oid:
        flash("No tienes permiso para borrar este prompt.", "error")
        return redirect(url_for("prompts.detalle", safe=safe))

    if borrar_prompt_en_cascada(srp, prompt):
        flash("Prompt eliminado.", "success")
    else:
        flash("No se ha podido eliminar el prompt.", "error")
    return redirect(url_for("prompts.mis_prompts"))
