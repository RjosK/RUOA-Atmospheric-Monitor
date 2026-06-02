from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = BASE_DIR / 'data' / 'raw'
DATA_OUT_DIR = BASE_DIR / 'data' / 'output'

# Region mappings (filename keyword to region name)
REGION_MAPPING = {
    'MORE': 'Morelia',
    'SLLO': 'Saltillo',
    'AGSC': 'Aguascalientes'
}

# Z-score thresholds for validation
VALIDATION_THRESHOLDS = {
    'Temp_Avg': (-3, 3),
    'WSpeed_Avg': (-4, 4),
    'Press_Avg': (-3, 3)
}

# Value boundaries
BOUNDARIES = {
    'WSpeed_Max_min': 0,
    # WSpeed_Max_max is dynamically calculated as the 98th percentile
    'Rain_Tot_min': 0,
    'Rad_Avg_min': 0.001,
    'RH_Avg': (1, 99),
    'WDir_Avg': (0.001, 359.999)
}

# Dashboard & Report Settings
REPORT_TITLE = 'Análisis Climatológico Estructurado (RUOA)'
