import bcrypt
import hashlib
import secrets
from flask import request
from shared.mongodb import MongoDB

db = MongoDB()


def create_secret(n):
    """Create a cryptographically secure random string."""
    return secrets.token_urlsafe(n)[:n]


def get_request_token():
    """Get token for current flask request context."""
    _, access_token = request.headers["Authorization"].split()
    token = db.getOne("tokens", {"access_token": access_token})
    return token


def old_sha1_check(password, old_hash):
    """Verify an old password using bcrypt."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), old_hash.encode('utf-8'))
    except ValueError:
        return False


def encrypt_pw(password):
    """Hash a password securely with bcrypt."""
    salt = bcrypt.gensalt()  # Generates a new random salt
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
