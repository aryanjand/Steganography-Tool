import hashlib
import os

from .constants import NONCE_LEN
from .errors import StegError


def _load_aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:
        raise StegError(
            "Missing dependency: cryptography. Install it with: pip install cryptography"
        ) from exc
    return AESGCM


def derive_key(key_material: str) -> bytes:
    if not key_material:
        raise StegError("Key must be non-empty.")
    return hashlib.sha256(key_material.encode("utf-8")).digest()


def encrypt_aes_gcm(plaintext: bytes, key_material: str) -> tuple[bytes, bytes]:
    key = derive_key(key_material)
    aesgcm = _load_aesgcm()(key)
    nonce = os.urandom(NONCE_LEN)
    try:
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    except Exception as exc:
        raise StegError("Encryption failure.") from exc
    return nonce, ciphertext


def decrypt_aes_gcm(nonce: bytes, ciphertext: bytes, key_material: str) -> bytes:
    key = derive_key(key_material)
    aesgcm = _load_aesgcm()(key)
    try:
        return aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise StegError("Decryption failure (wrong key or corrupted payload).") from exc

