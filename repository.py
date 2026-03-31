"""
repository.py — Data access facade for the people-db project.

Provides a flat function API over the Person and Connection model classes.
Used by discovery/runner.py so that the discovery package has a single,
stable import point that is independent of the internal model structure.
"""

from models.person import Person
from models.connection import Connection

# ── People ────────────────────────────────────────────────────────────────────

def add_person(data: dict) -> str:
    return Person.add(data)

def find_all() -> list:
    return Person.find_all()

def find_by_id(id_str: str) -> dict | None:
    return Person.find_by_id(id_str)

def find_by_name(name: str) -> list:
    return Person.find_by_name(name)

def search(field: str, value: str) -> list:
    return Person.search(field, value)

def resolve(id_or_name: str) -> list:
    return Person.resolve(id_or_name)

def update_person(id_str: str, updates: dict) -> bool:
    return Person.update(id_str, updates)

def delete_person(id_str: str) -> bool:
    return Person.delete(id_str)

# ── Social Profiles ───────────────────────────────────────────────────────────

def add_social_profile(id_str: str, profile: dict) -> bool:
    return Person.add_social_profile(id_str, profile)

def remove_social_profile(id_str: str, platform: str, username: str) -> bool:
    return Person.remove_social_profile(id_str, platform, username)

def get_social_profiles(id_str: str) -> list:
    return Person.get_social_profiles(id_str)

# ── Connections ───────────────────────────────────────────────────────────────

def upsert_connection(id_a: str, id_b: str, new_links: list, provider: str) -> str:
    return Connection.upsert(id_a, id_b, new_links, provider)

def find_connections_for_person(id_str: str) -> list:
    return Connection.find_for_person(id_str)

def find_connection_between(id_a: str, id_b: str) -> dict | None:
    return Connection.find_between(id_a, id_b)

def get_last_checked(id_a: str, id_b: str):
    return Connection.get_last_checked(id_a, id_b)

def delete_connections_for_person(id_str: str) -> int:
    return Connection.delete_for_person(id_str)
