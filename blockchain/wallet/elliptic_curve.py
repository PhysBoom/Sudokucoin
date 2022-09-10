from dataclasses import dataclass

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

    field_size: int = 2 ** 256 - 2 ** 32 - 2 ** 9 - 2 ** 8 - 2 ** 7 - 2 ** 6 - 2 ** 4 - 1
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

    def is_point_on_curve(self):
        return (self.x ** 3 + self.curve.a * self.x + self.curve.b - self.y ** 2) % self.curve.field_size == 0

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
            return EllipticCurvePoint(0, 0) # Same x but different y makes a line extending up to infinity
        else:
            # Find the tangent line at the current point using basic calc + modular inverses cuz we are doing stuff
            # mod the field size.

            # First, find the slope
            if self.x == other.x and self.y == other.y:
                # If the points are the same (we are doing p + p = 2p), the slope is the derivative of the curve
                # at the point (this is (3x^2+a)/2y, or the modular inverse of 2y since we are doing mod field size)
                slope = (3 * self.x ** 2 + self.curve.a) * modular_inverse(2 * self.y, self.curve.field_size)
            else:
                # Use good old (y2 - y1)/(x2 - x1)
                slope = (self.y - other.y) * modular_inverse(self.x - other.x, self.curve.field_size)
            line_function = lambda x: slope * (x - self.x) + self.y # Point slope

            # TODO: Figure out why this works. I had to look it up (found on Andrej Karpathy's implementation)
            intersection_x = (slope ** 2 - self.x - other.x) % self.curve.field_size
            # Must multiply y by -1 according to guide.
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
        return b'\x04' + self.x.to_bytes(32, 'big') + self.y.to_bytes(32, 'big')

    @classmethod
    def decode(cls, data: bytes):
        assert data[0] == 4
        return cls(int.from_bytes(data[1:33], 'big'), int.from_bytes(data[33:], 'big'))
