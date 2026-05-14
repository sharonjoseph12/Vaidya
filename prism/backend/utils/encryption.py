"""
PRISM Platform — AES-256 Field-Level Encryption
Encrypts/decrypts sensitive PHI (demographics) before database storage.
"""

import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import logging

logger = logging.getLogger(__name__)


def _get_key() -> bytes:
    """Load the AES-256 encryption key from settings."""
    from backend.config import get_settings
    settings = get_settings()
    return base64.b64decode(settings.encryption_key)


def encrypt_demographics(demographics: dict) -> bytes:
    """
    Encrypt a demographics dictionary using AES-256-GCM.

    Args:
        demographics: Dict with keys like name, age, sex, location, socioeconomic_tier

    Returns:
        Encrypted bytes (nonce + ciphertext) suitable for BYTEA column storage.
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    plaintext = json.dumps(demographics, ensure_ascii=False).encode("utf-8")
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    # Prepend nonce to ciphertext for storage
    return nonce + ciphertext


def decrypt_demographics(encrypted_data: bytes) -> dict:
    """
    Decrypt demographics from AES-256-GCM encrypted bytes.

    Args:
        encrypted_data: Bytes from the encrypted_demographics column (nonce + ciphertext).

    Returns:
        Decrypted demographics dictionary.
    """
    key = _get_key()
    aesgcm = AESGCM(key)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))


def generate_encryption_key() -> str:
    """Generate a new 32-byte AES key and return as base64 string."""
    key = AESGCM.generate_key(bit_length=256)
    return base64.b64encode(key).decode("utf-8")
