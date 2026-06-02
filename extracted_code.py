#importing libraries
import pandas as pd # Data manipulation library
import numpy as np # Numerical operations library
import datetime # Library for handling date and time data
import math 
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from windrose import WindroseAxes

# Estilo profesional para el PDF
plt.rcParams.update({'figure.autolayout': True})

# ---

#importing data
mor_data_raw = pd.read_parquet('RUOA_MORE_1h_Meteo_2024.parquet').reset_index(drop=True)
sal_data_raw = pd.read_parquet('RUOA_SLLO_1h_Meteo_2024.parquet').reset_index(drop=True)
agu_data_raw = pd.read_parquet('RUOA_AGSC_1h_Meteo_2024.parquet').reset_index(drop=True)

# ---

# Filling gaps in timestamp for each DataFrame and creating a complete time series for each region

dfs = [mor_data_raw, sal_data_raw, agu_data_raw] # Create a list of the three DataFrames to loop through them

for i in range(3): # Loop through each DataFrame in the list
    full_range = pd.date_range(start=dfs[i]['Time'].min(), end=dfs[i]['Time'].max(), freq='h')
    dfs[i]= dfs[i].set_index('Time')# Set the 'Time' column as the index of the DataFrame
    dfs[i]= dfs[i].reindex(full_range) # Reindex the DataFrame to include all timestamps in the full range

# Add a new column 'region' to each DataFrame and assign the corresponding region name
dfs[0]['region'] = 'Morelia' 
dfs[1]['region'] = 'Saltillo'
dfs[2]['region'] = 'Aguascalientes'

# Concatenate the three DataFrames into a single DataFrame and reset the index to have a clean 'Time' column
raw = pd.concat(dfs).reset_index(drop=False)
raw = raw.rename(columns={'index': 'Time'})
# All regions together
raw.head(10) # Display the first 10 rows of the combined DataFrame to verify the results

# ---

# make the calculations for the 98th and 99th percentiles of the 'WSpeed_Avg' and 'WSpeed_Max' columns, respectively, for each region

def q98(arr):
    return arr.quantile(0.98)

def q99(arr):
    return arr.quantile(0.99)
# Group the data by 'region' and calculate the required statistics for each group
dft = raw.groupby('region').agg(
    WSpeed_AVG_qh=('WSpeed_Avg', q99),# Calculate the 99th percentile of the 'WSpeed_Avg' column for each region and name it 'WSpeed_AVG_qh'
    WSpeed_Max_qh=('WSpeed_Max', q98), # Calculate the 98th percentile of the 'WSpeed_Max' column for each region and name it 'WSpeed_Max_qh'
    press_avg=('Press_Avg', 'mean'), # Calculate the mean of the 'Press_Avg' column for each region and name it 'press_avg'
    press_std=('Press_Avg', 'std'), # Calculate the standard deviation of the 'Press_Avg' column for each region and name it 'press_std'
    wspeed_avg=('WSpeed_Avg', 'mean'), # Calculate the mean of the 'WSpeed_Avg' column for each region and name it 'wspeed_avg'
wspeed_std=('WSpeed_Avg', 'std'), # Calculate the standard deviation of the 'WSpeed_Avg' column for each region and name it 'wspeed_std'
    temp_avg=('Temp_Avg', 'mean'), # Calculate the mean of the 'Temp_Avg' column for each region and name it 'temp_avg'
    temp_std=('Temp_Avg', 'std') # Calculate the standard deviation of the 'Temp_Avg' column for each region and name it 'temp_std'
).reset_index()

dft # Display the resulting DataFrame with the calculated statistics for each region

# ---

# Perfomm the data cleaning process by merging the original DataFrame with the aggregated statistics and applying validation criteria to identify and handle outliers and invalid values

clean_df = ( 
    raw.merge(dft, on='region', how='left') # Merge the original DataFrame with the aggregated statistics based on the 'region' column
)

