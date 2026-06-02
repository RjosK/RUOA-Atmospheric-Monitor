import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import math
from utils.helpers import fig_to_base64

# Estilo global
plt.rcParams.update({'figure.autolayout': True})

def generate_trends_plot(df):
    """Genera la gráfica de evolución temporal para temperatura y radiación."""
    fig, ax1 = plt.subplots(figsize=(11, 4.2))
    
    # Aseguramos que la fecha es datetime de pandas
    ax1.plot(df['Date'], df['Temp_MA7'], color='#d32f2f', linewidth=2)
    ax1.set_ylabel('Temperatura Promedio (°C)', color='#d32f2f')
    
    ax2 = ax1.twinx()
    ax2.plot(df['Date'], df['Rad_MA7'], color='#fbc02d', linewidth=1.5, linestyle='--')
    ax2.set_ylabel('Radiación Promedio (W/m²)', color='#fbc02d')
    
    ax1.set_title('Evolución Temporal: Temperatura y Radiación Solar (Media Móvil 7 Días)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    fig.autofmt_xdate(rotation=45)
    
    return fig_to_base64(fig)

def generate_scatter_plot(df):
    """Genera la regresión lineal entre Temperatura y Humedad Relativa."""
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.regplot(data=df, x="Temp_Avg", y="RH_Avg", color="#1976d2", ax=ax, scatter_kws={'alpha': 0.4, 's':15})
    ax.set_title('Dinámica Atmosférica: Temp vs HR')
    ax.set_xlabel('Temperatura Promedio Diaria (°C)')
    ax.set_ylabel('Humedad Relativa Diaria (%)')
    return fig_to_base64(fig)

def generate_histograms_panel(df):
    """Genera el panel de histogramas."""
    no_column = ['Date', 'Time', 'region', 'Temp_MA7', 'Rad_MA7']
    parameters = [col for col in df.columns if col not in no_column and not df[col].isna().all()]
    
    if not parameters:
        return ""
        
    n_cols = 2
    n_rows = math.ceil(len(parameters)/n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(11, 3.2 * n_rows))
    
    axes_flat = axes.flatten()
    for i, param in enumerate(parameters):
        sns.histplot(data=df, x=param, kde=True, ax=axes_flat[i], color='#2b5c8f', alpha=0.7)
        axes_flat[i].set_title(f'Distribución de {param}', fontsize=10)
        axes_flat[i].set_xlabel('')
        axes_flat[i].set_ylabel('')
        
    for j in range(len(parameters), len(axes_flat)):
        fig.delaxes(axes_flat[j])
        
    fig.tight_layout()
    return fig_to_base64(fig)
