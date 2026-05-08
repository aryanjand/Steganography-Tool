# Steganography-Tool

Deterministic steganography CLI with AES-256-GCM encryption and LSB embedding for PNG images.

## Commands

Encode:

```bash
./steg-encode -i <input.png> -m <message_file> -k <key> -o <output.png>
```

Decode:

```bash
./steg-decode -i <stego.png> -k <key> [-o <output_file>]
```

Default decode output: `decoded_output.bin`

## Payload Envelope

Binary layout:

- `4 bytes`: magic (`"STEG"`)
- `1 byte`: version (`1`)
- `4 bytes`: total embedded payload length (`uint32`, big-endian) for all bytes after magic+version
- `12 bytes`: AES-GCM nonce
- `4 bytes`: ciphertext length (`uint32`, big-endian)
- `N bytes`: ciphertext+tag (from AES-GCM)

## Implementation Rules

- Pixel traversal: row-major, left-to-right, top-to-bottom
- Channels used: RGB only
- RGBA alpha channel is never modified
- 1 LSB per RGB channel
- Bit order: MSB-first during embed and extract

## Encryption Contract

- Algorithm: AES-256-GCM
- Key derivation: `SHA-256(passphrase UTF-8 bytes)` -> 32-byte key
- Nonce: 12 random bytes generated during encode
- Wrong key/corrupted payload: decryption fails and decode exits non-zero

## Exit Codes

- `0`: success
- `1`: invalid args or processing failure
- `2`: file write failure

## Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
