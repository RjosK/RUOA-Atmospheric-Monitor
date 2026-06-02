import datetime
from pathlib import Path
from config.settings import DATA_OUT_DIR
from processors.loader import load_data
from processors.cleaner import clean_data
from processors.aggregator import aggregate_daily
from reports.generator import generate_html_report
from utils.logger import get_logger

logger = get_logger("LAIDEA_Pipeline")

def main():
    logger.info("Iniciando pipeline de procesamiento LAIDEA...")
    
    # 1. Cargar datos (Lazy)
    raw_lf = load_data()
    if raw_lf is None:
        logger.error("No hay datos para procesar. Saliendo.")
        return
        
    # 2. Limpieza de datos (Lazy)
    clean_lf = clean_data(raw_lf)
    
    # 3. Agregación temporal (Lazy)
    daily_lf = aggregate_daily(clean_lf)
    
    # 4. Ejecutar el grafo lógico (Collect)
    logger.info("Evaluando grafo lógico de Polars (Collect)...")
    final_df = daily_lf.collect()
    
    logger.info(f"Procesamiento completado. Total registros diarios: {len(final_df)}")
    
    # 5. Generación de Reportes
    # Separar por región usando Pandas para compatibilidad con Matplotlib/Seaborn
    final_pandas = final_df.to_pandas()
    
    regions = final_pandas['region'].unique()
    for region in regions:
        region_df = final_pandas[final_pandas['region'] == region]
        output_file = DATA_OUT_DIR / f"Reporte_{region}_{datetime.date.today().strftime('%Y%m%d')}.html"
        
        # Generar reporte HTML
        generate_html_report(region_df, region, output_file)
        
    logger.info("Pipeline finalizado con éxito.")

if __name__ == "__main__":
    main()
