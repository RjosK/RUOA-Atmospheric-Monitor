import polars as pl
from pathlib import Path
from config.settings import DATA_RAW_DIR, REGION_MAPPING
from utils.logger import get_logger

logger = get_logger(__name__)

def load_data() -> pl.LazyFrame:
    """
    Carga todos los archivos .parquet en data/raw usando Polars LazyFrames.
    Identifica la región basándose en el nombre del archivo.
    Retorna un único LazyFrame concatenado.
    """
    lazy_frames = []
    
    for file_path in DATA_RAW_DIR.glob('*.parquet'):
        region = 'Unknown'
        for key, region_name in REGION_MAPPING.items():
            if key in file_path.name:
                region = region_name
                break
        
        logger.info(f"Cargando archivo: {file_path.name} -> Región: {region}")
        
        # Leemos con lazy evaluation
        lf = pl.scan_parquet(file_path)
        
        # Añadimos la columna 'region'
        lf = lf.with_columns(pl.lit(region).alias('region'))
        lazy_frames.append(lf)
    
    if not lazy_frames:
        logger.warning("No se encontraron archivos parquet en data/raw")
        return None

    # Concatenamos todos los LazyFrames
    combined_lf = pl.concat(lazy_frames, how="vertical")
    
    # Asegurar el orden de las columnas o tipos si es necesario
    combined_lf = combined_lf.rename({'Time': 'Time'} if 'Time' in combined_lf.columns else {})
    
    return combined_lf
