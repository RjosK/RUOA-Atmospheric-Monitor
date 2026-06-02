# RUOA-Atmospheric-Monitor
Sistema automatizado para el procesamiento, análisis y visualización de datos de monitoreo atmosférico en tiempo real utilizando Python (Polars/Streamlit).
# LAIDEA: Sistema Automatizado de Monitoreo Atmosférico

## Descripción
Este repositorio contiene el framework de procesamiento y visualización diseñado para el **Laboratorio Internacional de Dispositivos Eléctricos Ambientales (LAIDEA)** de la UNAM. 

El sistema automatiza la ingesta, limpieza y análisis de datos de contaminación atmosférica provenientes de estaciones de monitoreo, transformando datos crudos en reportes técnicos procesables a través de un dashboard interactivo desarrollado en **Streamlit**.

## Características Principales
* **Procesamiento de Alto Rendimiento:** Utiliza `Polars` para el manejo eficiente de grandes volúmenes de datos mediante *lazy evaluation*.
* **Automatización ATPAD:** Implementación del *Automatic Technical Processing for Atmospheric Data* (ATPAD) para estandarizar la calidad de los datos.
* **Dashboard Interactivo:** Visualización en tiempo real de contaminantes y tendencias atmosféricas.
* **Modularidad:** Estructura de código diseñada para escalar la adición de nuevas estaciones de monitoreo.

## Stack Tecnológico
* **Lenguaje:** Python 3.10+
* **Procesamiento de Datos:** `Polars`, `Pandas`
* **Frontend/Dashboard:** `Streamlit`
* **Visualización:** `Plotly` / `Matplotlib`

## Estructura del Proyecto
```text
├── data/           # Datos crudos y procesados
├── processors/     # Lógica central (ATPAD)
├── app.py          # Dashboard de Streamlit
├── config/         # Archivos de configuración y constantes
├── requirements.txt
└── README.md
