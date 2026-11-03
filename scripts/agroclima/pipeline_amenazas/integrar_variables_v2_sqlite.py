"""Crea cruce_rendimiento_v2.sqlite: la SQLite del 20 oct + las variables nuevas de la tabla v2 de maíz.

No modifica la SQLite original: la copia a una carpeta nueva y agrega:
  variables_v2         filas de maize_gee_variables_v2.py (píxel × temporada × fase), solo calidad OK
  variables_v2_deriv   por píxel y fase, sobre las temporadas 1981–2016:
                         p_menos_et0_z    estandarizado por píxel y fase (media 0, DE 1)
                         p_menos_et0_pct  percentil empírico dentro del píxel y fase (0–1)
                         sequia_q1        1 si p_menos_et0 < Q1 del píxel y fase (Le Roux et al. 2024, Q1 por píxel)
  vista pares_v2       pares_anuales (ambas alineaciones) + variables_v2 + derivadas, unidas por píxel, temporada y fase
Uso: .venv/Scripts/python.exe integrar_variables_v2_sqlite.py [--csv RUTA] [--destino CARPETA]
"""
import argparse, shutil, sqlite3, time, json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SQL_ORIG = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_anual_ONI_MJO_20261020_183145/cruce_rendimiento.sqlite'
CSV_V2 = ROOT / '03_Resultados/Agroclima/vigente/ejecuciones/maize_variables_v2_GEE_1981_2016/variables_v2_por_fase.csv'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--csv', default=str(CSV_V2))
    ap.add_argument('--destino', default=str(ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_{time.strftime("%Y%m%d_%H%M%S")}'))
    a = ap.parse_args()
    src = Path(a.csv)
    if not src.exists():
        raise SystemExit(f'No existe {src}: el cálculo GEE v2 no ha terminado.')
    out = Path(a.destino); out.mkdir(parents=True, exist_ok=False)
    db = out / 'cruce_rendimiento_v2.sqlite'
    print('Copiando SQLite original (1,4 GB)...', flush=True)
    shutil.copy2(SQL_ORIG, db)

    v = pd.read_csv(src)
    n0 = len(v); v = v[v.quality.eq('OK')].copy()
    v = v.rename(columns={'season_year': 'temporada', 'phase': 'fase'})
    print(f'variables_v2: {len(v):,} filas OK de {n0:,}', flush=True)

    g = v.groupby(['pixel_id', 'fase'])['p_menos_et0']
    v['p_menos_et0_z'] = (v.p_menos_et0 - g.transform('mean')) / g.transform('std')
    v['p_menos_et0_pct'] = g.rank(pct=True)
    v['q1'] = g.transform(lambda s: s.quantile(0.25))
    v['sequia_q1'] = (v.p_menos_et0 < v.q1).astype(int)
    cols = ['pixel_id', 'temporada', 'fase', 'start', 'end', 'dias_ventana', 'coverage_fraction', 'umbral_v2',
            'p_mm', 'et0_mm', 'p_menos_et0', 'edd29', 'rachas_v2', 'dias_racha_v2', 'pct_dias_racha_v2',
            'p_menos_et0_z', 'p_menos_et0_pct', 'q1', 'sequia_q1']

    con = sqlite3.connect(db)
    v[cols].to_sql('variables_v2', con, index=False, if_exists='fail', chunksize=50_000)
    con.execute('create index ix_v2 on variables_v2(pixel_id, temporada, fase)')
    con.execute("""create view pares_v2 as
        select p.*, v.p_mm, v.et0_mm, v.p_menos_et0, v.edd29, v.rachas_v2, v.dias_racha_v2, v.pct_dias_racha_v2,
               v.p_menos_et0_z, v.p_menos_et0_pct, v.sequia_q1, v.umbral_v2
        from pares_anuales p left join variables_v2 v
          on v.pixel_id = p.pixel_id and v.temporada = p.temporada and v.fase = p.fase""")
    con.commit()
    n_par = con.execute('select count(*) from pares_anuales').fetchone()[0]
    n_join = con.execute('select count(*) from pares_v2 where p_mm is not null').fetchone()[0]
    con.close()
    info = dict(sqlite_original=str(SQL_ORIG), csv_v2=str(src), filas_v2_ok=len(v), filas_pares=n_par,
                filas_pares_con_v2=n_join, nota='Q1 por píxel y fase (adaptación de Le Roux et al. 2024, que usa Q1 sobre todas las celdas). ETP Hargreaves.')
    (out / 'procedencia.json').write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(info, ensure_ascii=False, indent=1), flush=True)
    print('TERMINÓ integración:', db, flush=True)


if __name__ == '__main__':
    main()
