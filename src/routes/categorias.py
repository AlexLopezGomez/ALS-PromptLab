"""Rutas para administrar categorías temáticas de prompts."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required

from sirope_config import get_sirope, oid_from_safe, safe_oid
from models.categoria import Categoria, desasociar_prompts_de_categoria
from models.prompt import Prompt

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


def _cargar_cat(srp, safe):
    """Carga una Categoria desde su OID seguro o aborta con 404.

    :param srp: Instancia de Sirope.
    :param safe: OID seguro.
    :return: Categoria cargada.
    """
    oid = oid_from_safe(srp, safe)
    try:
        cat = srp.load(oid) if oid else None
    except Exception:
        cat = None
    if not cat:
        abort(404)
    return cat


@bp.route("/")
def lista():
    """Muestra todas las categorías y cuántos prompts tiene cada una.

    :return: Render del listado de categorías.
    """
    srp = get_sirope()
    try:
        cats = list(srp.load_all(Categoria))
        prompts = list(srp.load_all(Prompt))
    except Exception:
        cats, prompts = [], []

    conteo = {}
    for p in prompts:
        if p.categoria_oid:
            try:
                key = srp.safe_from_oid(p.categoria_oid)
                conteo[key] = conteo.get(key, 0) + 1
            except Exception:
                pass

    items = []
    for c in cats:
        s = safe_oid(srp, c)
        items.append({"cat": c, "safe": s, "num": conteo.get(s, 0)})

    return render_template("categorias/lista.html", items=items)


@bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    """Crea una nueva categoría.

    :return: Render del formulario o redirección al listado.
    """
    srp = get_sirope()
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()

        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("categorias/form.html",
                                   categoria=None,
                                   form={"nombre": nombre,
                                         "descripcion": descripcion})
        try:
            existe = srp.find_first(Categoria,
                                    lambda c: (c.nombre or "").lower() == nombre.lower())
        except Exception:
            existe = None
        if existe:
            flash("Ya existe una categoría con ese nombre.", "error")
            return render_template("categorias/form.html",
                                   categoria=None,
                                   form={"nombre": nombre,
                                         "descripcion": descripcion})

        try:
            cat = Categoria(nombre=nombre, descripcion=descripcion)
            srp.save(cat)
        except Exception:
            flash("No se pudo crear la categoría.", "error")
            return redirect(url_for("categorias.lista"))

        flash("Categoría creada.", "success")
        return redirect(url_for("categorias.lista"))

    return render_template("categorias/form.html",
                           categoria=None, form={})


@bp.route("/<safe>/editar", methods=["GET", "POST"])
@login_required
def editar(safe):
    """Edita los datos de una categoría existente.

    :param safe: OID seguro de la Categoria.
    :return: Render del formulario o redirección al listado.
    """
    srp = get_sirope()
    cat = _cargar_cat(srp, safe)

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("categorias/form.html",
                                   categoria=cat, safe=safe,
                                   form={"nombre": nombre,
                                         "descripcion": descripcion})
        try:
            cat.nombre = nombre
            cat.descripcion = descripcion
            srp.save(cat)
        except Exception:
            flash("No se pudieron guardar los cambios.", "error")
            return redirect(url_for("categorias.lista"))

        flash("Categoría actualizada.", "success")
        return redirect(url_for("categorias.lista"))

    form = {"nombre": cat.nombre, "descripcion": cat.descripcion}
    return render_template("categorias/form.html",
                           categoria=cat, safe=safe, form=form)


@bp.route("/<safe>/borrar", methods=["POST"])
@login_required
def borrar(safe):
    """Elimina una categoría desasociándola previamente de sus prompts.

    :param safe: OID seguro de la Categoria.
    :return: Redirección al listado.
    """
    srp = get_sirope()
    cat = _cargar_cat(srp, safe)
    try:
        afectados = desasociar_prompts_de_categoria(srp, cat.oid)
        srp.delete(cat.oid)
        if afectados:
            flash(f"Categoría eliminada. {afectados} prompts quedaron sin categoría.",
                  "success")
        else:
            flash("Categoría eliminada.", "success")
    except Exception:
        flash("No se pudo eliminar la categoría.", "error")
    return redirect(url_for("categorias.lista"))
