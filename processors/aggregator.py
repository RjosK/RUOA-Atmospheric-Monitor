import polars as pl
import numpy as np
from utils.logger import get_logger

logger = get_logger(__name__)

def _mean_if_valid(col_name: str, valid_threshold: int = 18) -> pl.Expr:
    """Calcula el promedio si hay al menos `valid_threshold` valores no nulos en el grupo."""
    return pl.when(pl.col(col_name).drop_nulls().count() >= valid_threshold) \
             .then(pl.col(col_name).mean().round(2)) \
             .otherwise(None) \
             .alias(col_name)

def _circular_mean_if_valid(col_name: str, valid_threshold: int = 18) -> pl.Expr:
    """Calcula la media circular (para grados) si hay al menos `valid_threshold` valores válidos."""
    # Convertimos a radianes
    rads = pl.col(col_name) * (np.pi / 180.0)
    
    sin_mean = rads.sin().mean()
    cos_mean = rads.cos().mean()
    
    # arctan2(sin, cos) y luego de vuelta a grados, mod 360
    angle_deg = pl.arctan2(sin_mean, cos_mean) * (180.0 / np.pi)
    angle_mod = (angle_deg + 360) % 360
    
    return pl.when(pl.col(col_name).drop_nulls().count() >= valid_threshold) \
             .then(angle_mod.round(2)) \
             .otherwise(None) \
             .alias(col_name)

def aggregate_daily(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Agrupa los datos por región y día (Date), aplicando las funciones
    de promedio lineal y promedio circular (para WDir_Avg).
    """
    logger.info("Agregando promedios diarios...")
    
    # Aseguramos que existe la columna 'Date'
    lf = lf.with_columns(pl.col('Time').dt.date().alias('Date'))
    
    # Agrupamos por región y fecha
    aggs = [
        _mean_if_valid("Temp_Avg"),
        _mean_if_valid("WSpeed_Avg"),
        _mean_if_valid("WSpeed_Max"),
        _mean_if_valid("Rain_Tot"),
        _mean_if_valid("Press_Avg"),
        _mean_if_valid("Rad_Avg"),
        _mean_if_valid("RH_Avg"),
        _circular_mean_if_valid("WDir_Avg")
    ]
    
    daily_lf = lf.group_by(["region", "Date"]).agg(aggs).sort(["region", "Date"])
    
    return daily_lf
