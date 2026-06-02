import polars as pl
from utils.logger import get_logger

logger = get_logger(__name__)

def clean_data(lf: pl.LazyFrame) -> pl.LazyFrame:
    """
    Realiza la limpieza de datos usando validaciones de z-score y límites absolutos,
    basado íntegramente en expresiones diferidas de Polars.
    """
    logger.info("Aplicando reglas de validación y limpieza...")
    
    # 1. Calcular Z-scores y Cuantiles usando Window Functions
    lf = lf.with_columns([
        ((pl.col("Temp_Avg") - pl.col("Temp_Avg").mean().over("region")) / pl.col("Temp_Avg").std().over("region")).alias("temp_zvalue"),
        ((pl.col("WSpeed_Avg") - pl.col("WSpeed_Avg").mean().over("region")) / pl.col("WSpeed_Avg").std().over("region")).alias("wspeed_zvalue"),
        ((pl.col("Press_Avg") - pl.col("Press_Avg").mean().over("region")) / pl.col("Press_Avg").std().over("region")).alias("press_zvalue"),
        pl.col("WSpeed_Max").quantile(0.98).over("region").alias("WSpeed_Max_qh")
    ])

    # 2. Aplicar condiciones lógicas para filtrar los outliers reemplazándolos con NULL
    lf = lf.with_columns([
        pl.when(pl.col("temp_zvalue").is_between(-3, 3) | pl.col("Temp_Avg").is_null())
          .then(pl.col("Temp_Avg")).otherwise(None).alias("Temp_Avg"),
          
        pl.when(pl.col("wspeed_zvalue").is_between(-4, 4) | pl.col("WSpeed_Avg").is_null())
          .then(pl.col("WSpeed_Avg")).otherwise(None).alias("WSpeed_Avg"),
          
        pl.when((pl.col("WSpeed_Max").is_between(0, pl.col("WSpeed_Max_qh"))) | pl.col("WSpeed_Max").is_null())
          .then(pl.col("WSpeed_Max")).otherwise(None).alias("WSpeed_Max"),
          
        pl.when((pl.col("Rain_Tot") >= 0) | pl.col("Rain_Tot").is_null())
          .then(pl.col("Rain_Tot")).otherwise(None).alias("Rain_Tot"),
          
        pl.when(pl.col("press_zvalue").is_between(-3, 3) | pl.col("Press_Avg").is_null())
          .then(pl.col("Press_Avg")).otherwise(None).alias("Press_Avg"),
          
        pl.when((pl.col("Rad_Avg") > 0.001) | pl.col("Rad_Avg").is_null())
          .then(pl.col("Rad_Avg")).otherwise(None).alias("Rad_Avg"),
          
        pl.when(pl.col("RH_Avg").is_between(1, 99) | pl.col("RH_Avg").is_null())
          .then(pl.col("RH_Avg")).otherwise(None).alias("RH_Avg"),
          
        pl.when(pl.col("WDir_Avg").is_between(0.001, 359.999) | pl.col("WDir_Avg").is_null())
          .then(pl.col("WDir_Avg")).otherwise(None).alias("WDir_Avg")
    ])

    # 3. Seleccionar solo las columnas de interés
    columns_to_keep = [
        'Time', 'region', 'Temp_Avg', 'WSpeed_Avg', 'WSpeed_Max', 
        'Rain_Tot', 'Press_Avg', 'Rad_Avg', 'RH_Avg', 'WDir_Avg'
    ]
    
    # Check if all columns are available, some datasets might lack some (e.g., Rain_Tot).
    # We will use pl.col() to keep only existing.
    lf = lf.select([pl.col(c) for c in columns_to_keep])
    
    return lf
