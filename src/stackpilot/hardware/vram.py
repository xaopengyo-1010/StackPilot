from __future__ import annotations


MAX_REASONABLE_VRAM_GB = 128


def adapter_ram_to_gb(value: object | None) -> float | None:
    """Convert a Windows AdapterRAM value in bytes to GB when plausible."""

    if value is None:
        return None
    try:
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            numeric = int(float(text))
        else:
            numeric = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if numeric <= 0:
        return None
    gb = round(numeric / (1024 ** 3), 2)
    if gb <= 0 or gb > MAX_REASONABLE_VRAM_GB:
        return None
    return gb


def estimate_dedicated_vram_from_name(name: str | None) -> float | None:
    """Return a conservative VRAM estimate for common dedicated GPU names."""

    text = (name or "").upper()
    if not text:
        return None
    known_models = {
        "5090": 32,
        "4090": 24,
        "3090": 24,
        "4080": 16,
        "3080": 10,
        "4070": 12,
        "3070": 8,
        "3060": 12,
        "4060": 8,
        "4050": 6,
        "2080": 8,
        "2070": 8,
        "2060": 6,
        "1660": 6,
        "1650": 4,
        "1060": 6,
        "1050": 4,
        "RX 7900": 24,
        "RX 7800": 16,
        "RX 7700": 12,
        "RX 7600": 8,
        "RX 6800": 16,
        "RX 6700": 12,
        "RX 6600": 8,
    }
    for marker, vram in known_models.items():
        if marker in text:
            return float(vram)
    if "RTX" in text:
        return 8.0
    if "GTX" in text:
        return 4.0
    if "RADEON RX" in text:
        return 8.0
    return None
