import re
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from db import get_collection

KNOWN_FIELDS = {
    "_id", "name", "phones", "emails", "addresses",
    "id_cards", "social_profiles", "notes",
    "created_at", "updated_at",
}

PLATFORM_LABELS = {
    "facebook": "Facebook",
    "instagram": "Instagram",
    "twitter": "Twitter/X",
    "x": "Twitter/X",
    "linkedin": "LinkedIn",
}


class Person:

    @staticmethod
    def _col():
        return get_collection()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def add(data: dict) -> str:
        doc = dict(data)
        doc["created_at"] = Person._now()
        doc["updated_at"] = Person._now()
        result = Person._col().insert_one(doc)
        return str(result.inserted_id)

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def find_all() -> list:
        return list(Person._col().find().sort("name", 1))

    @staticmethod
    def find_by_id(id_str: str) -> dict | None:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return None
        return Person._col().find_one({"_id": oid})

    @staticmethod
    def find_by_name(name: str) -> list:
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        return list(Person._col().find({"name": pattern}))

    @staticmethod
    def search(field: str, value: str) -> list:
        pattern = re.compile(re.escape(value), re.IGNORECASE)
        return list(Person._col().find({field: pattern}))

    @staticmethod
    def resolve(id_or_name: str) -> list:
        doc = Person.find_by_id(id_or_name)
        if doc:
            return [doc]
        return Person.find_by_name(id_or_name)

    # ── Update ────────────────────────────────────────────────────────────────

    @staticmethod
    def update(id_str: str, updates: dict) -> bool:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return False
        updates["updated_at"] = Person._now()
        result = Person._col().update_one({"_id": oid}, {"$set": updates})
        return result.modified_count > 0

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete(id_str: str) -> bool:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return False
        result = Person._col().delete_one({"_id": oid})
        return result.deleted_count > 0

    # ── Social Profiles ───────────────────────────────────────────────────────

    @staticmethod
    def add_social_profile(id_str: str, profile: dict) -> bool:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return False
        result = Person._col().update_one(
            {"_id": oid},
            {
                "$push": {"social_profiles": profile},
                "$set": {"updated_at": Person._now()},
            },
        )
        return result.modified_count > 0

    @staticmethod
    def remove_social_profile(id_str: str, platform: str, username: str) -> bool:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return False
        result = Person._col().update_one(
            {"_id": oid},
            {
                "$pull": {"social_profiles": {"platform": platform, "username": username}},
                "$set": {"updated_at": Person._now()},
            },
        )
        return result.modified_count > 0

    @staticmethod
    def get_social_profiles(id_str: str) -> list:
        doc = Person.find_by_id(id_str)
        return (doc or {}).get("social_profiles", [])