# Calculate z-scores for Press_Avg, Temp_Avg, and WSpeed_Avg
clean_df['press_zvalue'] = (clean_df['Press_Avg'] - clean_df['press_avg']) / clean_df['press_std']
clean_df['temp_zvalue'] = (clean_df['Temp_Avg'] - clean_df['temp_avg']) / clean_df['temp_std']
clean_df['wspeed_zvalue'] = (clean_df['WSpeed_Avg'] - clean_df['wspeed_avg']) / clean_df['wspeed_std']

# Apply validation criteria and set invalid values to None
clean_df['Temp_Avg'] = clean_df['Temp_Avg'].where(((clean_df['temp_zvalue'].between(-3, 3)) | (clean_df['Temp_Avg'].isna())), None)
clean_df['WSpeed_Avg'] = clean_df['WSpeed_Avg'].where(((clean_df['wspeed_zvalue'].between(-4, 4)) | (clean_df['WSpeed_Avg'].isna())), None)
clean_df['WSpeed_Max'] = clean_df['WSpeed_Max'].where(((clean_df['WSpeed_Max'].between(0, clean_df['WSpeed_Max_qh'])) | (clean_df['WSpeed_Max'].isna())), None)
clean_df['Rain_Tot'] = clean_df['Rain_Tot'].where(((clean_df['Rain_Tot'] >= 0) | (clean_df['Rain_Tot'].isna())), None)
clean_df['Press_Avg'] = clean_df['Press_Avg'].where(((clean_df['press_zvalue'].between(-3, 3)) | (clean_df['Press_Avg'].isna())), None)
clean_df['Rad_Avg'] = clean_df['Rad_Avg'].where(((clean_df['Rad_Avg'] > 0.001) | (clean_df['Rad_Avg'].isna())), None)
clean_df['RH_Avg'] = clean_df['RH_Avg'].where(((clean_df['RH_Avg'].between(1, 99)) | (clean_df['RH_Avg'].isna())), None)
clean_df['WDir_Avg'] = clean_df['WDir_Avg'].where(((clean_df['WDir_Avg'].between(0.001, 359.999)) | (clean_df['WDir_Avg'].isna())), None)

# Select and rename columns for the final clean dataset
clean_df = clean_df[['Time', 'region', 'Temp_Avg', 'WSpeed_Avg', 'WSpeed_Max', 'Rain_Tot', 'Press_Avg', 'Rad_Avg', 'RH_Avg', 'WDir_Avg']].copy()
#clean_df.iloc[0:10] # Display the first 24 rows of the clean dataset to verify the results
clean_df 

# ---

# 24 h_average (output: 366 lines) diurnal cycles taking the mean for better representation
h_average = clean_df.copy()
h_average = h_average.assign(Date=h_average['Time'].dt.date)

def calculate_daily_mean(group, is_circular=False):
  valid_count = group.notna().sum()
  if valid_count >= 18:
    if is_circular:
      rad = np.deg2rad(group)
      mean_sin = np.mean(np.sin(rad))
      mean_cos = np.mean(np.cos(rad))
      mean_angle = np.arctan2(mean_sin, mean_cos)
      return np.rad2deg(mean_angle).round(2) % 360
    else:
      return group.mean().round(2)
  return np.nan

daily_mean = h_average.groupby(['region', 'Date']).apply(
  lambda g: pd.Series({
    'Temp_Avg': calculate_daily_mean(g['Temp_Avg']),
    'WSpeed_AVG': calculate_daily_mean(g['WSpeed_Avg']),
    'WSpeed_Max': calculate_daily_mean(g['WSpeed_Max']),
    'Rain_Tot': calculate_daily_mean(g['Rain_Tot']),
    'Press_Avg': calculate_daily_mean(g['Press_Avg']),
    'Rad_Avg': calculate_daily_mean(g['Rad_Avg']),
    'RH_Avg': calculate_daily_mean(g['RH_Avg']),
    'WDir_AVG': calculate_daily_mean(g['WDir_Avg'], is_circular=True),
  }), include_groups=False
).reset_index()

# ---

daily_mean

# ---

# 1. Ajustar las fechas (como son datos diarios, solo necesitamos Año-Mes-Día)
# Convertimos a datetime.date para que coincida con el formato de tu columna 'Date'
start_date = pd.to_datetime('2024-01-01').date() 
end_date = pd.to_datetime('2024-12-31').date() 

