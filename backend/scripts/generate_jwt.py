#!/usr/bin/env python3
"""Generate a test JWT token.

This script prefers python-jose if installed, otherwise falls back to a
minimal HS256 implementation using hmac. It emits a JWT to stdout.

Usage examples:
  python scripts/generate_jwt.py --sub 27f7830e-b88b-11f0-801c-7c10c921fbde
  python scripts/generate_jwt.py --sub <UUID> --secret mysecret --exp 600

Install (recommended):
  pip install "python-jose[cryptography]"
"""
import argparse
import time
import json
import base64
import hmac
import hashlib
import sys

try:
    from jose import jwt  # type: ignore

    HAVE_JOSE = True
except Exception:
    HAVE_JOSE = False


def b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def generate_hs256(payload: dict, secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h = b64u(json.dumps(header, separators=(",", ":")).encode())
    p = b64u(json.dumps(payload, separators=(",", ":")).encode())
    msg = (h + "." + p).encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).digest()
    s = b64u(sig)
    return f"{h}.{p}.{s}"


def main() -> int:
    p = argparse.ArgumentParser(description="Generate a HS256 JWT for testing")
    p.add_argument(
        "--sub", required=True, help="Subject (sub) claim - usually the user UUID"
    )
    p.add_argument(
        "--secret", default="dev-secret", help="HMAC secret (default: dev-secret)"
    )
    p.add_argument(
        "--alg",
        default="HS256",
        help="JWT algorithm (only HS256 supported by fallback)",
    )
    p.add_argument(
        "--exp", type=int, default=3600, help="Expiry in seconds (default 3600)"
    )
    args = p.parse_args()

    now = int(time.time())
    payload = {"sub": args.sub, "iat": now, "exp": now + args.exp}

    if HAVE_JOSE:
        try:
            token = jwt.encode(payload, args.secret, algorithm=args.alg)
        except Exception as e:
            print(f"Error encoding token with python-jose: {e}", file=sys.stderr)
            return 2
    else:
        if args.alg != "HS256":
            print(
                "python-jose not available; only HS256 supported by fallback",
                file=sys.stderr,
            )
            return 3
        token = generate_hs256(payload, args.secret)

    sys.stdout.write(token + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
