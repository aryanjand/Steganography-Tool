from .constants import DEFAULT_DECODE_OUTPUT, HEADER_LEN
from .crypto import decrypt_aes_gcm, encrypt_aes_gcm
from .envelope import build_payload_envelope, parse_header, parse_payload_fields
from .errors import FileWriteError, StegError
from .lsb import (
    capacity_bytes,
    embed_lsb_rgb_msb_first,
    extract_header_lsb_rgb_msb_first,
    extract_lsb_rgb_msb_first,
    load_png,
    save_png,
)


def read_message_file(path: str) -> bytes:
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as exc:
        raise StegError(f"Message read failure: cannot read '{path}'.") from exc

    if not data:
        raise StegError("Message read failure: message file is empty.")
    return data


def write_output_file(path: str, data: bytes) -> None:
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError as exc:
        raise FileWriteError(f"File write failure: cannot write output file '{path}'.") from exc


def run_encode(input_png: str, message_file: str, key: str, output_png: str) -> None:
    source = load_png(input_png)
    plaintext = read_message_file(message_file)

    nonce, ciphertext = encrypt_aes_gcm(plaintext, key)
    payload = build_payload_envelope(nonce, ciphertext)

    if len(payload) > capacity_bytes(source.image):
        raise StegError(
            f"Insufficient capacity: need {len(payload)} bytes, have {capacity_bytes(source.image)} bytes."
        )

    stego = embed_lsb_rgb_msb_first(source.image, payload)
    save_png(stego, output_png, source.save_kwargs)


def run_decode(input_png: str, key: str, output_file: str = DEFAULT_DECODE_OUTPUT) -> None:
    source = load_png(input_png)

    header = extract_header_lsb_rgb_msb_first(source.image)
    payload_len = parse_header(header)
    total_len = HEADER_LEN + payload_len

    if total_len > capacity_bytes(source.image):
        raise StegError("Invalid header: embedded length exceeds image capacity.")

    full = extract_lsb_rgb_msb_first(source.image, total_len)
    body = full[HEADER_LEN:]

    nonce, ciphertext = parse_payload_fields(body)
    plaintext = decrypt_aes_gcm(nonce, ciphertext, key)
    write_output_file(output_file, plaintext)