# 2. Ordenar usando la columna 'Date' en lugar de 'Time'
daily_mean_sorted = daily_mean.sort_values(by='Date')

# 3. Filtrar por región
region_aguascalientes = daily_mean.loc[daily_mean['region'] == 'Aguascalientes']

# 4. Filtrar por periodo (usando 'Date')
periodos_use = (daily_mean['Date'] >= start_date) & (daily_mean['Date'] <= end_date)
periodo = daily_mean.loc[periodos_use]

# Opcional: Combinar ambos filtros (Región + Fechas) de forma directa
datos_finales = daily_mean.loc[(daily_mean['region'] == 'Aguascalientes') & periodos_use]

# Mostrar los primeros 10 resultados para verificar
datos_finales

# ---

# 1. Asegurar que datos_finales es independiente para evitar alertas de Pandas
datos_finales = datos_finales.copy()

# 2. Calcular promedios móviles (Corregido a 7 días)
datos_finales['Temp_MA7'] = datos_finales['Temp_Avg'].rolling(window=7, min_periods=1).mean()
datos_finales['Rad_MA7'] = datos_finales['Rad_Avg'].rolling(window=7, min_periods=1).mean()

fig, ax1 = plt.subplots(figsize=(12, 5))

# Eje principal: Temperatura (Puntos pálidos diarios + Línea sólida de tendencia)
color_temp = '#d32f2f'
ax1.set_ylabel('Temperatura Promedio (°C)', color=color_temp) 
ax1.scatter(datos_finales['Date'], datos_finales['Temp_Avg'], color=color_temp, alpha=0.2, s=15) 
ax1.plot(datos_finales['Date'], datos_finales['Temp_MA7'], color=color_temp, linewidth=2.5) # Agregué linewidth
ax1.tick_params(axis='y', labelcolor=color_temp, labelsize=12)

# Ajuste de fechas en el eje X (Corregido el error de datetime)
ax1.set_xlim(start_date, end_date) # start_date y end_date ya son objetos de fecha
ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=1)) # Muestra un tick cada mes
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y')) 

# Eje secundario gemelo: Radiación
ax2 = ax1.twinx()
color_rad = '#fbc02d'
ax2.set_ylabel('Radiación Promedio (W/m²)', color=color_rad)
ax2.plot(datos_finales['Date'], datos_finales['Rad_MA7'], color=color_rad, linewidth=2, linestyle='--', label='Rad (Media 7d)') 
ax2.tick_params(axis='y', labelcolor=color_rad, labelsize=12, labelrotation=0)

# Rotación de etiquetas a 90 grados
fig.autofmt_xdate(rotation=90) 

plt.title('Tendencias Estacionales: Temperatura y Radiación Solar (Media Móvil 7 Días)', pad=15, fontsize=16)
plt.tight_layout() # Asegura que los márgenes se adapten bien
plt.show()

# fig.savefig("serie_tiempo_2016.png", dpi=300)

# ---

# Gráfico de dispersión con regresión lineal ajustada
g = sns.jointplot(
    data=datos_finales,
    x="Temp_Avg",
    y="RH_Avg",
    kind="reg", 
    color="#1976d2",
    height=6,
    scatter_kws={'alpha': 0.6, 'edgecolor': 'w'},
    line_kws={'color': '#d32f2f', 'linewidth': 2}
)

g.set_axis_labels('Temperatura Promedio Diaria (°C)', 'Humedad Relativa Diaria (%)', fontsize=12)
plt.suptitle('Dinámica Atmosférica: Efecto de la Temperatura sobre la Humedad', y=1.03, fontsize=14)
plt.show()
# g.savefig("dispersion_humedad.png", dpi=300)

# ---

fig = plt.figure(figsize=(7, 7))
ax = WindroseAxes.from_ax(fig=fig)

