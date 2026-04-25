from __future__ import annotations

from hashlib import sha256


PASSWORD_SALT = "pulsedesk-demo::v1"


def hash_password(password: str) -> str:
    return sha256(f"{PASSWORD_SALT}:{password}".encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def build_access_token(user_id: int, email: str) -> str:
    slug = email.split("@", maxsplit=1)[0].replace(".", "-")
    return f"demo-{user_id}-{slug}"
