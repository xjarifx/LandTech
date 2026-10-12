"""Demo Ed25519 signing. The generated private key is never committed."""

import base64
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, PrivateFormat, NoEncryption


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def generate_key() -> tuple[Ed25519PrivateKey, bytes]:
    private = Ed25519PrivateKey.generate()
    return private, private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def load_or_generate_key() -> tuple[Ed25519PrivateKey, bytes]:
    """Keep the demo key outside the repository so seed and server agree."""
    path = Path.home() / ".daffodil-deedguard-demo.key"
    if path.exists():
        private = Ed25519PrivateKey.from_private_bytes(path.read_bytes())
    else:
        private = Ed25519PrivateKey.generate()
        path.write_bytes(private.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()))
    return private, private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)


def sign(private: Ed25519PrivateKey, deed_hash: str) -> str:
    return base64.b64encode(private.sign(deed_hash.encode())).decode()


def verify(public: bytes, deed_hash: str, signature: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(public).verify(
            base64.b64decode(signature), deed_hash.encode())
        return True
    except (ValueError, TypeError):
        return False
