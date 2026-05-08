from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .constants import HEADER_LEN
from .errors import FileWriteError, StegError


@dataclass
class LoadedPng:
    image: Any
    save_kwargs: dict[str, Any]


def _load_pillow():
    try:
        from PIL import Image, UnidentifiedImageError
        from PIL.PngImagePlugin import PngInfo
    except ImportError as exc:
        raise StegError("Missing dependency: Pillow. Install it with: pip install pillow") from exc
    return Image, UnidentifiedImageError, PngInfo


def _build_pnginfo(image, pnginfo_cls):
    if not hasattr(image, "text"):
        return None
    if not image.text:
        return None

    pnginfo = pnginfo_cls()
    for key, value in image.text.items():
        pnginfo.add_text(str(key), str(value))
    return pnginfo


def load_png(path: str) -> LoadedPng:
    Image, UnidentifiedImageError, PngInfo = _load_pillow()
    try:
        with Image.open(path) as img:
            img.load()
            if img.format != "PNG":
                raise StegError("Invalid PNG input.")

            mode = "RGBA" if "A" in img.getbands() else "RGB"
            work = img.convert(mode)

            save_kwargs: dict[str, Any] = {}
            for field in ("icc_profile", "exif", "dpi", "transparency", "gamma"):
                if field in img.info:
                    save_kwargs[field] = img.info[field]

            pnginfo = _build_pnginfo(img, PngInfo)
            if pnginfo is not None:
                save_kwargs["pnginfo"] = pnginfo

            return LoadedPng(image=work, save_kwargs=save_kwargs)
    except FileNotFoundError as exc:
        raise StegError(f"Input image not found: {path}") from exc
    except UnidentifiedImageError as exc:
        raise StegError("Invalid PNG input.") from exc
    except OSError as exc:
        raise StegError("Invalid PNG input.") from exc


def save_png(image, output_path: str, save_kwargs: dict[str, Any]) -> None:
    try:
        image.save(output_path, format="PNG", **save_kwargs)
    except OSError as exc:
        raise FileWriteError(f"File write failure: cannot write output image '{output_path}'.") from exc


def capacity_bytes(image) -> int:
    pixel_count = image.width * image.height
    return (pixel_count * 3) // 8


def _iter_payload_bits_msb_first(payload: bytes):
    for byte in payload:
        for bit_index in range(7, -1, -1):
            yield (byte >> bit_index) & 1


def embed_lsb_rgb_msb_first(image, payload: bytes):
    required_bytes = len(payload)
    available_bytes = capacity_bytes(image)
    if required_bytes > available_bytes:
        raise StegError(
            f"Insufficient capacity: need {required_bytes} bytes, have {available_bytes} bytes."
        )

    pixels = list(image.getdata())
    bit_stream = _iter_payload_bits_msb_first(payload)
    finished = False

    for idx, pixel in enumerate(pixels):
        channels = list(pixel)
        for channel_index in range(3):
            try:
                bit = next(bit_stream)
            except StopIteration:
                finished = True
                break
            channels[channel_index] = (channels[channel_index] & 0xFE) | bit
        pixels[idx] = tuple(channels)
        if finished:
            break

    image.putdata(pixels)
    return image


def extract_lsb_rgb_msb_first(image, byte_count: int) -> bytes:
    required_bits = byte_count * 8
    if required_bits == 0:
        return b""

    available_bits = image.width * image.height * 3
    if required_bits > available_bits:
        raise StegError("Payload extract failure: requested data exceeds image capacity.")

    bits_read = 0
    current_byte = 0
    current_bits = 0
    out = bytearray()

    for pixel in image.getdata():
        for channel_index in range(3):
            bit = pixel[channel_index] & 1
            current_byte = (current_byte << 1) | bit
            current_bits += 1
            bits_read += 1

            if current_bits == 8:
                out.append(current_byte)
                current_byte = 0
                current_bits = 0

            if bits_read >= required_bits:
                return bytes(out)

    raise StegError("Payload extract failure: not enough data in image.")


def extract_header_lsb_rgb_msb_first(image) -> bytes:
    return extract_lsb_rgb_msb_first(image, HEADER_LEN)

