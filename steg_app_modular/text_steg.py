"""
Utility functions for text-based steganography helpers that can be reused
inside the Streamlit UI without pulling in heavy dependencies automatically.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# --- Imports for libraries that (should) support encode/decode ---
try:
    import zwsp_steg  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    zwsp_steg = None  # type: ignore

try:
    import pyUnicodeSteganography as usteg  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    usteg = None  # type: ignore

# For homoglyph detection
try:
    from confusables import confusable_characters  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    confusable_characters = None  # type: ignore

# ========== ENCODERS ==========


def encode_zwsp_py(secret: str, cover: str) -> str:
    if not zwsp_steg:
        raise ImportError("zwsp_steg-py not installed")
    # Note: zwsp_steg.encode(secret, [optional mode]) returns pure stego (no cover)
    # So to embed into cover, we just append or interleave.
    hidden = zwsp_steg.encode(secret)
    return cover + hidden


def encode_pyUnicode(secret: str, cover: str) -> str:
    if not usteg:
        raise ImportError("pyUnicodeSteganography not installed")
    return usteg.encode(cover, secret)


def encode_zwsteg_cli_wrapper(secret: str, cover: str) -> str:
    """
    Wrapper for ZW-Steg tool: this is not a library, but you can
    call its code via subprocess or import if possible.
    For simplicity, we treat it like zero-width: append hidden after cover.
    """
    encoded = zwsp_steg.encode(secret) if zwsp_steg else None
    if encoded:
        return cover + encoded
    raise ImportError("zwsp-steg modules not available")


# ========== DECODERS ==========

def decode_zwsp_py(text: str) -> Optional[str]:
    if not zwsp_steg:
        raise ImportError("zwsp_steg-py not installed")
    try:
        return zwsp_steg.decode(text)
    except Exception:
        return None


def decode_pyUnicode(text: str) -> Optional[str]:
    if not usteg:
        raise ImportError("pyUnicodeSteganography not installed")
    try:
        return usteg.decode(text)
    except Exception:
        return None


def decode_zwsteg_cli_wrapper(text: str) -> Optional[str]:
    # same as zwsp decoder
    return decode_zwsp_py(text)


# ========== DETECTORS ==========

def detect_zero_width(text: str) -> List[str]:
    zw = ["\u200b", "\u200c", "\u200d", "\u2060", "\u2062", "\u2063", "\ufeff"]
    return [c for c in text if c in zw]


def detect_homoglyphs(text: str) -> List[Tuple[str, List[str]]]:
    if not confusable_characters:
        raise ImportError("confusables not installed")
    findings = []
    for ch in text:
        conf = confusable_characters(ch)
        if conf:
            findings.append((ch, conf))
    return findings


def detect_whitespace_steg(text: str) -> Dict[str, bool]:
    # detect suspicious repeated spaces or trailing spaces
    trailing = re.search(r"[ ]+$", text, flags=re.MULTILINE)
    multi = re.search(r" {2,}", text)
    tabs = re.search(r"\t+", text)
    return {
        "trailing_spaces": bool(trailing),
        "multiple_spaces": bool(multi),
        "tabs": bool(tabs),
    }


# ========== UNIVERSAL RUNNER ==========

def encode_text(method: str, cover: str, secret: str) -> str:
    if method == "zwsp-py":
        return encode_zwsp_py(secret, cover)
    if method == "pyUnicode":
        return encode_pyUnicode(secret, cover)
    if method == "zwsteg-cli":
        return encode_zwsteg_cli_wrapper(secret, cover)
    raise ValueError(f"Unknown method {method}")


def try_all_decoders(text: str) -> Dict[str, str]:
    results = {}
    for name, fn in [
        ("zwsp-py", decode_zwsp_py),
        ("pyUnicode", decode_pyUnicode),
        ("zwsteg-cli", decode_zwsteg_cli_wrapper),
    ]:
        try:
            msg = fn(text)
            if msg:
                results[name] = msg
        except ImportError:
            continue
    return results


def detect_all(text: str) -> Dict[str, Optional[object]]:
    return {
        "zero_width_chars": detect_zero_width(text),
        "homoglyphs": detect_homoglyphs(text) if confusable_characters else None,
        "whitespace_patterns": detect_whitespace_steg(text),
    }


def available_methods() -> List[str]:
    """Return list of encode methods that currently have dependencies available."""
    methods = []
    if zwsp_steg:
        methods.append("zwsp-py")
    if usteg:
        methods.append("pyUnicode")
    if zwsp_steg:
        methods.append("zwsteg-cli")
    return methods


if __name__ == "__main__":
    cover = input("Cover text: ")
    secret = input("Secret message: ")
    method = input("Method (zwsp-py / pyUnicode / zwsteg-cli): ")
    encoded = encode_text(method, cover, secret)
    print("Encoded text:\n", encoded)
    print("Detection:", detect_all(encoded))
    print("Decoded results:", try_all_decoders(encoded))
