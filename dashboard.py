import streamlit as st
import pandas as pd
from pathlib import Path
from processors.loader import load_data
from processors.cleaner import clean_data
from processors.aggregator import aggregate_daily
import altair as alt

# Configuración de página
st.set_page_config(page_title="Dashboard LAIDEA - RUOA", layout="wide")

st.title("🌦️ Dashboard Interactivo LAIDEA")
st.markdown("Plataforma automatizada para el análisis de la red RUOA.")

@st.cache_data
def process_data():
    """Ejecuta el pipeline de Polars y cachea el resultado en Pandas"""
    raw_lf = load_data()
    if raw_lf is None:
        return None
        
    clean_lf = clean_data(raw_lf)
    daily_lf = aggregate_daily(clean_lf)
    
    # Collect execution and convert to Pandas for Streamlit
    return daily_lf.collect().to_pandas()

df = process_data()

if df is not None:
    # Sidebar
    st.sidebar.header("Filtros")
    
    regiones = df['region'].unique()
    region_seleccionada = st.sidebar.selectbox("Selecciona una Estación:", regiones)
    
    df_filtrado = df[df['region'] == region_seleccionada].copy()
    
    if not df_filtrado.empty:
        # Métricas Clave
        st.subheader(f"Métricas Resumen - {region_seleccionada}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Temperatura Media", f"{df_filtrado['Temp_Avg'].mean():.1f} °C")
        col2.metric("Humedad Relativa Media", f"{df_filtrado['RH_Avg'].mean():.1f} %")
        col3.metric("Precipitación Total", f"{df_filtrado['Rain_Tot'].sum():.1f} mm")
        col4.metric("Días Procesados", len(df_filtrado))
        
        # Gráfica de Tendencias (Interactiva con st.line_chart)
        st.subheader("Tendencias de Temperatura")
        df_filtrado['Temp_MA7'] = df_filtrado['Temp_Avg'].rolling(7).mean()
        
        # Streamlit nativo
        chart_data = df_filtrado.set_index('Date')[['Temp_Avg', 'Temp_MA7']]
        st.line_chart(chart_data)

        # --- NUEVA SECCIÓN INTERACTIVA ---
        st.subheader("Dinámica Atmosférica (Interactiva)")
        
        # 1. Crear los puntos de dispersión
        puntos = alt.Chart(df_filtrado).mark_circle(opacity=0.5, size=60, color="#1976d2").encode(
            x=alt.X('Temp_Avg', title='Temperatura Promedio Diaria (°C)'),
            y=alt.Y('RH_Avg', title='Humedad Relativa Diaria (%)'),
            # El "tooltip" es lo que hace la magia: decide qué datos mostrar al pasar el mouse
            tooltip=['Date', 'Temp_Avg', 'RH_Avg']
        )
        
        # 2. Calcular y dibujar la línea de regresión (tendencia) automáticamente
        linea_tendencia = puntos.transform_regression(
            'Temp_Avg', 'RH_Avg'
        ).mark_line(color="#d32f2f", size=2)
        
        # 3. Renderizar la suma de ambas capas (puntos + línea) en Streamlit
        st.altair_chart(puntos + linea_tendencia, use_container_width=True)
        # ---------------------------------
        
        st.subheader("Explorador de Datos Crudos Agregados")
        st.dataframe(df_filtrado)
else:
    st.error("No se encontraron archivos .parquet en la carpeta `data/raw`")

st.sidebar.markdown("---")
st.sidebar.markdown("**Instrucciones:** Para actualizar los datos, simplemente arrastra los nuevos archivos `.parquet` a la carpeta `data/raw` y recarga esta página.")
