"""Fast kernels: a C shared library (built on first use) with a numba fallback.

Backend choice: ``LPLAB_BACKEND`` = ``c`` | ``numba`` (default: C if a compiler is available).
Both backends implement the same algorithms; ``tests/test_kernels.py`` checks they agree.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import platform
import shutil
import subprocess
from functools import cache
from pathlib import Path

import numpy as np
import numpy.typing as npt
from numba import njit

from ..gematria import IndexArray

SOURCE = Path(__file__).with_name("lpkernel.c")
CACHE_DIR = Path(os.environ.get("LPLAB_CACHE", Path.home() / ".cache" / "lplab"))

FloatArray = npt.NDArray[np.float32]
BoolArray = npt.NDArray[np.bool_]


class KernelBuildError(RuntimeError):
    pass


def _lib_path() -> Path:
    digest = hashlib.sha256(SOURCE.read_bytes() + platform.machine().encode()).hexdigest()[:12]
    return CACHE_DIR / f"lpkernel-{digest}.so"


def build(force: bool = False) -> Path:
    """Compile the C kernel into the cache dir. Raises KernelBuildError with compiler output."""
    out = _lib_path()
    if out.exists() and not force:
        return out
    cc = os.environ.get("CC") or shutil.which("cc") or shutil.which("gcc")
    if cc is None:
        raise KernelBuildError("no C compiler found (set CC or install gcc)")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(f".{os.getpid()}.tmp")
    cmd = [cc, "-O3", "-fPIC", "-shared", "-std=c99", "-o", str(tmp), str(SOURCE)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
    if proc.returncode != 0:
        raise KernelBuildError(f"{' '.join(cmd)} failed:\n{proc.stderr}")
    tmp.replace(out)  # atomic, so parallel workers never load a half-written file
    return out


@cache
def _clib() -> ctypes.CDLL:
    lib = ctypes.CDLL(str(build()))
    u8p = ctypes.POINTER(ctypes.c_uint8)
    f32p = ctypes.POINTER(ctypes.c_float)
    lib.lp_quad_score.argtypes = [u8p, ctypes.c_int64, f32p]
    lib.lp_quad_score.restype = ctypes.c_double
    lib.lp_climb_periodic.argtypes = [
        u8p, ctypes.c_int64, u8p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        f32p, ctypes.c_int, ctypes.c_int, ctypes.c_uint64, u8p,
    ]  # fmt: skip
    lib.lp_climb_periodic.restype = ctypes.c_double
    return lib


@cache
def backend() -> str:
    wanted = os.environ.get("LPLAB_BACKEND", "").lower()
    if wanted == "numba":
        return "numba"
    try:
        _clib()
        return "c"
    except (KernelBuildError, OSError, subprocess.SubprocessError):
        if wanted == "c":
            raise
        return "numba"


def _u8(a: npt.NDArray[np.generic]) -> ctypes._Pointer[ctypes.c_uint8]:
    return a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))


def _f32(a: FloatArray) -> ctypes._Pointer[ctypes.c_float]:
    return a.ctypes.data_as(ctypes.POINTER(ctypes.c_float))


# --- numba implementations (same algorithms as lpkernel.c) -------------------------------


@njit(cache=True)  # type: ignore[misc,unused-ignore]
def _nb_quad_score(t: IndexArray, quad: FloatArray) -> float:  # pragma: no cover - compiled
    n = t.size
    if n < 4:
        return -1e30
    s = 0.0
    for i in range(n - 3):
        q = ((np.int64(t[i]) * 29 + t[i + 1]) * 29 + t[i + 2]) * 29 + t[i + 3]
        s += quad[q]
    return s / (n - 3)


@njit(cache=True)  # type: ignore[misc,unused-ignore]
def _nb_climb(
    ct: IndexArray, skip: BoolArray, period: int, sign: int, a: int, b: int,
    quad: FloatArray, restarts: int, sweeps: int, seed: int,
) -> tuple[float, IndexArray]:  # pragma: no cover - compiled  # fmt: skip
    n = ct.size
    slot = np.empty(n, dtype=np.int64)
    live = 0
    for i in range(n):
        if skip[i]:
            slot[i] = -1
        else:
            slot[i] = live % period
            live += 1
    np.random.seed(seed)
    pt = np.empty(n, dtype=np.uint8)
    key = np.zeros(period, dtype=np.uint8)
    best_key = np.zeros(period, dtype=np.uint8)
    best = -1e30
    for _r in range(restarts):
        for k in range(period):
            key[k] = np.random.randint(0, 29)
        for i in range(n):
            pt[i] = ct[i] if slot[i] < 0 else (a * ((ct[i] - sign * key[slot[i]]) % 29) + b) % 29
        cur = _nb_quad_score(pt, quad)
        for _sw in range(sweeps):
            improved = False
            for k in range(period):
                keep = key[k]
                for v in range(29):
                    if v == keep:
                        continue
                    key[k] = v
                    for i in range(n):
                        if slot[i] == k:
                            pt[i] = (a * ((ct[i] - sign * v) % 29) + b) % 29
                    s = _nb_quad_score(pt, quad)
                    if s > cur:
                        cur = s
                        keep = v
                        improved = True
                key[k] = keep
                for i in range(n):
                    if slot[i] == k:
                        pt[i] = (a * ((ct[i] - sign * keep) % 29) + b) % 29
            if not improved:
                break
        if cur > best:
            best = cur
            best_key[:] = key
    return best, best_key


# --- public API ---------------------------------------------------------------------------


def quad_score(text: IndexArray, quad: FloatArray) -> float:
    t = np.ascontiguousarray(text, dtype=np.uint8)
    q = np.ascontiguousarray(quad, dtype=np.float32)
    if backend() == "c":
        return float(_clib().lp_quad_score(_u8(t), t.size, _f32(q)))
    return float(_nb_quad_score(t, q))


def climb_periodic(
    ct: IndexArray,
    period: int,
    quad: FloatArray,
    *,
    skip: BoolArray | None = None,
    sign: int = 1,
    a: int = 1,
    b: int = 0,
    restarts: int = 8,
    sweeps: int = 12,
    seed: int = 1,
) -> tuple[float, IndexArray]:
    """Best periodic key of length ``period`` under quadgram fitness. Returns (score, key)."""
    if period < 1:
        raise ValueError("period must be >= 1")
    c = np.ascontiguousarray(ct, dtype=np.uint8)
    s = np.zeros(c.size, dtype=np.uint8) if skip is None else skip.astype(np.uint8)
    q = np.ascontiguousarray(quad, dtype=np.float32)
    if backend() == "c":
        key = np.zeros(period, dtype=np.uint8)
        score = _clib().lp_climb_periodic(
            _u8(c), c.size, _u8(s), period, sign, a % 29, b % 29, _f32(q),
            restarts, sweeps, seed, _u8(key),
        )  # fmt: skip
        return float(score), key
    score, key = _nb_climb(c, s.astype(np.bool_), period, sign, a % 29, b % 29, q,
                           restarts, sweeps, seed)  # fmt: skip
    return float(score), key.astype(np.uint8)
