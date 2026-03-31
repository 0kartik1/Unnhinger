from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from models.person import Person
from models.connection import Connection
from discovery import run_discovery, osint_providers_available, build_osint_providers
from discovery.local_provider import LocalProvider

connections_bp = Blueprint("connections", __name__, url_prefix="/connections")


def _flash_discovery_summary(summary: dict) -> None:
    checked = summary["pairs_checked"]
    skipped = summary["pairs_skipped_stale"]
    found = summary["connections_found"]

    if found > 0:
        flash(
            f"Discovery complete — {checked} pair(s) checked, "
            f"{skipped} skipped (recent), {found} link(s) found.",
            "success",
        )
    else:
        flash(
            f"Discovery complete — {checked} pair(s) checked, no new links found.",
            "info",
        )
    for name_a, name_b, provider, msg in summary["errors"]:
        flash(f"Provider error [{provider}] on {name_a} ↔ {name_b}: {msg}", "warning")


def _build_people_cache(connections: list) -> dict:
    cache = {}
    for conn in connections:
        for field in ("person_a_id", "person_b_id"):
            pid = str(conn[field])
            if pid not in cache:
                doc = Person.find_by_id(pid)
                if doc:
                    cache[pid] = doc.get("name", f"[{pid[:8]}...]")
    return cache


@connections_bp.route("/<id>", methods=["GET"])
def list_connections(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    connections = Connection.find_for_person(id)
    people_cache = _build_people_cache(connections)

    return render_template(
        "connections/index.html",
        person=person,
        connections=connections,
        people_cache=people_cache,
        all_people=Person.find_all(),
        active_person_id=str(person["_id"]),
        osint_available=osint_providers_available(),
    )


@connections_bp.route("/between/<id_a>/<id_b>", methods=["GET"])
def show_connection(id_a, id_b):
    person_a = Person.find_by_id(id_a)
    person_b = Person.find_by_id(id_b)
    if not person_a or not person_b:
        abort(404)

    connection = Connection.find_between(id_a, id_b)

    return render_template(
        "connections/detail.html",
        person_a=person_a,
        person_b=person_b,
        connection=connection,
        all_people=Person.find_all(),
        active_person_id=id_a,
    )


@connections_bp.route("/run/<id>", methods=["POST"])
def run_for_person(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    use_osint = request.form.get("use_osint") == "1"

    # Always run local discovery first (fast, free)
    summary = run_discovery(
        new_person_id=id,
        providers=[LocalProvider()],
        staleness_days=0,
        quiet=True,
    )

    # Optionally run OSINT providers
    if use_osint and osint_providers_available():
        osint_summary = run_discovery(
            new_person_id=id,
            providers=build_osint_providers(),
            staleness_days=0,
            quiet=True,
        )
        # Merge summaries
        summary["pairs_checked"] += osint_summary["pairs_checked"]
        summary["connections_found"] += osint_summary["connections_found"]
        summary["errors"].extend(osint_summary["errors"])

    _flash_discovery_summary(summary)
    return redirect(url_for("connections.list_connections", id=id))


@connections_bp.route("/run-all", methods=["POST"])
def run_all():
    use_osint = request.form.get("use_osint") == "1"

    providers = [LocalProvider()]
    if use_osint and osint_providers_available():
        providers.extend(build_osint_providers())

    summary = run_discovery(providers=providers, quiet=True)
    _flash_discovery_summary(summary)
    return redirect(url_for("people.list_people"))
