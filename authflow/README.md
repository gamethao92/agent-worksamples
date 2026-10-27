# authflow — password login + tests (stdlib only)

Secure password login module: PBKDF2-HMAC-SHA256 (600k iters, per-user salt),
constant-time verification, timing-equalized user lookup (dummy hash for
unknown users), hashed bearer session tokens with expiry, logout, failed-login
lockout, password change with session invalidation, atomic JSON persistence.

API: `AuthService.register / login / logout / whoami / change_password`.

Run tests: `pytest tests -q` (12 tests). No third-party dependencies.
