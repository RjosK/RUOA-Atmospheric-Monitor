from pathlib import Path
from utils.logger import get_logger
from reports.visualizations import generate_trends_plot, generate_scatter_plot, generate_histograms_panel

logger = get_logger(__name__)

def generate_html_report(df, station_name, output_path: Path):
    """
    Toma un DataFrame (Pandas) ya filtrado por estación y procesado,
    genera las gráficas en base64 y crea el documento HTML.
    """
    logger.info(f"Generando reporte HTML para: {station_name}")
    
    start_date = df['Date'].min()
    end_date = df['Date'].max()
    
    # Métricas Clave
    metrics = {
        'station': station_name,
        'start': start_date.strftime('%d/%m/%Y') if not type(start_date) == str else start_date,
        'end': end_date.strftime('%d/%m/%Y') if not type(end_date) == str else end_date,
        'total_days': len(df),
        'temp_avg': df['Temp_Avg'].mean(),
        'temp_max': df['Temp_Avg'].max(),
        'temp_min': df['Temp_Avg'].min(),
        'rh_avg': df['RH_Avg'].mean(),
        'rain_tot': df['Rain_Tot'].sum() if 'Rain_Tot' in df.columns else 0.0,
    }
    
    # Calcular promedios móviles para gráficas
    df['Temp_MA7'] = df['Temp_Avg'].rolling(window=7, min_periods=1).mean()
    df['Rad_MA7'] = df['Rad_Avg'].rolling(window=7, min_periods=1).mean()
    
    img_trends = generate_trends_plot(df)
    img_joint = generate_scatter_plot(df)
    img_hist = generate_histograms_panel(df)
    
    html_template = f"""<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte RUOA - {metrics['station']}</title>
        <style>
            :root {{ --ancho-carta: 21.59cm; --alto-carta: 27.94cm; }}
            body {{ font-family: 'Segoe UI', Arial, sans-serif; background-color: #525659; margin: 0; padding: 20px 0; display: flex; flex-direction: column; align-items: center; color: #2d3748; }}
            .hoja-carta {{ width: var(--ancho-carta); min-height: var(--alto-carta); background: white; padding: 1.5cm 2cm; margin-bottom: 20px; box-sizing: border-box; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }}
            .header {{ background-color: #1e3d59; color: white; padding: 20px; border-radius: 4px; margin-bottom: 20px; }}
            .header h1 {{ margin: 0 0 5px 0; font-size: 20px; }}
            .header p {{ color: #ff6e40; font-weight: bold; margin: 0; font-size: 12px; }}
            h2 {{ color: #1e3d59; border-left: 5px solid #ff6e40; padding-left: 10px; margin-top: 20px; font-size: 15px; page-break-after: avoid; }}
            p {{ text-align: justify; font-size: 12px; line-height: 1.5; margin: 5px 0 15px 0; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 6px 10px; border: 1px solid #e2e8f0; font-size: 12px; text-align: left; }}
            th {{ background-color: #1e3d59; color: white; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            .img-box {{ text-align: center; margin: 15px 0; page-break-inside: avoid; }}
            .img-box img {{ max-width: 100%; height: auto; }}
            .caption {{ font-size: 10px; color: #4a5568; font-style: italic; margin-top: 5px; }}
            @media print {{
                @page {{ size: letter; margin: 0; }}
                body {{ background-color: white; margin: 0; padding: 0; display: block; }}
                .hoja-carta {{ box-shadow: none; margin: 0; width: 100%; padding: 1.5cm 2cm; }}
                .header, th {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            }}
        </style>
    </head>
    <body>
        <div class="hoja-carta">
            <div class="header">
                <h1>Análisis Climatológico Estructurado (RUOA)</h1>
                <p>Estación: {metrics['station']} | Periodo: {metrics['start']} al {metrics['end']}</p>
            </div>
            
            <h2>1. Resumen Ejecutivo de Métricas Ambientales</h2>
            <p>Este reporte ejecutivo resume las condiciones meteorológicas clave procesadas de manera reproducible mediante Polars.</p>
            <table>
                <tr><th>Días Analizados</th><td>{metrics['total_days']}</td><th>Temp Media</th><td>{metrics['temp_avg']:.2f} °C</td></tr>
                <tr><th>Temp Máxima</th><td>{metrics['temp_max']:.2f} °C</td><th>Temp Mínima</th><td>{metrics['temp_min']:.2f} °C</td></tr>
                <tr><th>Humedad Relativa</th><td>{metrics['rh_avg']:.2f} %</td><th>Precipitación</th><td>{metrics['rain_tot']:.2f} mm</td></tr>
            </table>

            <h2>2. Evolución Temporal Estacional</h2>
            <div class="img-box">
                <img src="{img_trends}">
                <div class="caption">Figura 1. Comportamiento interanual de la temperatura y radiación con filtro de media móvil.</div>
            </div>

            <h2>3. Interacción Dinámica y Distribución Estadística</h2>
            <div class="img-box">
                <img src="{img_joint}" style="max-width:60%;">
                <div class="caption">Figura 2. Correlación y dispersión bivariada entre temperatura y humedad.</div>
            </div>
            
            <div class="img-box">
                <img src="{img_hist}">
                <div class="caption">Figura 3. Histogramas generales de frecuencia para los parámetros de la estación.</div>
            </div>
        </div>
    </body>
    </html>"""
    
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(html_template)
    
    logger.info(f"✅ Reporte guardado en: {output_path}")
