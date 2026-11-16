"""Constantes métier partagées (modèles, ETL, API)."""

# Les 12 saisons glissantes de 3 mois publiées par la NOAA, dans l'ordre (DJF = déc-jan-fév).
# Tuple et non liste : models.py l'injecte tel quel dans un CHECK SQL
# (f"season IN {SEASONS}" -> "season IN ('DJF', 'JFM', ...)"), une liste donnerait du SQL invalide.
SEASONS: tuple[str, ...] = (
    "DJF",
    "JFM",
    "FMA",
    "MAM",
    "AMJ",
    "MJJ",
    "JJA",
    "JAS",
    "ASO",
    "SON",
    "OND",
    "NDJ",
)