# El parámetro normed=True muestra frecuencias relativas (%)
ax.bar(
    datos_finales['WDir_AVG'], 
    datos_finales['WSpeed_AVG'], 
    normed=True, 
    opening=0.8, 
    edgecolor='white',
    cmap=plt.cm.viridis # Mapa de colores amigable para publicaciones
)

ax.set_title('Rosa de Vientos Climatológica\n(Frecuencia Diaria)', pad=15, fontsize=14)
ax.set_legend(title='Velocidad Promedio\n(m/s)', loc=(1.05, 0))
plt.show()
# fig.savefig("rosa_vientos.png", dpi=300, bbox_inches="tight")

# ---

fig, ax1 = plt.subplots(figsize=(10, 5))

# Eje principal: Precipitación (Barras)
color_rain = "#0703ff"
ax1.set_ylabel('Precipitación Total (mm)', color=color_rain)
# Usamos un ancho de 1 para que las barras diarias queden pegadas
ax1.bar(datos_finales['Date'], datos_finales['Rain_Tot'], color=color_rain, alpha=0.7, width=2.0)
ax1.tick_params(axis='y', labelcolor=color_rain)

# Eje secundario: Temperatura (Línea)
ax2 = ax1.twinx()
color_temp = "#c62828ff"
ax2.set_ylabel('Temperatura Promedio (°C)', color=color_temp)
ax2.plot(datos_finales['Date'], datos_finales['Temp_Avg'], color=color_temp, linewidth=2)
ax2.tick_params(axis='y', labelcolor=color_temp)

# Formato limpio para los meses en el eje X
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
ax1.xaxis.set_major_locator(mdates.MonthLocator())

plt.title('Climograma: Regulación de la Temperatura por Temporada de Lluvias', pad=15)
plt.show()
# fig.savefig("climograma.png", dpi=300)

# ---

no_column = ['Time', 'region', 'Date'] # Columnas que no queremos incluir en los histogramas
parameters = [col for col in datos_finales.columns if col not in no_column]

# Calcular filas dinámicamente (2 columnas fijas)
n_cols = 3
n_rows = math.ceil(len(parameters) / n_cols)

# Crear el panel de subplots
fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4 * n_rows))
axes = axes.flatten() # Aplanar el arreglo para iterar fácilmente con un solo índice

for i, parameter in enumerate(parameters):
    sns.histplot(data=datos_finales, x=parameter, kde=True, bins=30, ax=axes[i], color='#2b5c8f')
    axes[i].set_title(f'{parameter}', fontsize=12)
    axes[i].set_xlabel('')
    axes[i].set_ylabel('Frecuencia')

# Borrar los subplots vacíos si el número de parámetros es impar
for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

# Título general para todo el panel
plt.suptitle(f'Distribución Meteorológica ({start_date} a {end_date})', fontsize=16, y=1.02)
plt.tight_layout()
plt.show()
# fig.savefig("panel_histogramas_meteo.png", bbox_inches='tight', dpi=300)

# ---

# Reutilizamos los mismos 'parameters', 'n_cols' y 'n_rows' del bloque anterior
fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4 * n_rows))
axes = axes.flatten()

for i, parameter in enumerate(parameters):
    # inner='quartile' suele ser más informativo en ciencia de datos que 'box'
    sns.violinplot(data=datos_finales, x='region', y=parameter, inner='quartile', ax=axes[i], palette='Set2')
    axes[i].set_title(f'{parameter}', fontsize=12)
    axes[i].set_xlabel('')
    axes[i].set_ylabel('')

for j in range(i + 1, len(axes)):
    fig.delaxes(axes[j])

plt.suptitle(f'Comparativa Regional por Parámetro ({start_date} a {end_date})', fontsize=16, y=1.02)
plt.tight_layout()
plt.show()

# ---

# Para series de tiempo, es mejor 1 sola columna para que la gráfica sea ancha
n_cols_ts = 1
n_rows_ts = len(parameters)

fig, axes = plt.subplots(n_rows_ts, n_cols_ts, figsize=(14, 3 * n_rows_ts), sharex=True)

# Si solo hay 1 fila, axes no es una lista, así que la forzamos a ser iterable
if n_rows_ts == 1:
    axes = [axes]

