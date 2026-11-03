"""Abrir en terminal: python -i abrir_base_terminal.py

df contiene las primeras 10 filas. La base completa se consulta con conexion.
"""
from pathlib import Path
import sqlite3
import pandas as pd

ruta = Path(
    'C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/rendimiento/'
    'cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite'
)
tabla = 'pares_anuales'

if not ruta.is_file():
    raise FileNotFoundError(ruta)

# Solo lectura. No cargar los millones de filas en memoria.
conexion = sqlite3.connect(ruta.as_uri() + '?mode=ro', uri=True)
df = pd.read_sql_query(f'SELECT * FROM {tabla} LIMIT 10', conexion)
n_filas = conexion.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]
forma_base = (n_filas, len(df.columns))

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 180)
pd.set_option('display.expand_frame_repr', True)

print(f'\nBase: {ruta}')
print(f'Tabla: {tabla}')
print(f'Forma de la tabla completa: {forma_base} (filas, columnas)')
print(f'Forma de df: {df.shape} (solo las primeras 10 filas)')
print('\nPRIMERAS 10 FILAS:\n')
print(df)
print('\nCOLUMNAS:\n')
print(df.columns.tolist())
print('''
Para explorar en la terminal interactiva:

    forma_base                 # dimensiones de la tabla completa
    df.shape                   # dimensiones de la muestra
    df.head(10)                 # primeras 10 filas
    df.columns                 # nombres de las columnas
    df.dtypes                  # tipos inferidos en estas 10 filas
    df.info()                  # información de la muestra
    df[['pixel_id', 'temporada', 'fase', 'pct_dias_afectados', 'z_rendimiento']]

Para leer otras filas:

    consulta = "SELECT * FROM pares_anuales WHERE fase = 'FLO' LIMIT 100"
    df_flo = pd.read_sql_query(consulta, conexion)

Al terminar:

    conexion.close()
    exit()
''')
