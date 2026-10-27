import time

import pytest

import authflow
from authflow import AuthService, AuthStore


@pytest.fixture(autouse=True)
def fast_kdf(monkeypatch):
    monkeypatch.setattr(authflow, "PBKDF2_ITERATIONS", 1000)


@pytest.fixture
def svc():
    return AuthService(AuthStore())


def test_register_and_login_roundtrip(svc):
    assert svc.register("alice", "correct horse") is True
    token = svc.login("alice", "correct horse")
    assert token and svc.whoami(token) == "alice"


def test_duplicate_register_rejected(svc):
    svc.register("alice", "pw1")
    assert svc.register("alice", "pw2") is False


def test_wrong_password_no_session(svc):
    svc.register("alice", "pw1")
    assert svc.login("alice", "wrong") is None


def test_unknown_user_returns_none(svc):
    assert svc.login("ghost", "pw") is None


def test_logout_invalidates_token(svc):
    svc.register("bob", "pw")
    token = svc.login("bob", "pw")
    assert svc.logout(token) is True
    assert svc.whoami(token) is None
    assert svc.logout(token) is False


def test_session_expiry(svc):
    svc.register("bob", "pw")
    now = 1_000_000.0
    token = svc.login("bob", "pw", now=now)
    assert svc.whoami(token, now=now + 10) == "bob"
    assert svc.whoami(token, now=now + authflow.SESSION_TTL_SECONDS + 1) is None


def test_lockout_after_failed_attempts(svc):
    svc.register("eve", "right")
    now = time.time()
    for _ in range(authflow.MAX_FAILED_ATTEMPTS):
        assert svc.login("eve", "bad", now=now) is None
    # locked now: even the right password fails while lock is active
    assert svc.login("eve", "right", now=now + 1) is None
    # after lockout window, correct password works again
    assert svc.login("eve", "right", now=now + authflow.LOCKOUT_SECONDS + 2) is not None


def test_change_password_invalidates_sessions(svc):
    svc.register("eve", "old")
    token = svc.login("eve", "old")
    assert svc.change_password("eve", "old", "new") is True
    assert svc.whoami(token) is None
    assert svc.login("eve", "old") is None
    assert svc.login("eve", "new") is not None


def test_change_password_wrong_old_fails(svc):
    svc.register("eve", "old")
    assert svc.change_password("eve", "nope", "new") is False
    assert svc.login("eve", "old") is not None


def test_password_stored_hashed_not_plaintext(svc):
    svc.register("alice", "s3cret!")
    rec = svc.store.users["alice"]
    assert "s3cret!" not in json_dumps(rec)
    assert len(bytes.fromhex(rec["hash"])) == 32 and len(bytes.fromhex(rec["salt"])) == 16


def test_persistence_roundtrip(tmp_path):
    store = AuthStore()
    svc = AuthService(store)
    svc.register("carol", "pw")
    path = str(tmp_path / "auth.json")
    store.save(path)
    svc2 = AuthService(AuthStore.load(path))
    token = svc2.login("carol", "pw")
    assert svc2.whoami(token) == "carol"


def test_empty_credentials_rejected(svc):
    with pytest.raises(ValueError):
        svc.register("", "pw")
    with pytest.raises(ValueError):
        svc.register("u", "")


def json_dumps(obj):
    import json
    return json.dumps(obj)
