from .constants import (
    CIPHERTEXT_LEN_LEN,
    HEADER_LEN,
    MAGIC,
    NONCE_LEN,
    TOTAL_LEN_LEN,
    VERSION,
)
from .errors import StegError


def build_payload_envelope(nonce: bytes, ciphertext: bytes) -> bytes:
    if len(nonce) != NONCE_LEN:
        raise StegError("Payload build failure: nonce length mismatch.")

    body = nonce + len(ciphertext).to_bytes(CIPHERTEXT_LEN_LEN, "big") + ciphertext
    if len(body) > (2**32 - 1):
        raise StegError("Payload build failure: payload too large.")
    return MAGIC + bytes([VERSION]) + len(body).to_bytes(TOTAL_LEN_LEN, "big") + body


def parse_header(header: bytes) -> int:
    if len(header) != HEADER_LEN:
        raise StegError("Header read failure.")

    magic = header[0:4]
    version = header[4]
    payload_len = int.from_bytes(header[5:9], "big")

    if magic != MAGIC or version != VERSION:
        raise StegError("Invalid header: bad magic or unsupported version.")
    return payload_len


def parse_payload_fields(payload_body: bytes) -> tuple[bytes, bytes]:
    min_len = NONCE_LEN + CIPHERTEXT_LEN_LEN
    if len(payload_body) < min_len:
        raise StegError("Malformed payload: too short.")

    nonce = payload_body[:NONCE_LEN]
    ciphertext_len = int.from_bytes(
        payload_body[NONCE_LEN : NONCE_LEN + CIPHERTEXT_LEN_LEN], "big"
    )
    ciphertext = payload_body[NONCE_LEN + CIPHERTEXT_LEN_LEN :]

    if ciphertext_len != len(ciphertext):
        raise StegError("Malformed payload: ciphertext length mismatch.")
    return nonce, ciphertext

