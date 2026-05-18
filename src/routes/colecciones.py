"""Rutas para crear, editar y gestionar colecciones de prompts."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from sirope_config import get_sirope, oid_from_safe, safe_oid
from models.coleccion import Coleccion, colecciones_de_usuario, colecciones_publicas
from models.prompt import Prompt, cargar_prompt

bp = Blueprint("colecciones", __name__, url_prefix="/colecciones")


def _cargar_col(srp, safe):
    """Carga una Coleccion desde su OID seguro o aborta con 404.

    :param srp: Instancia de Sirope.
    :param safe: OID seguro.
    :return: Coleccion cargada.
    """
    oid = oid_from_safe(srp, safe)
    try:
        col = srp.load(oid) if oid else None
    except Exception:
        col = None
    if not col:
        abort(404)
    return col


@bp.route("/")
@login_required
def lista():
    """Lista las colecciones del usuario y las públicas de otros usuarios.

    :return: Render del listado de colecciones.
    """
    srp = get_sirope()
    propias = colecciones_de_usuario(srp, current_user.oid)
    publicas = colecciones_publicas(srp, excluir_usuario_oid=current_user.oid)

    propias_items = [
        {"col": c, "safe": safe_oid(srp, c), "num": len(c.prompt_oids or [])}
        for c in propias
    ]
    publicas_items = []
    for c in publicas:
        autor = None
        try:
            autor = srp.load(c.usuario_oid) if c.usuario_oid else None
        except Exception:
            autor = None
        publicas_items.append({
            "col": c, "safe": safe_oid(srp, c),
            "num": len(c.prompt_oids or []), "autor": autor,
        })

    return render_template("colecciones/lista.html",
                           propias=propias_items,
                           publicas=publicas_items)


@bp.route("/nueva", methods=["GET", "POST"])
@login_required
def nueva():
    """Crea una colección nueva para el usuario actual.

    :return: Render del formulario o redirección al detalle.
    """
    srp = get_sirope()
    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        publica = bool(request.form.get("publica"))

        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("colecciones/form.html",
                                   coleccion=None,
                                   form={"nombre": nombre,
                                         "descripcion": descripcion,
                                         "publica": publica})
        try:
            col = Coleccion(nombre=nombre, descripcion=descripcion,
                            usuario_oid=current_user.oid, publica=publica)
            srp.save(col)
        except Exception:
            flash("No se pudo crear la colección.", "error")
            return redirect(url_for("colecciones.lista"))

        flash("Colección creada.", "success")
        return redirect(url_for("colecciones.detalle", safe=safe_oid(srp, col)))

    return render_template("colecciones/form.html",
                           coleccion=None, form={})


@bp.route("/<safe>")
@login_required
def detalle(safe):
    """Muestra el detalle de una colección con sus prompts.

    :param safe: OID seguro de la Coleccion.
    :return: Render del detalle.
    """
    srp = get_sirope()
    col = _cargar_col(srp, safe)
    es_owner = col.usuario_oid == current_user.oid
    if not es_owner and not col.publica:
        flash("No tienes acceso a esta colección.", "error")
        return redirect(url_for("colecciones.lista"))

    prompts_items = []
    for poid in (col.prompt_oids or []):
        p = cargar_prompt(srp, poid)
        if not p:
            continue
        prompts_items.append({
            "prompt": p,
            "safe": srp.safe_from_oid(p.oid),
        })

    candidatos = []
    if es_owner:
        try:
            todos = list(srp.load_all(Prompt))
        except Exception:
            todos = []
        existentes = set()
        for poid in (col.prompt_oids or []):
            try:
                existentes.add(srp.safe_from_oid(poid))
            except Exception:
                pass
        for p in todos:
            psafe = srp.safe_from_oid(p.oid)
            if psafe not in existentes:
                candidatos.append({"prompt": p, "safe": psafe})

    autor = None
    try:
        autor = srp.load(col.usuario_oid) if col.usuario_oid else None
    except Exception:
        autor = None

    return render_template("colecciones/detalle.html",
                           col=col, safe=safe, autor=autor,
                           prompts_items=prompts_items,
                           candidatos=candidatos,
                           es_owner=es_owner)


@bp.route("/<safe>/editar", methods=["GET", "POST"])
@login_required
def editar(safe):
    """Edita los metadatos de una colección. Solo el propietario.

    :param safe: OID seguro de la Coleccion.
    :return: Render del formulario o redirección al detalle.
    """
    srp = get_sirope()
    col = _cargar_col(srp, safe)
    if col.usuario_oid != current_user.oid:
        flash("No tienes permiso para editar esta colección.", "error")
        return redirect(url_for("colecciones.detalle", safe=safe))

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        descripcion = (request.form.get("descripcion") or "").strip()
        publica = bool(request.form.get("publica"))

        if not nombre:
            flash("El nombre es obligatorio.", "error")
            return render_template("colecciones/form.html",
                                   coleccion=col, safe=safe,
                                   form={"nombre": nombre,
                                         "descripcion": descripcion,
                                         "publica": publica})
        try:
            col.nombre = nombre
            col.descripcion = descripcion
            col.publica = publica
            srp.save(col)
        except Exception:
            flash("No se pudieron guardar los cambios.", "error")
            return redirect(url_for("colecciones.detalle", safe=safe))

        flash("Colección actualizada.", "success")
        return redirect(url_for("colecciones.detalle", safe=safe))

    form = {
        "nombre": col.nombre,
        "descripcion": col.descripcion,
        "publica": col.publica,
    }
    return render_template("colecciones/form.html",
                           coleccion=col, safe=safe, form=form)


@bp.route("/<safe>/borrar", methods=["POST"])
@login_required
def borrar(safe):
    """Elimina una colección sin afectar a los prompts contenidos.

    :param safe: OID seguro de la Coleccion.
    :return: Redirección al listado de colecciones.
    """
    srp = get_sirope()
    col = _cargar_col(srp, safe)
    if col.usuario_oid != current_user.oid:
        flash("No tienes permiso para borrar esta colección.", "error")
        return redirect(url_for("colecciones.detalle", safe=safe))
    try:
        srp.delete(col.oid)
        flash("Colección eliminada.", "success")
    except Exception:
        flash("No se pudo eliminar la colección.", "error")
    return redirect(url_for("colecciones.lista"))


@bp.route("/<safe>/agregar/<prompt_safe>", methods=["POST"])
@login_required
def agregar(safe, prompt_safe):
    """Añade un prompt a una colección del usuario.

    :param safe: OID seguro de la Coleccion.
    :param prompt_safe: OID seguro del Prompt a añadir.
    :return: Redirección al detalle de la colección.
    """
    srp = get_sirope()
    col = _cargar_col(srp, safe)
    if col.usuario_oid != current_user.oid:
        flash("No tienes permiso para modificar esta colección.", "error")
        return redirect(url_for("colecciones.detalle", safe=safe))

    prompt_oid = oid_from_safe(srp, prompt_safe)
    prompt = cargar_prompt(srp, prompt_oid)
    if not prompt:
        flash("El prompt no existe.", "error")
        return redirect(url_for("colecciones.detalle", safe=safe))

    try:
        if prompt.oid not in (col.prompt_oids or []):
            col.prompt_oids = list(col.prompt_oids or []) + [prompt.oid]
            srp.save(col)
            flash("Prompt añadido a la colección.", "success")
        else:
            flash("El prompt ya estaba en la colección.", "info")
    except Exception:
        flash("No se pudo añadir el prompt.", "error")

    return redirect(url_for("colecciones.detalle", safe=safe))


@bp.route("/<safe>/quitar/<prompt_safe>", methods=["POST"])
@login_required
def quitar(safe, prompt_safe):
    """Quita un prompt de una colección del usuario.

    :param safe: OID seguro de la Coleccion.
    :param prompt_safe: OID seguro del Prompt a quitar.
    :return: Redirección al detalle de la colección.
    """
    srp = get_sirope()
    col = _cargar_col(srp, safe)
    if col.usuario_oid != current_user.oid:
        flash("No tienes permiso para modificar esta colección.", "error")
        return redirect(url_for("colecciones.detalle", safe=safe))

    prompt_oid = oid_from_safe(srp, prompt_safe)
    try:
        col.prompt_oids = [o for o in (col.prompt_oids or []) if o != prompt_oid]
        srp.save(col)
        flash("Prompt retirado de la colección.", "success")
    except Exception:
        flash("No se pudo retirar el prompt.", "error")

    return redirect(url_for("colecciones.detalle", safe=safe))
