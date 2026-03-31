from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from db import get_connections_collection


class Connection:

    @staticmethod
    def _col():
        return get_connections_collection()

    @staticmethod
    def _now():
        return datetime.now(timezone.utc)

    @staticmethod
    def _canonical_pair(id_a: str, id_b: str) -> tuple[str, str]:
        return (id_a, id_b) if id_a < id_b else (id_b, id_a)

    # ── Upsert ────────────────────────────────────────────────────────────────

    @staticmethod
    def upsert(id_a: str, id_b: str, new_links: list, provider: str) -> str:
        small, large = Connection._canonical_pair(id_a, id_b)
        oid_a, oid_b = ObjectId(small), ObjectId(large)

        existing = Connection._col().find_one({"person_a_id": oid_a, "person_b_id": oid_b})
        existing_keys = set()
        if existing:
            for lnk in existing.get("links", []):
                existing_keys.add((lnk.get("type"), lnk.get("value"), lnk.get("provider")))

        deduped = [
            lnk for lnk in new_links
            if (lnk.get("type"), lnk.get("value"), lnk.get("provider")) not in existing_keys
        ]

        now = Connection._now()
        update = {
            "$set": {"last_checked": now},
            "$setOnInsert": {"discovered_at": now},
            "$addToSet": {"providers_run": provider},
        }
        if deduped:
            update["$push"] = {"links": {"$each": deduped}}

        result = Connection._col().update_one(
            {"person_a_id": oid_a, "person_b_id": oid_b},
            update,
            upsert=True,
        )
        if result.upserted_id:
            return str(result.upserted_id)
        doc = Connection._col().find_one(
            {"person_a_id": oid_a, "person_b_id": oid_b}, {"_id": 1}
        )
        return str(doc["_id"])

    # ── Read ──────────────────────────────────────────────────────────────────

    @staticmethod
    def find_for_person(id_str: str) -> list:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return []
        return list(
            Connection._col().find({"$or": [{"person_a_id": oid}, {"person_b_id": oid}]})
        )

    @staticmethod
    def find_between(id_a: str, id_b: str) -> dict | None:
        try:
            small, large = Connection._canonical_pair(id_a, id_b)
            oid_a, oid_b = ObjectId(small), ObjectId(large)
        except InvalidId:
            return None
        return Connection._col().find_one({"person_a_id": oid_a, "person_b_id": oid_b})

    @staticmethod
    def get_last_checked(id_a: str, id_b: str) -> datetime | None:
        doc = Connection.find_between(id_a, id_b)
        return doc.get("last_checked") if doc else None

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_for_person(id_str: str) -> int:
        try:
            oid = ObjectId(id_str)
        except InvalidId:
            return 0
        result = Connection._col().delete_many(
            {"$or": [{"person_a_id": oid}, {"person_b_id": oid}]}
        )
        return result.deleted_count
