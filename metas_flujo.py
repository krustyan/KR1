"""Metas de personas: Meta Flujo Diaria HalloWIN.xlsx, columna Meta (pers./día)."""

METAS_DIARIAS_2026 = (130, 150, 250, 210, 410, 335, 165)


def meta_flujo(fecha):
    """Devuelve None fuera del período autorizado; cero no significa sin meta."""
    if fecha.year == 2026 and fecha.month in (10, 11, 12):
        return METAS_DIARIAS_2026[fecha.weekday()]
    return None
