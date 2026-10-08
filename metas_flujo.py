"""Metas de personas: Meta Flujo Diaria HalloWIN.xlsx, columna Meta (pers./día)."""

METAS_OCTUBRE_2026 = (130, 150, 250, 210, 410, 335, 165)


def meta_flujo(fecha):
    """Devuelve None fuera del período autorizado; cero no significa sin meta."""
    if (fecha.year, fecha.month) == (2026, 10):
        return METAS_OCTUBRE_2026[fecha.weekday()]
    return None
