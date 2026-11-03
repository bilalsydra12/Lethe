"""Tiny 4x4 matrix / vector helpers (row-major lists), enough to pose and re-skin a glTF without numpy."""
import math


def eye():
    return [[1.0 if r == c else 0.0 for c in range(4)] for r in range(4)]


def mul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def from_gltf(m):          # glTF stores column-major
    return [[m[c * 4 + r] for c in range(4)] for r in range(4)]


def to_gltf(M):
    return [M[r][c] for c in range(4) for r in range(4)]


def trs(t=None, q=None, s=None):
    M = eye()
    if s:
        M = [[M[r][c] * (s[c] if c < 3 else 1) for c in range(4)] for r in range(4)]
    if q:
        M = mul(quat_mat(q), M)
    if t:
        T = eye()
        T[0][3], T[1][3], T[2][3] = t
        M = mul(T, M)
    return M


def quat_mat(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
            [0, 0, 0, 1]]


def axis_angle(axis, ang):
    n = math.sqrt(sum(a * a for a in axis)) or 1.0
    s = math.sin(ang / 2)
    return quat_mat((axis[0] / n * s, axis[1] / n * s, axis[2] / n * s, math.cos(ang / 2)))


def between(a, b):
    """Rotation matrix taking direction a onto direction b."""
    na = math.sqrt(sum(x * x for x in a)); nb = math.sqrt(sum(x * x for x in b))
    a = [x / na for x in a]; b = [x / nb for x in b]
    c = [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
    d = max(-1.0, min(1.0, sum(a[i] * b[i] for i in range(3))))
    if math.sqrt(sum(x * x for x in c)) < 1e-9:
        return eye()
    return axis_angle(c, math.acos(d))


def inv(M):
    """Inverse of an affine 4x4 (general 3x3 part)."""
    a = [row[:3] for row in M[:3]]
    det = (a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1]) - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
           + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0]))
    ia = [[(a[1][1] * a[2][2] - a[1][2] * a[2][1]) / det, (a[0][2] * a[2][1] - a[0][1] * a[2][2]) / det, (a[0][1] * a[1][2] - a[0][2] * a[1][1]) / det],
          [(a[1][2] * a[2][0] - a[1][0] * a[2][2]) / det, (a[0][0] * a[2][2] - a[0][2] * a[2][0]) / det, (a[0][2] * a[1][0] - a[0][0] * a[1][2]) / det],
          [(a[1][0] * a[2][1] - a[1][1] * a[2][0]) / det, (a[0][1] * a[2][0] - a[0][0] * a[2][1]) / det, (a[0][0] * a[1][1] - a[0][1] * a[1][0]) / det]]
    t = [M[0][3], M[1][3], M[2][3]]
    it = [-sum(ia[r][k] * t[k] for k in range(3)) for r in range(3)]
    return [ia[0] + [it[0]], ia[1] + [it[1]], ia[2] + [it[2]], [0, 0, 0, 1]]


def pt(M, p):
    return [M[r][0] * p[0] + M[r][1] * p[1] + M[r][2] * p[2] + M[r][3] for r in range(3)]


def vec(M, v):
    return [M[r][0] * v[0] + M[r][1] * v[1] + M[r][2] * v[2] for r in range(3)]


def pos(M):
    return [M[0][3], M[1][3], M[2][3]]