for i, parameter in enumerate(parameters):
    sns.lineplot(data=datos_finales, x='Date', y=parameter, hue='region', palette='tab10', ax=axes[i], alpha=0.7)
    axes[i].set_title(f'Serie de Tiempo: {parameter}', loc='left', fontsize=11)
    axes[i].set_ylabel('')
    
    # Solo dejar la leyenda en la primera gráfica para no saturar el panel
    if i == 0:
        axes[i].legend(title='Región', bbox_to_anchor=(1.01, 1), loc='upper left')
    else:
        if axes[i].get_legend():
            axes[i].get_legend().remove()

# Ajustar el eje X solo en la última gráfica del panel
axes[-1].set_xlabel('Fecha / Hora')

plt.suptitle(f'Evolución Temporal de Parámetros Meteorológicos', fontsize=16, y=1.01)
plt.tight_layout()
plt.show()

# ---

import io
import base64
import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

def fig_to_base64(fig):
    """Convierte una figura en Base64 para incrustarla directo en el HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    base64_string = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{base64_string}"

def automatizar_reporte_html_carta(df_entrada, station_name, start_date, end_date, output_filename):
    """Procesa datos, genera gráficas y exporta un documento HTML optimizado para imprimir en tamaño Carta."""
    
    df = df_entrada.copy().sort_values('Date')
    
    # 1. MÉTRICAS CLAVE
    metrics = {
        'temp_avg': df['Temp_Avg'].mean(),
        'temp_max': df['Temp_Avg'].max(),
        'temp_min': df['Temp_Avg'].min(),
        'rh_avg': df['RH_Avg'].mean(),
        'ws_avg': df['WSpeed_AVG'].mean(),
        'ws_max': df['WSpeed_Max'].max(),
        'rain_tot': df['Rain_Tot'].sum() if 'Rain_Tot' in df.columns else 0.0,
        'station': station_name,
        'start': start_date.strftime('%d/%m/%Y'),
        'end': end_date.strftime('%d/%m/%Y'),
        'total_days': len(df)
    }

    # 2. GENERACIÓN DE GRÁFICAS EN MEMORIA
    df['Temp_MA7'] = df['Temp_Avg'].rolling(window=7, min_periods=1).mean()
    df['Rad_MA7'] = df['Rad_Avg'].rolling(window=7, min_periods=1).mean()
    
    # Gráfica 1: Tendencias
    fig1, ax1 = plt.subplots(figsize=(11, 4.2))
    ax1.plot(df['Date'], df['Temp_MA7'], color='#d32f2f', linewidth=2)
    ax1.set_ylabel('Temperatura Promedio (°C)', color='#d32f2f')
    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df['Rad_MA7'], color='#fbc02d', linewidth=1.5, linestyle='--')
    ax2.set_ylabel('Radiación Promedio (W/m²)', color='#fbc02d')
    ax1.set_title('Evolución Temporal: Temperatura y Radiación Solar (Media Móvil 7 Días)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig1.autofmt_xdate(rotation=45)
    img_trends = fig_to_base64(fig1)

    # Gráfica 2: Regresión Temp vs HR
    fig2, ax = plt.subplots(figsize=(6, 4.5))
    sns.regplot(data=df, x="Temp_Avg", y="RH_Avg", color="#1976d2", ax=ax, scatter_kws={'alpha': 0.4, 's':15})
    ax.set_title('Dinámica Atmosférica: Temp vs HR')
    ax.set_xlabel('Temperatura Promedio Diaria (°C)')
    ax.set_ylabel('Humedad Relativa Diaria (%)')
    img_joint = fig_to_base64(fig2)

    # Gráfica 3: Panel de Histogramas
    no_column = ['Date', 'Time', 'region', 'Temp_MA7', 'Rad_MA7']
    parameters = [col for col in df.columns if col not in no_column and not df[col].isna().all()]
    fig3, axes = plt.subplots(math.ceil(len(parameters)/2), 2, figsize=(11, 3.2 * math.ceil(len(parameters)/2)))
    for i, param in enumerate(parameters):
        sns.histplot(data=df, x=param, kde=True, ax=axes.flatten()[i], color='#2b5c8f', alpha=0.7)
        axes.flatten()[i].set_title(f'Distribución de {param}', fontsize=10)
        axes.flatten()[i].set_xlabel('')
        axes.flatten()[i].set_ylabel('')
    for j in range(i + 1, len(axes.flatten())):
        fig3.delaxes(axes.flatten()[j])
    fig3.tight_layout()
    img_hist = fig_to_base64(fig3)

    # 3. CONSTRUCCIÓN DEL HTML (Visor Estilo PDF - Tamaño Carta Estricto)
    html_template = f"""<!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Reporte RUOA - {metrics['station']}</title>
        <style>
            /* Variables físicas exactas para Tamaño Carta */
            :root {{
                --ancho-carta: 21.59cm;
                --alto-carta: 27.94cm;
            }}
            
            body {{ 
                font-family: 'Segoe UI', Arial, sans-serif; 
                background-color: #525659; /* Fondo gris oscuro tipo visor de PDF */
                margin: 0; 
                padding: 20px 0; 
                display: flex;
                flex-direction: column;
                align-items: center;
                color: #2d3748;
            }}
            
            /* El contenedor ahora es una hoja de papel física */
            .hoja-carta {{ 
                width: var(--ancho-carta); 
                min-height: var(--alto-carta); 
                background: white; 
                padding: 1.5cm 2cm; /* Márgenes físicos internos */
                margin-bottom: 20px;
                box-sizing: border-box;
                box-shadow: 0 4px 10px rgba(0,0,0,0.5); /* Sombra de documento */
            }}
            
            .header {{ 
                background-color: #1e3d59; 
                color: white; 
                padding: 20px; 
                border-radius: 4px; 
                margin-bottom: 20px; 
            }}
            .header h1 {{ margin: 0 0 5px 0; font-size: 20px; }}
            .header p {{ color: #ff6e40; font-weight: bold; margin: 0; font-size: 12px; }}
            
            h2 {{ 
                color: #1e3d59; 
                border-left: 5px solid #ff6e40; 
                padding-left: 10px; 
                margin-top: 20px; 
                font-size: 15px;
                page-break-after: avoid;
            }}
            
            p {{ text-align: justify; font-size: 12px; line-height: 1.5; margin: 5px 0 15px 0; }}
            
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
            th, td {{ padding: 6px 10px; border: 1px solid #e2e8f0; font-size: 12px; text-align: left; }}
            th {{ background-color: #1e3d59; color: white; }}
            tr:nth-child(even) {{ background-color: #f8fafc; }}
            
            .img-box {{ 
                text-align: center; 
                margin: 15px 0; 
                page-break-inside: avoid;
            }}
            .img-box img {{ max-width: 100%; height: auto; }}
            .caption {{ font-size: 10px; color: #4a5568; font-style: italic; margin-top: 5px; }}

            /* Reglas estrictas de impresión */
            @media print {{
                @page {{ 
                    size: letter; 
                    margin: 0; /* Anulamos el margen del navegador porque la hoja ya lo tiene */
                }}
                body {{ 
                    background-color: white; 
                    margin: 0; 
                    padding: 0; 
                    display: block;
                }}
                .hoja-carta {{ 
                    box-shadow: none; 
                    margin: 0; 
                    width: 100%;
                    padding: 1.5cm 2cm; /* Respetamos el margen interno al imprimir */
                }}
                .header, th {{ 
                    -webkit-print-color-adjust: exact; 
                    print-color-adjust: exact; 
                }}
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
            <p>Este reporte ejecutivo resume las condiciones meteorológicas clave procesadas de manera reproducible.</p>
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

    # 4. EXPORTAR ARCHIVO
    with open(output_filename, "w", encoding="utf-8") as file:
        file.write(html_template)
    
    print(f"✅ HTML listo para impresión Tamaño Carta guardado como: {output_filename}")


# ---

# Ejecución:
automatizar_reporte_html_carta(datos_finales, "Aguascalientes", start_date, end_date, "Reporte_Final.html")

# ---



# ---

