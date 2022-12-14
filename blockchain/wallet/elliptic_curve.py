from dataclasses import dataclass
import base64
import math
from Crypto.Hash import RIPEMD160
import hashlib

# From scratch implementation of elliptic curve by me (w/ reference to Mastering Bitcoin book's description of stuff). If there are any errors, please let me know.

# The extended euclidean + modular inverse implementations were stolen from Andrej Karpathy's implementation
# of Bitcoin which I believe were originally stolen from Wikipedia. Credit where credit is due.
def extended_euclidean_algorithm(a, b):
    old_r, r = a, b
    old_s, s = 1, 0
    old_t, t = 0, 1
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    return old_r, old_s, old_t


def modular_inverse(n, p):
    gcd, x, y = extended_euclidean_algorithm(n, p)
    return x % p


# Stolen from Karpathy's implementation cuz I'm too lazy to implement
# This myself.
def b58encode(b: bytes, alphabet: str) -> str:
    n = int.from_bytes(b, "big")
    chars = []
    while n:
        n, i = divmod(n, 58)
        chars.append(alphabet[i])
    # special case handle the leading 0 bytes... ¯\_(ツ)_/¯
    num_leading_zeros = len(b) - len(b.lstrip(b"\x00"))
    return num_leading_zeros * alphabet[0] + "".join(reversed(chars))


def b58decode(s: str, alphabet: str) -> bytes:
    n = 0
    for c in s:
        n *= 58
        n += alphabet.index(c)
    return n.to_bytes(math.ceil(n.bit_length() / 8), "big")


def sha256(msg):
    return hashlib.sha256(msg).digest()


def ripemd160(msg):
    return RIPEMD160.new(msg).digest()


@dataclass(frozen=True)
class EllipticCurve:
    """
    An elliptic curve is a function in the form y^2 = x^3 + ax + b (mod some field size).
    As such, we have the following implementation of the elliptic curve

    Attributes:
        <int> field_size: A prime number over which the curve is modded
        (default is the large number as per secp256k1 specifications)
        <int> a: Coefficient of x term (0 in secp256k1)
        <int> b: Constant (7 in secp256k1)
    """

    field_size: int = (
        2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1
    )
    a: int = 0
    b: int = 7


@dataclass(frozen=True)
class EllipticCurvePoint:
    """
    A point on an elliptic curve.

    Attributes:
        <int> x: X coordinate
        <int> y: Y coordinate
        <EllipticCurve> curve: Curve which the point is on

    Methods:
        <bool> is_point_on_curve: Returns whether or not the point is on the
        given curve
    """

    x: int
    y: int
    curve: EllipticCurve = EllipticCurve()

    ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

    def is_point_on_curve(self):
        return (
            self.x**3 + self.curve.a * self.x + self.curve.b - self.y**2
        ) % self.curve.field_size == 0

    def is_point_at_infinity(self):
        return self.x == 0 and self.y == 0

    def __add__(self, other):
        # The "point at infinity" is a point where x = y = 0 that is curve-independent.
        # The special case with it is that if P1 + point_at_infinity = P1
        if self.is_point_at_infinity():
            return other
        elif other.is_point_at_infinity():
            return self
        elif self.x == other.x and self.y != other.y:
            return EllipticCurvePoint(
                0, 0
            )  # Same x but different y makes a line extending up to infinity
        else:
            """
            The derivation of the below is as follows:

            Since we know that point addition (P1 + P2 = P3) has P3 = the point that the line between
            P1 and P2 intersects on the curve, we can state the following:

            1. The line between P1 and P2 is (y - P1.y) = m * (x - P1.x), where m is either (P1.y - P2.y)/(P1.x - P2.x)
            or, if P1 = P2, the derivative of the curve at (x, y) (which is (3x^2 + a)/2y)

            2. The equation (m * (x-P1.x) + P1.y)^2 = x^3 + ax + b, or (m * (x-P1.x) + P1.y)^2 - x^3 - ax - b = 0
            represents the intersection of the line and the curve

            3. P1.x, P2.x, and P3.x are all solutions to the equation, so (x-P1.x)(x-P2.x)(x-P3.x) = 0

            Therefore, we can do the following to solve for point 3:

            1. Expand the equation of intersection to get
            x^3 - m^2x^2 + 2m^2x(P1.y) + m^2(P1.y)^2 - 2P1.y(m)(P1.x) + ax + b - P1.x^2 = 0

            2. Group the expression by powers of x
            x^3 - x^2(m^2) + x(2(m^2)(P1.y) - 2(P1.y)(m) + a) + ((m^2)(P1.y^2) + 2(P1.y)(m)(P1.x)-P1.x^2) = 0

            3. Expand the condition in statement 3 to get
            x^3 - x^2(P1.x+P2.x+P3.x) + x((P1.x)(P2.x) + (P1.x)(P3.x) + (P2.x)(P3.x)) + ((P1.x)(P2.x)(P3.x)) = 0

            4. Because the two equations are equal, we know that the coefficients must be equal (by Viera's law, although
            also logically if ax^3 + bx^2 + cx + d = ex^3 + fx^2 + gx + d for all x, a = e, b = f etc. since otherwise they
            are two different functions).

            As such, P1.x + P2.x + P3.x = m^2

            --> P3.x = m^2 - P1.x - P2.x

            5. By the line equation, we know that (P3.y - P1.y) = m(P3.x - P1.x)

            --> P3.y' = m(P3.x - P1.x) + P1.y

            Since in elliptic curve addition we have to reflect over the x axis, P3.y is then just -P3.y'
            """
            # Find the tangent line at the current point using basic calc + modular inverses cuz we are doing stuff
            # mod the field size.

            # First, find the slope
            if self.x == other.x:
                # If the points are the same (we are doing p + p = 2p), the slope is the derivative of the curve
                # at the point (this is (3x^2+a)/2y, or the modular inverse of 2y since we are doing mod field size)
                slope = (3 * self.x**2 + self.curve.a) * modular_inverse(
                    2 * self.y, self.curve.field_size
                )
            else:
                # Use good old (y2 - y1)/(x2 - x1)
                slope = (self.y - other.y) * modular_inverse(
                    self.x - other.x, self.curve.field_size
                )
            line_function = lambda x: slope * (x - self.x) + self.y  # Point slope
            intersection_x = (slope**2 - self.x - other.x) % self.curve.field_size
            intersection_y = -line_function(intersection_x) % self.curve.field_size
            return EllipticCurvePoint(intersection_x, intersection_y, self.curve)

    def __mul__(self, times: int):
        # Stolen from Andrej Karpathy's implementation and refactored slightly
        assert int(times) == times
        result = EllipticCurvePoint(0, 0, self.curve)
        current_point = self
        while times:
            if times % 2 == 1:
                result += current_point
            current_point += current_point
            times >>= 1
        return result

    def __rmul__(self, times: int):
        return self * times

    def encode(self):
        return b"\x04" + self.x.to_bytes(32, "big") + self.y.to_bytes(32, "big")

    def encode_b64(self):
        return base64.b64encode(self.encode()).decode()

    def to_address(self):
        k = self.encode()
        address = ripemd160(sha256(k))
        checksum = sha256(sha256(b"\x69" + address))[:4]
        new_payload = b"\x02\xe4" + address + checksum
        return b58encode(new_payload, self.ALPHABET)

    @classmethod
    def decode(cls, data: bytes):
        assert data[0] == 4
        return cls(int.from_bytes(data[1:33], "big"), int.from_bytes(data[33:], "big"))

    @classmethod
    def decode_b64(cls, data: str):
        return cls.decode(base64.b64decode(data))
