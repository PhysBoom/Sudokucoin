import math
import os

from .elliptic_curve import EllipticCurvePoint
from Crypto.Hash import RIPEMD160
import hashlib
import ecdsa


def sha256(msg):
    return hashlib.sha256(msg).digest()


def ripemd160(msg):
    return RIPEMD160.new(msg).digest()


# Stolen from Karpathy's implementation cuz I'm too lazy to implement
# This myself.
def b58encode(b: bytes, alphabet: str) -> str:
    n = int.from_bytes(b, 'big')
    chars = []
    while n:
        n, i = divmod(n, 58)
        chars.append(alphabet[i])
    # special case handle the leading 0 bytes... ¯\_(ツ)_/¯
    num_leading_zeros = len(b) - len(b.lstrip(b'\x00'))
    res = num_leading_zeros * alphabet[0] + ''.join(reversed(chars))
    return res


def b58decode(s: str, alphabet: str) -> bytes:
    n = 0
    for c in s:
        n *= 58
        n += alphabet.index(c)
    b = n.to_bytes(math.ceil(n.bit_length() / 8), 'big')
    return b


class Address:
    """
    The sudokucoin address

    Attributes:
        <int> private_key: Private key of the address

    Methods:
        <EllipticCurvePoint> to_public_key: Get the public key given the private key
        <str> to_address: Gets the Base58 address using Base58Check Encode
    """
    GENERATOR = EllipticCurvePoint(
        0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
        0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
    )

    ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def __init__(self, private_key: int):
        self.private_key = private_key

    def to_public_key(self) -> EllipticCurvePoint:
        return self.GENERATOR * self.private_key

    def to_address(self) -> str:
        # Note: Sudokucoin uses the \x02\xe4 prefix unlike Bitcoin's \x00 (see what addresses this generates)
        # (ok, well half the time it does indeed generate 68 as the first 2 characters. But the other half of
        # the time it is nice)
        # Conversion is defined as Base58CheckEncode(ripemd(sha256(pubkey)))
        k = self.to_public_key().encode()
        address = ripemd160(sha256(k))
        checksum = sha256(sha256(b'\x69' + address))[:4]
        new_payload = b'\x02\xe4' + address + checksum
        return b58encode(new_payload, self.ALPHABET)

    def sign(self, msg: bytes) -> bytes:
        """
        Sign the message with the private key
        """
        private_key = ecdsa.SigningKey.from_secret_exponent(self.private_key, curve=ecdsa.SECP256k1)
        return private_key.sign(msg)

    @classmethod
    def create(cls, private_key: int = None) -> 'Address':
        """
        Create a new address
        """
        if private_key is None:
            private_key = int.from_bytes(os.urandom(32), 'big')
        return cls(private_key)

    @staticmethod
    def verify(msg: bytes, signature: bytes, public_key: EllipticCurvePoint) -> bool:
        """
        Verify the signature of the message with the public key
        """
        try:
            public_key = ecdsa.VerifyingKey.from_string(public_key.encode(), curve=ecdsa.SECP256k1)
            return public_key.verify(signature, msg)
        except ecdsa.BadSignatureError:
            return False
