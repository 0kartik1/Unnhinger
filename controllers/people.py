from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from models.person import Person
from models.connection import Connection
from discovery import run_discovery
from discovery.local_provider import LocalProvider

people_bp = Blueprint("people", __name__, url_prefix="/people")


# ── Form parsing ──────────────────────────────────────────────────────────────

def _parse_person_form(form) -> dict:
    data = {}

    name = form.get("name", "").strip()
    if name:
        data["name"] = name

    phones = [v.strip() for v in form.getlist("phones") if v.strip()]
    if phones:
        data["phones"] = phones

    emails = [v.strip() for v in form.getlist("emails") if v.strip()]
    if emails:
        data["emails"] = emails

    # addresses: address_label_N / address_value_N
    addresses = []
    i = 0
    while f"address_value_{i}" in form:
        label = form.get(f"address_label_{i}", "").strip()
        value = form.get(f"address_value_{i}", "").strip()
        if value:
            addresses.append({"label": label, "value": value})
        i += 1
    if addresses:
        data["addresses"] = addresses

    # id_cards: id_card_type_N / id_card_number_N
    id_cards = []
    i = 0
    while f"id_card_type_{i}" in form:
        ctype = form.get(f"id_card_type_{i}", "").strip()
        number = form.get(f"id_card_number_{i}", "").strip()
        if ctype and number:
            id_cards.append({"type": ctype, "number": number})
        i += 1
    if id_cards:
        data["id_cards"] = id_cards

    notes = form.get("notes", "").strip()
    if notes:
        data["notes"] = notes

    return data


def _flash_discovery(summary: dict, person_name: str) -> None:
    checked = summary["pairs_checked"]
    skipped = summary["pairs_skipped_stale"]
    found = summary["connections_found"]
    if found > 0:
        flash(
            f"{person_name} saved. Discovery: {checked} pair(s) checked, "
            f"{skipped} skipped, {found} link(s) found.",
            "success",
        )
    else:
        flash(
            f"{person_name} saved. Discovery: {checked} pair(s) checked, no new links.",
            "success",
        )
    for _, _, provider, msg in summary["errors"]:
        flash(f"Provider error [{provider}]: {msg}", "warning")


# ── Routes ────────────────────────────────────────────────────────────────────

@people_bp.route("/", methods=["GET"])
def list_people():
    q = request.args.get("q", "").strip()
    if q:
        people = Person.find_by_name(q)
    else:
        people = Person.find_all()
    return render_template(
        "people/index.html",
        people=people,
        all_people=Person.find_all(),
        query=q,
    )


@people_bp.route("/add", methods=["GET"])
def add_person_form():
    return render_template(
        "people/form.html",
        person={},
        action="add",
        all_people=Person.find_all(),
        active_person_id=None,
    )


@people_bp.route("/add", methods=["POST"])
def add_person_submit():
    data = _parse_person_form(request.form)
    if not data.get("name"):
        flash("Name is required.", "error")
        return redirect(url_for("people.add_person_form"))

    new_id = Person.add(data)

    # Auto-run local discovery against all existing people
    all_people = Person.find_all()
    if len(all_people) > 1:
        summary = run_discovery(
            new_person_id=new_id,
            providers=[LocalProvider()],
            staleness_days=0,
            quiet=True,
        )
        _flash_discovery(summary, data["name"])
    else:
        flash(f"'{data['name']}' added successfully.", "success")

    return redirect(url_for("people.view_person", id=new_id))


@people_bp.route("/<id>", methods=["GET"])
def view_person(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    connections = Connection.find_for_person(id)

    # Build name cache for connected people
    people_cache = {}
    for conn in connections:
        for oid_field in ("person_a_id", "person_b_id"):
            pid = str(conn[oid_field])
            if pid not in people_cache:
                doc = Person.find_by_id(pid)
                if doc:
                    people_cache[pid] = doc.get("name", f"[{pid[:8]}...]")

    from discovery import osint_providers_available
    return render_template(
        "people/detail.html",
        person=person,
        connections=connections,
        people_cache=people_cache,
        all_people=Person.find_all(),
        active_person_id=str(person["_id"]),
        osint_available=osint_providers_available(),
    )


@people_bp.route("/<id>/edit", methods=["GET"])
def edit_person_form(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)
    return render_template(
        "people/form.html",
        person=person,
        action="edit",
        all_people=Person.find_all(),
        active_person_id=str(person["_id"]),
    )


@people_bp.route("/<id>/edit", methods=["POST"])
def edit_person_submit(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    data = _parse_person_form(request.form)
    if not data.get("name"):
        flash("Name is required.", "error")
        return redirect(url_for("people.edit_person_form", id=id))

    ok = Person.update(id, data)
    if ok:
        flash(f"'{data['name']}' updated.", "success")
    else:
        flash("Update failed — no changes were saved.", "error")

    return redirect(url_for("people.view_person", id=id))


@people_bp.route("/<id>/delete", methods=["GET"])
def confirm_delete(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)
    conn_count = len(Connection.find_for_person(id))
    return render_template(
        "people/confirm_delete.html",
        person=person,
        conn_count=conn_count,
        all_people=Person.find_all(),
        active_person_id=str(person["_id"]),
    )


@people_bp.route("/<id>/delete", methods=["POST"])
def delete_person_submit(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    name = person.get("name", "Unknown")
    removed = Connection.delete_for_person(id)
    Person.delete(id)

    conn_msg = f" {removed} connection record(s) also removed." if removed else ""
    flash(f"'{name}' deleted.{conn_msg}", "success")
    return redirect(url_for("people.list_people"))
