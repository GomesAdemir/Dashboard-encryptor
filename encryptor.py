#!/usr/bin/env python3
import argparse, base64, os, sys
from pathlib import Path

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives import hashes
except ImportError:
    sys.exit(
        "Instale a dependência dentro de um venv:\n"
        "  python3 -m venv .venv && source .venv/bin/activate && pip install cryptography"
    )

USERNAME   = "ademir"
PASSWORD   = "ademir"
ITERATIONS = 600_000

FILE_IMPUT = "dashboard_olimpiadas.html"
FILE_OUTPUT = "dashboard_olimpiadas_encrypted.html"

def derive_key(username, password, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITERATIONS)
    return kdf.derive(f"{username}:{password}".encode())

def main():
    ap = argparse.ArgumentParser(description="Seal an HTML file with AES-256-GCM.")
    ap.add_argument("input",            nargs="?", default=FILE_IMPUT,        help="plaintext HTML")
    ap.add_argument("-t", "--template", default="envelope_template.html",      help="login template")
    ap.add_argument("-o", "--output",   default=None,                           help=f"encrypted output (default: {FILE_OUTPUT})")
    args = ap.parse_args()

    src = Path(args.input)
    tpl = Path(args.template)
    dst = Path(args.output) if args.output else Path(FILE_OUTPUT)

    if not src.is_file():
        sys.exit(f"Input not found: {src}")
    if not tpl.is_file():
        sys.exit(f"Template not found: {tpl}")

    template = tpl.read_text(encoding="utf-8")
    for marker in ("__SALT__", "__IV__", "__PAYLOAD__", "__ITERATIONS__"):
        if marker not in template:
            sys.exit(f"Template is missing marker: {marker}")

    salt = os.urandom(16)
    iv   = os.urandom(12)
    key  = derive_key(USERNAME, PASSWORD, salt)
    ct   = AESGCM(key).encrypt(iv, src.read_bytes(), None)
    b64  = lambda b: base64.b64encode(b).decode()

    sealed = (template
              .replace("__SALT__",       b64(salt))
              .replace("__IV__",         b64(iv))
              .replace("__PAYLOAD__",    b64(ct))
              .replace("__ITERATIONS__", str(ITERATIONS)))

    dst.write_text(sealed, encoding="utf-8")
    print(f"Sealed: {src} ({src.stat().st_size:,} B)  →  {dst} ({dst.stat().st_size:,} B)")
    print(f"Cipher: AES-256-GCM  |  KDF: PBKDF2-SHA256 / {ITERATIONS:,} iterations")

if __name__ == "__main__":
    main()
