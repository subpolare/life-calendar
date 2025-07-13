import os, base64
from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
load_dotenv()

MASTER_KEY = base64.urlsafe_b64decode(os.getenv('ENCRYPTION_KEY'))

def generate_user_key() -> bytes:
    return AESGCM.generate_key(bit_length = 256)

def encrypt_key(user_key: bytes) -> dict:
    aes = AESGCM(MASTER_KEY)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, user_key, None)
    return {'nonce': base64.b64encode(nonce).decode(), 'encrypted_payload': base64.b64encode(ct).decode()}

def decrypt_key(key_record: dict) -> bytes:
    aes = AESGCM(MASTER_KEY)
    nonce = base64.b64decode(key_record['nonce'])
    ct = base64.b64decode(key_record['encrypted_payload'])
    return aes.decrypt(nonce, ct, None)

def encrypt(plaintext: bytes, user_key: bytes) -> dict:
    aes = AESGCM(user_key)
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext, None)
    return {'nonce': base64.b64encode(nonce).decode(), 'encrypted_payload': base64.b64encode(ct).decode()}

def decrypt(record: dict, user_key: bytes) -> bytes:
    aes = AESGCM(user_key)
    nonce = base64.b64decode(record['nonce'])
    ct = base64.b64decode(record['encrypted_payload'])
    return aes.decrypt(nonce, ct, None)
