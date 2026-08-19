# SPDX-FileCopyrightText: 2026 Alex Gee
# SPDX-License-Identifier: GPL-3.0-or-later
"""Repair the pycolmap CUDA wheel's missing ONNX Runtime provider DLLs.

The lyehe/build_gpu_colmap pycolmap 4.1.0 CUDA wheel ships the core
onnxruntime DLL but omits the two execution-provider DLLs it loads at
runtime. COLMAP appends the CUDA execution provider to every ONNX session
(ALIKED extraction, LightGlue/ALIKED matching) even with use_gpu off, so
the failed load escapes a COLMAP worker thread and aborts the subprocess
with exit code 3 (issue #11).

The matching DLLs live in the binary release zip produced by the same CI
run as the wheel. The version match with the embedded core is mandatory:
the same-named DLLs from the official onnxruntime-gpu packages fail with
WinError 1114 against it (verified 2026-08-19). Only the two members are
fetched from the 1.9 GB zip, via HTTP Range requests.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

from .gpu_extraction_install import _emit, _url_to_zip

PLUGIN_ROOT = Path(__file__).resolve().parent.parent

_ZIP_URL = ("https://github.com/lyehe/build_gpu_colmap/releases/download/"
            "v4.1.0/COLMAP-4.1.0-windows-2022-CUDA-cuDSS-Caspar.zip")

_PROVIDER_DLLS = [
    {"name": "onnxruntime_providers_shared.dll",
     "size": 22040,
     "sha256": "1bcbad19d14bc8395c1422c752e9e4cdd79e316e2582cdcd767bb8f500cdae99"},
    {"name": "onnxruntime_providers_cuda.dll",
     "size": 275606552,
     "sha256": "ce1c698cae708fd4ed9ab36eddf256213df40779d0806d20f32132c5d422da72"},
]

_MANUAL_FIX = ("see the manual fix on "
               "https://github.com/alexmgee/lichtfeld-360-plugin/issues/11")


def _dest_dir(root: Path) -> Path:
    return Path(root) / ".venv" / "Lib" / "site-packages" / "pycolmap.libs"


def missing_provider_dlls(root: Path = PLUGIN_ROOT) -> list[dict]:
    """Provider DLL specs not yet present next to pycolmap's onnxruntime."""
    dest = _dest_dir(root)
    return [s for s in _PROVIDER_DLLS if not (dest / s["name"]).exists()]


def _fetch_member(zf, info, spec: dict, dest: Path, on_output) -> None:
    partial = dest / (spec["name"] + ".partial")
    digest = hashlib.sha256()
    got = 0
    next_pct = 25
    with zf.open(info) as src, open(partial, "wb") as out:
        while True:
            chunk = src.read(8 << 20)
            if not chunk:
                break
            out.write(chunk)
            digest.update(chunk)
            got += len(chunk)
            pct = got * 100 // spec["size"]
            if pct >= next_pct:
                _emit(on_output, "  %s %d%%" % (spec["name"], pct))
                next_pct = pct + 25
    if got != spec["size"] or digest.hexdigest() != spec["sha256"]:
        partial.unlink(missing_ok=True)
        raise ValueError("hash mismatch for %s" % spec["name"])
    os.replace(partial, dest / spec["name"])
    _emit(on_output, "  installed %s" % spec["name"])


def ensure_provider_dlls(on_output=None, root: Path = PLUGIN_ROOT) -> None:
    """Download any missing provider DLLs into pycolmap.libs.

    No-op when both are present. Raises RuntimeError on failure, pointing
    at the manual fix, so the run stops with a diagnostic instead of the
    exit-code-3 crash.
    """
    missing = missing_provider_dlls(root)
    if not missing:
        return
    dest = _dest_dir(root)
    if not dest.is_dir():
        raise RuntimeError(
            "pycolmap.libs not found at %s; is the CUDA pycolmap wheel "
            "installed? (%s)" % (dest, _MANUAL_FIX))
    total_mb = sum(s["size"] for s in missing) >> 20
    _emit(on_output,
          "One-time download of %d MB of ONNX Runtime files the COLMAP "
          "package is missing (needed for ALIKED/LightGlue)..." % total_mb)
    try:
        with _url_to_zip(_ZIP_URL) as zf:
            infos = {i.filename.rsplit("/", 1)[-1]: i for i in zf.infolist()}
            for spec in missing:
                _fetch_member(zf, infos[spec["name"]], spec, dest, on_output)
    except Exception as exc:
        raise RuntimeError(
            "ALIKED/LightGlue need two ONNX Runtime files that the COLMAP "
            "package is missing, and the automatic download failed (%s); "
            "%s" % (exc, _MANUAL_FIX)) from exc
