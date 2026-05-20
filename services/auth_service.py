"""
TRS Auth Service — Security Hardened
- bcrypt password hashing (مع SHA256 fallback للـ migration)
- Secure session management مع sliding expiry
- Rate limiting على الـ login
- CSRF token generation
"""

import hashlib
import hmac
import secrets
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ── bcrypt (optional, graceful fallback) ─────────────────────────────────
try:
    import bcrypt
    BCRYPT_OK = True
except ImportError:
    BCRYPT_OK = False
    logger.warning("bcrypt not installed — using SHA256+salt. Run: pip install bcrypt")


class AuthService:

    # ── Password hashing ──────────────────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """bcrypt لو متاح، SHA256+salt لو لأ"""
        if BCRYPT_OK:
            return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
        # SHA256 + random salt (أحسن من SHA256 بس)
        salt = secrets.token_hex(16)
        h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
        return f"pbkdf2:{salt}:{h.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """يدعم bcrypt + pbkdf2 + sha256 القديم (للـ migration)"""
        if not password or not password_hash:
            return False
        try:
            # bcrypt
            if BCRYPT_OK and password_hash.startswith("$2"):
                return bcrypt.checkpw(password.encode(), password_hash.encode())
            # pbkdf2 (جديد بدون bcrypt)
            if password_hash.startswith("pbkdf2:"):
                _, salt, stored = password_hash.split(":", 2)
                h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 200_000)
                return hmac.compare_digest(h.hex(), stored)
            # SHA256 قديم — بدون salt (legacy migration)
            old_hash = hashlib.sha256(password.encode()).hexdigest()
            return hmac.compare_digest(old_hash, password_hash)
        except Exception:
            return False

    @staticmethod
    def needs_rehash(password_hash: str) -> bool:
        """هل الـ hash قديم ومحتاج يتحدث؟"""
        return not (password_hash.startswith("$2") or password_hash.startswith("pbkdf2:"))

    @staticmethod
    def issue_session_token() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def generate_csrf_token() -> str:
        return secrets.token_hex(24)


# ── Rate Limiter ──────────────────────────────────────────────────────────

class LoginRateLimiter:
    """
    Simple in-memory rate limiter
    Max 5 attempts per IP per 5 minutes
    """
    def __init__(self, max_attempts: int = 5, window_sec: int = 300):
        self._attempts: dict[str, list[float]] = {}
        self.max_attempts = max_attempts
        self.window_sec   = window_sec

    def is_blocked(self, ip: str) -> tuple[bool, int]:
        """Returns (blocked, seconds_remaining)"""
        now = time.time()
        attempts = self._attempts.get(ip, [])
        # Remove old attempts outside window
        attempts = [t for t in attempts if now - t < self.window_sec]
        self._attempts[ip] = attempts
        if len(attempts) >= self.max_attempts:
            oldest = min(attempts)
            wait = int(self.window_sec - (now - oldest))
            return True, max(0, wait)
        return False, 0

    def record_attempt(self, ip: str):
        now = time.time()
        if ip not in self._attempts:
            self._attempts[ip] = []
        self._attempts[ip].append(now)

    def clear(self, ip: str):
        self._attempts.pop(ip, None)

    def cleanup(self):
        """Remove old entries (call periodically)"""
        now = time.time()
        self._attempts = {
            ip: [t for t in times if now - t < self.window_sec]
            for ip, times in self._attempts.items()
            if any(now - t < self.window_sec for t in times)
        }


# ── Session Store ─────────────────────────────────────────────────────────

class SessionStore:
    """
    In-memory session store مع:
    - Sliding expiry (تتجدد مع كل request)
    - Max sessions per user
    - Cleanup تلقائي
    """
    SESSION_TTL     = 8 * 3600   # 8 ساعات
    SLIDING_WINDOW  = 2 * 3600   # تتجدد لو في نشاط آخر ساعتين
    MAX_PER_USER    = 5          # أكتر من 5 sessions لنفس المستخدم تُلغى القديمة

    def __init__(self):
        self._sessions: dict[str, dict] = {}  # token → {user, created, last_seen}
        self._last_cleanup = time.time()

    def create(self, token: str, user: dict):
        now = time.time()
        # Remove old sessions for same user if exceeded max
        user_id = user["id"]
        user_sessions = [(t, d) for t, d in self._sessions.items()
                         if d["user"]["id"] == user_id]
        if len(user_sessions) >= self.MAX_PER_USER:
            # Remove oldest
            oldest = sorted(user_sessions, key=lambda x: x[1]["last_seen"])
            for t, _ in oldest[:len(user_sessions) - self.MAX_PER_USER + 1]:
                del self._sessions[t]

        self._sessions[token] = {
            "user":      user,
            "created":   now,
            "last_seen": now,
        }

    def get(self, token: str) -> dict | None:
        if not token:
            return None
        session = self._sessions.get(token)
        if not session:
            return None
        now = time.time()
        # Check absolute TTL
        if now - session["created"] > self.SESSION_TTL:
            del self._sessions[token]
            return None
        # Sliding window
        if now - session["last_seen"] > self.SLIDING_WINDOW:
            del self._sessions[token]
            return None
        # Update last_seen (sliding)
        session["last_seen"] = now
        # Periodic cleanup
        if now - self._last_cleanup > 3600:
            self._cleanup()
        return session["user"]

    def delete(self, token: str):
        self._sessions.pop(token, None)

    def delete_user_sessions(self, user_id: int):
        to_del = [t for t, d in self._sessions.items() if d["user"]["id"] == user_id]
        for t in to_del:
            del self._sessions[t]

    def _cleanup(self):
        now = time.time()
        expired = [t for t, d in self._sessions.items()
                   if now - d["created"] > self.SESSION_TTL
                   or now - d["last_seen"] > self.SLIDING_WINDOW]
        for t in expired:
            del self._sessions[t]
        self._last_cleanup = now
        logger.debug(f"Session cleanup: removed {len(expired)}, remaining {len(self._sessions)}")

    def active_count(self) -> int:
        return len(self._sessions)


# Singletons
login_limiter = LoginRateLimiter(max_attempts=5, window_sec=300)
session_store  = SessionStore()
