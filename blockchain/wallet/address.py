import os
from .elliptic_curve import EllipticCurvePoint
import ecdsa


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
        0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8,
    )

    def __init__(self, private_key: int):
        self.private_key = private_key

    def to_public_key(self) -> EllipticCurvePoint:
        return self.GENERATOR * self.private_key

    def to_address(self) -> str:
        # Note: Sudokucoin uses the \x02\xe4 prefix unlike Bitcoin's \x00 (see what addresses this generates)
        # (ok, well half the time it does indeed generate 68 as the first 2 characters. But the other half of
        # the time it is nice)
        # Conversion is defined as Base58CheckEncode(ripemd(sha256(pubkey)))
        return self.to_public_key().to_address()

    def sign(self, msg: bytes) -> bytes:
        """
        Sign the message with the private key
        """
        private_key = ecdsa.SigningKey.from_secret_exponent(
            self.private_key, curve=ecdsa.SECP256k1
        )
        return private_key.sign(msg)

    @classmethod
    def create(cls, private_key: int = None) -> "Address":
        """
        Create a new address
        """
        if private_key is None:
            private_key = int.from_bytes(os.urandom(32), "big")
        return cls(private_key)

    @staticmethod
    def verify(msg: bytes, signature: bytes, public_key: EllipticCurvePoint) -> bool:
        """
        Verify the signature of the message with the public key
        """
        try:
            public_key = ecdsa.VerifyingKey.from_string(
                public_key.encode(), curve=ecdsa.SECP256k1
            )
            return public_key.verify(signature, msg)
        except ecdsa.BadSignatureError:
            return False
