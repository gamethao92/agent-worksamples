#!/usr/bin/env python3
"""Minimal secure password-login module (stdlib only).

Features: PBKDF2-HMAC-SHA256 hashing with per-user random salt, constant-time
verification, timing-equalized user lookup, bearer session tokens (hashed at
rest), expiry, logout, and failed-login lockout.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field

PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 16
TOKEN_BYTES = 32
SESSION_TTL_SECONDS = 24 * 3600
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_SECONDS = 15 * 60

_DUMMY_SALT = b"\x00" * SALT_BYTES
_DUMMY_HASH = hashlib.pbkdf2_hmac("sha256", b"dummy", _DUMMY_SALT, PBKDF2_ITERATIONS)


def _hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


@dataclass
class AuthStore:
    users: dict = field(default_factory=dict)          # username -> record
    sessions: dict = field(default_factory=dict)       # token_hash -> session

    def save(self, path: str) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"users": self.users, "sessions": self.sessions}, fh)
        os.replace(tmp, path)

    @classmethod
    def load(cls, path: str) -> "AuthStore":
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(users=data["users"], sessions=data["sessions"])


class AuthService:
    def __init__(self, store: AuthStore | None = None):
        self.store = store if store is not None else AuthStore()

    def register(self, username: str, password: str) -> bool:
        if not username or not password:
            raise ValueError("username and password must be non-empty")
        if username in self.store.users:
            return False
        salt = secrets.token_bytes(SALT_BYTES)
        self.store.users[username] = {
            "salt": salt.hex(),
            "hash": _hash_password(password, salt).hex(),
            "iterations": PBKDF2_ITERATIONS,
            "failed": 0,
            "locked_until": 0,
        }
        return True

    def login(self, username: str, password: str, now: float | None = None) -> str | None:
        now = time.time() if now is None else now
        user = self.store.users.get(username)
        # verify (or dummy-verify) FIRST: response time must not reveal existence
        salt = bytes.fromhex(user["salt"]) if user else _DUMMY_SALT
        expected = bytes.fromhex(user["hash"]) if user else _DUMMY_HASH
        ok = hmac.compare_digest(_hash_password(password, salt), expected)
        if not user or not ok:
            if user:
                self._register_failure(user, now)
            return None
        if now < user["locked_until"]:
            self._register_failure(user, now)
            return None
        user["failed"] = 0
        user["locked_until"] = 0
        token = secrets.token_hex(TOKEN_BYTES)
        self.store.sessions[self._token_hash(token)] = {
            "username": username,
            "expires_at": now + SESSION_TTL_SECONDS,
        }
        return token

    def logout(self, token: str) -> bool:
        return self.store.sessions.pop(self._token_hash(token), None) is not None

    def whoami(self, token: str, now: float | None = None) -> str | None:
        now = time.time() if now is None else now
        session = self.store.sessions.get(self._token_hash(token))
        if session is None or now >= session["expires_at"]:
            if session is not None:
                del self.store.sessions[self._token_hash(token)]
            return None
        return session["username"]

    def change_password(self, username: str, old: str, new: str) -> bool:
        user = self.store.users.get(username)
        if not user or not hmac.compare_digest(
            _hash_password(old, bytes.fromhex(user["salt"])), bytes.fromhex(user["hash"])
        ):
            return False
        salt = secrets.token_bytes(SALT_BYTES)
        user.update(salt=salt.hex(), hash=_hash_password(new, salt).hex())
        # invalidate all sessions of the user
        th = self._token_hash
        for h in [h for h, s in self.store.sessions.items() if s["username"] == username]:
            del self.store.sessions[h]
        return True

    @staticmethod
    def _token_hash(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def _register_failure(self, user: dict, now: float) -> None:
        user["failed"] += 1
        if user["failed"] >= MAX_FAILED_ATTEMPTS:
            user["locked_until"] = now + LOCKOUT_SECONDS
            user["failed"] = 0
