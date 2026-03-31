from flask import Blueprint, redirect, url_for, flash, request, abort
from models.person import Person

social_bp = Blueprint("social", __name__, url_prefix="/people")


@social_bp.route("/<id>/social/add", methods=["POST"])
def add_social(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    platform = request.form.get("platform", "").strip().lower()
    username = request.form.get("username", "").strip()

    if not platform or not username:
        flash("Platform and username are required.", "error")
        return redirect(url_for("people.view_person", id=id))

    profile = {"platform": platform, "username": username}
    url_val = request.form.get("url", "").strip()
    profile_id = request.form.get("profile_id", "").strip()
    if url_val:
        profile["url"] = url_val
    if profile_id:
        profile["profile_id"] = profile_id

    ok = Person.add_social_profile(id, profile)
    if ok:
        flash(f"[{platform}] @{username} added.", "success")
    else:
        flash("Failed to add social profile.", "error")

    return redirect(url_for("people.view_person", id=id))


@social_bp.route("/<id>/social/remove", methods=["POST"])
def remove_social(id):
    person = Person.find_by_id(id)
    if not person:
        abort(404)

    platform = request.form.get("platform", "").strip()
    username = request.form.get("username", "").strip()

    if not platform or not username:
        flash("Invalid request.", "error")
        return redirect(url_for("people.view_person", id=id))

    ok = Person.remove_social_profile(id, platform, username)
    if ok:
        flash(f"@{username} removed.", "success")
    else:
        flash("Remove failed.", "error")

    return redirect(url_for("people.view_person", id=id))
