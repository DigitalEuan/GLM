"""Spatial carriers, discrete fields and boundary conditions.

CentCalculus2 is explicit that *a point in 24-D space is not a field*.  This
module therefore separates:

* :data:`Carrier24` — an exact rational point in the 24-D carrier;
* :class:`ScalarField` / :class:`VectorField` — samplable fields on the integer
  lattice (optionally spanning only the first ``ndim`` axes);
* discrete stencils: central gradient, divergence, the antisymmetric
  **2-form** curl with 276 independent components, and the Laplacian;
* :class:`BoundaryCondition` (Dirichlet / Neumann / Robin) applied by
  :class:`GridField` when a stencil samples outside the domain.

All arithmetic is exact.  ``h`` (grid spacing) must be a positive rational.
The discrete identities ``curl ∘ grad = 0`` and ``div ∘ curl = 0`` hold exactly
for these central stencils on interior points and are tested.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

from .exact import CentError, ErrorCode, Q, div, format_q, q, sign

DIM = 24

Carrier24 = tuple[Q, ...]


def carrier(values: Iterable[Any], where: Optional[str] = None) -> Carrier24:
    pts = tuple(q(v, where) for v in values)
    if len(pts) != DIM:
        raise CentError(
            ErrorCode.INVALID_INPUT,
            f"carrier point must have {DIM} coordinates",
            where,
            {"got": len(pts)},
        )
    return pts


def origin() -> Carrier24:
    return tuple(q(0) for _ in range(DIM))


def norm_square(v: Carrier24) -> Q:
    return sum((x * x for x in v), q(0))


def distance_square(a: Carrier24, b: Carrier24) -> Q:
    return sum(((x - y) ** 2 for x, y in zip(a, b)), q(0))


def tax_residual(v: Carrier24, lam: Carrier24, divisor: int = 32) -> Q:
    """Geometric residual ``||v − λ||² / 32`` (a score, not an energy)."""
    if divisor <= 0:
        raise CentError(ErrorCode.INVALID_INPUT, "TAX divisor must be positive")
    return distance_square(v, lam) / divisor


# ---------------------------------------------------------------------------
# Boundary conditions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BoundaryCondition:
    """Dirichlet, Neumann or Robin boundary data on a lattice face.

    ``αψ + β(∂ψ/∂n) = γ`` with the outward normal derivative discretised as
    ``(ψ_face − ψ_interior)/(h·gap)``.  Dirichlet fixes ``ψ = value``;
    Neumann (``β ≠ 0, α = 0, γ = 0``) mirrors the interior sample, giving a
    zero one-sided difference.
    """

    kind: str = "dirichlet"
    value: Q = Fraction(0)
    alpha: Q = Fraction(1)
    beta: Q = Fraction(1)
    gamma: Q = Fraction(0)

    def __post_init__(self) -> None:
        kind = self.kind.lower()
        if kind not in {"dirichlet", "neumann", "robin"}:
            raise CentError(ErrorCode.INVALID_INPUT, f"unknown boundary condition {self.kind!r}")
        object.__setattr__(self, "kind", kind)
        for name in ("value", "alpha", "beta", "gamma"):
            object.__setattr__(self, name, q(getattr(self, name)))

    def extrapolate(self, interior: Q, h: Q, gap: int = 1) -> Q:
        """Value at ``gap`` lattice steps outside the domain."""
        interior, h = q(interior), q(h)
        if h <= 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "grid spacing must be positive")
        if gap < 1:
            raise CentError(ErrorCode.INVALID_INPUT, "boundary gap must be >= 1")
        if self.kind == "dirichlet":
            return self.value
        if self.kind == "neumann":
            return interior
        denom = self.alpha + self.beta / (h * gap)
        if denom == 0:
            raise CentError(
                ErrorCode.DOMAIN_ERROR,
                "Robin condition is singular for this spacing",
                detail={"alpha": format_q(self.alpha), "beta": format_q(self.beta)},
            )
        return (self.gamma + self.beta * interior / (h * gap)) / denom


# ---------------------------------------------------------------------------
# Fields
# ---------------------------------------------------------------------------

class ScalarField:
    """A samplable exact scalar field on ``Z^ndim``."""

    def __init__(self, sampler: Callable[[tuple[int, ...]], Any], ndim: int = DIM,
                 name: str = "field"):
        if not 1 <= ndim <= DIM:
            raise CentError(ErrorCode.INVALID_INPUT, f"ndim must be in 1..{DIM}")
        self._sampler = sampler
        self.ndim = ndim
        self.name = name

    def at(self, index: Sequence[int]) -> Q:
        idx = tuple(int(i) for i in index)
        if len(idx) != self.ndim:
            raise CentError(
                ErrorCode.INVALID_INPUT,
                f"field index has {len(idx)} coordinates, expected {self.ndim}",
            )
        return q(self._sampler(idx))

    def __call__(self, index: Sequence[int]) -> Q:
        return self.at(index)

    def shifted(self, axis: int, delta: int) -> "ScalarField":
        return ScalarField(lambda idx: self.at(_shift(idx, axis, delta)), self.ndim,
                           f"{self.name}[{axis}{delta:+d}]")

    def map(self, fn: Callable[[Q], Any], name: str = "map") -> "ScalarField":
        return ScalarField(lambda idx: fn(self.at(idx)), self.ndim, f"{name}({self.name})")

    def __repr__(self) -> str:  # pragma: no cover - formatting
        return f"ScalarField({self.name!r}, ndim={self.ndim})"


def _shift(index: Sequence[int], axis: int, delta: int) -> tuple[int, ...]:
    out = list(index)
    out[axis] += delta
    return tuple(out)


@dataclass
class GridDomain:
    """A rectangular lattice domain with one boundary condition for all faces."""

    shape: tuple[int, ...]
    spacing: Q = Fraction(1)
    boundary: BoundaryCondition = field(default_factory=BoundaryCondition)

    def __post_init__(self) -> None:
        if not self.shape or any(s <= 0 for s in self.shape):
            raise CentError(ErrorCode.INVALID_INPUT, "grid shape must be positive in every axis")
        object.__setattr__(self, "shape", tuple(int(s) for s in self.shape))
        object.__setattr__(self, "spacing", q(self.spacing))
        if self.spacing <= 0:
            raise CentError(ErrorCode.DOMAIN_ERROR, "grid spacing must be positive")

    @property
    def ndim(self) -> int:
        return len(self.shape)

    def in_bounds(self, index: Sequence[int]) -> bool:
        return all(0 <= i < n for i, n in zip(index, self.shape))

    def nearest_interior(self, index: Sequence[int]) -> tuple[int, ...]:
        return tuple(min(max(int(i), 0), n - 1) for i, n in zip(index, self.shape))


class GridField(ScalarField):
    """A sparse exact grid field with boundary-condition extrapolation."""

    def __init__(self, values: Mapping[Sequence[int], Any], domain: GridDomain,
                 name: str = "grid"):
        self.values = {tuple(int(i) for i in k): q(v) for k, v in values.items()}
        for idx in self.values:
            if len(idx) != domain.ndim:
                raise CentError(
                    ErrorCode.INVALID_INPUT,
                    f"index {idx} does not match grid dimension {domain.ndim}",
                )
            if not domain.in_bounds(idx):
                raise CentError(ErrorCode.INVALID_INPUT, f"index {idx} outside the grid domain")
        self.domain = domain
        super().__init__(self._sample_with_bc, domain.ndim, name)

    def _sample_with_bc(self, index: Sequence[int]) -> Q:
        if self.domain.in_bounds(index):
            if index not in self.values:
                raise CentError(
                    ErrorCode.DOMAIN_ERROR,
                    "undefined sample at an interior grid point",
                    detail={"index": list(index)},
                )
            return self.values[index]
        # Extrapolate along the first out-of-range axis, then resample
        # recursively so corners receive the composed condition.
        for axis, (i, n) in enumerate(zip(index, self.domain.shape)):
            if i < 0 or i >= n:
                gap = -i if i < 0 else i - (n - 1)
                inner = list(index)
                inner[axis] = 0 if i < 0 else n - 1
                interior_value = self._sample_with_bc(tuple(inner))
                return self.domain.boundary.extrapolate(
                    interior_value, self.domain.spacing, gap
                )
        raise AssertionError("unreachable")  # pragma: no cover


def analytic_field(fn: Callable[[tuple[int, ...]], Any], ndim: int = DIM,
                   name: str = "analytic") -> ScalarField:
    return ScalarField(lambda idx: q(fn(idx)), ndim, name)


@dataclass(frozen=True)
class VectorField:
    """A vector field as ``ndim`` scalar components (24 by default)."""

    components: tuple[ScalarField, ...]

    def __post_init__(self) -> None:
        if not self.components:
            raise CentError(ErrorCode.INVALID_INPUT, "vector field has no components")
        ndims = {c.ndim for c in self.components}
        if len(ndims) != 1:
            raise CentError(ErrorCode.INVALID_INPUT, "vector components have mixed dimensions")

    @property
    def ndim(self) -> int:
        return self.components[0].ndim

    def at(self, index: Sequence[int]) -> tuple[Q, ...]:
        return tuple(c.at(index) for c in self.components)

    def __getitem__(self, axis: int) -> ScalarField:
        return self.components[axis]


@dataclass(frozen=True)
class TwoForm:
    """Antisymmetric 2-form on the carrier: 276 independent components."""

    values: Mapping[tuple[int, int], Q]

    def __post_init__(self) -> None:
        clean: dict[tuple[int, int], Q] = {}
        for (i, j), v in self.values.items():
            if not (0 <= i < DIM and 0 <= j < DIM):
                raise CentError(ErrorCode.INVALID_INPUT, f"2-form index out of range: {(i, j)}")
            if i == j:
                raise CentError(ErrorCode.INVALID_INPUT, "2-form diagonal must vanish")
            a, b = (i, j) if i < j else (j, i)
            clean[(a, b)] = q(v)
        object.__setattr__(self, "values", clean)

    def get(self, i: int, j: int) -> Q:
        if i == j:
            return q(0)
        a, b = (i, j) if i < j else (j, i)
        s = 1 if (a, b) == (i, j) else -1
        return s * self.values.get((a, b), q(0))

    def components(self) -> tuple[tuple[int, int, Q], ...]:
        return tuple((i, j, self.values[(i, j)]) for i, j in sorted(self.values))

    def is_zero(self) -> bool:
        return all(v == 0 for v in self.values.values())

    def __len__(self) -> int:
        return len(self.values)


# ---------------------------------------------------------------------------
# Discrete stencils
# ---------------------------------------------------------------------------

def _check_h(h: Any) -> Q:
    h = q(h)
    if h <= 0:
        raise CentError(ErrorCode.DOMAIN_ERROR, "stencil spacing h must be strictly positive")
    return h


def gradient(field: ScalarField, h: Any = 1) -> VectorField:
    """Central-difference gradient; returns a 24-component vector field.

    Components beyond the field's ``ndim`` are identically zero.
    """
    h = _check_h(h)
    comps: list[ScalarField] = []
    for axis in range(DIM):
        if axis < field.ndim:
            def make(axis=axis, field=field):
                def sample(idx: tuple[int, ...]) -> Q:
                    return (field.at(_shift(idx, axis, 1)) - field.at(_shift(idx, axis, -1))) / (2 * h)
                return sample
            comps.append(ScalarField(make(), field.ndim, f"grad[{axis}]({field.name})"))
        else:
            comps.append(ScalarField(lambda idx: q(0), field.ndim, "zero"))
    return VectorField(tuple(comps))


def gradient_at(field: ScalarField, point: Sequence[int], h: Any = 1) -> tuple[Q, ...]:
    return gradient(field, h).at(point)


def divergence_at(vector: VectorField, point: Sequence[int], h: Any = 1) -> Q:
    """Central-difference divergence ``Σ ∂_i v_i``."""
    h = _check_h(h)
    total = q(0)
    for axis in range(vector.ndim):
        comp = vector[axis]
        total += (comp.at(_shift(point, axis, 1)) - comp.at(_shift(point, axis, -1))) / (2 * h)
    return total


def divergence(vector: VectorField, h: Any = 1) -> ScalarField:
    h = _check_h(h)

    def sample(idx: tuple[int, ...]) -> Q:
        total = q(0)
        for axis in range(vector.ndim):
            comp = vector[axis]
            total += (comp.at(_shift(idx, axis, 1)) - comp.at(_shift(idx, axis, -1))) / (2 * h)
        return total

    return ScalarField(sample, vector.ndim, "div")


def curl_2form_at(vector: VectorField, point: Sequence[int], h: Any = 1) -> TwoForm:
    """Antisymmetric exterior derivative ``ω_ij = ∂_i v_j − ∂_j v_i``.

    All 276 components for the 24-D carrier are produced.  The classical 3-D
    curl is a three-component projection of this object.
    """
    h = _check_h(h)
    values: dict[tuple[int, int], Q] = {}
    ndim = vector.ndim
    for i in range(ndim):
        vi = vector[i]
        for j in range(i + 1, ndim):
            vj = vector[j]
            dij = (vj.at(_shift(point, i, 1)) - vj.at(_shift(point, i, -1))) / (2 * h)
            dji = (vi.at(_shift(point, j, 1)) - vi.at(_shift(point, j, -1))) / (2 * h)
            values[(i, j)] = dij - dji
    return TwoForm(values)


def curl_3d(vector: VectorField, h: Any = 1) -> VectorField:
    """The 3-D curl ``(ω_23, −ω_13, ω_12)`` as a vector field.

    Only the first three axes participate; the remaining 21 components are
    identically zero.  This is the documented restriction of the 2-form.
    """
    h = _check_h(h)
    ndim = vector.ndim
    if ndim < 3:
        raise CentError(ErrorCode.DOMAIN_ERROR, "3-D curl needs at least three axes")

    def component(a: int, b: int, sign: int, name: str) -> ScalarField:
        def sample(idx: tuple[int, ...]) -> Q:
            va, vb = vector[a], vector[b]
            p = (vb.at(_shift(idx, a, 1)) - vb.at(_shift(idx, a, -1))) / (2 * h)
            r = (va.at(_shift(idx, b, 1)) - va.at(_shift(idx, b, -1))) / (2 * h)
            return sign * (p - r)
        return ScalarField(sample, ndim, name)

    comps = [
        component(1, 2, 1, "curl_x"),
        component(0, 2, -1, "curl_y"),
        component(0, 1, 1, "curl_z"),
    ] + [ScalarField(lambda idx: q(0), ndim, "zero") for _ in range(DIM - 3)]
    return VectorField(tuple(comps))


def laplacian_at(field: ScalarField, point: Sequence[int], h: Any = 1,
                 axes: Optional[Sequence[int]] = None) -> Q:
    """Central second difference summed over ``axes`` (default: all field axes)."""
    h = _check_h(h)
    axes = tuple(range(field.ndim)) if axes is None else tuple(axes)
    total = q(0)
    centre = field.at(point)
    for axis in axes:
        if not 0 <= axis < field.ndim:
            raise CentError(ErrorCode.INVALID_INPUT, f"axis {axis} outside the field")
        total += (
            field.at(_shift(point, axis, 1)) - 2 * centre + field.at(_shift(point, axis, -1))
        ) / (h * h)
    return total


def laplacian(field: ScalarField, h: Any = 1,
              axes: Optional[Sequence[int]] = None) -> ScalarField:
    h = _check_h(h)
    selected = tuple(range(field.ndim)) if axes is None else tuple(axes)

    def sample(idx: tuple[int, ...]) -> Q:
        return laplacian_at(field, idx, h, selected)

    return ScalarField(sample, field.ndim, "laplacian")


def divergence_of_curl_3d(vector: VectorField, point: Sequence[int], h: Any = 1) -> Q:
    """``div(curl(v))``; exactly zero for these stencils on interior points."""
    return divergence_at(curl_3d(vector, h), point, h)
