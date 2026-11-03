"""Cadena de correlaciones de maíz, una tras otra, para tabular y estudiar antes de decidir.

Paso 1  ONI (ponderado por la ventana de cada fase) vs frecuencia de amenaza, por píxel y fase.
Paso 2  Frecuencia de amenaza por fase vs rendimiento sin tendencia (same-label y maturity-year).
Paso 3  ONI por fase vs rendimiento sin tendencia (same-label).
Paso 4  Cadena: píxeles donde ONI→amenaza y amenaza→rendimiento son significativos tras FDR.
Paso 5  Regresión de las seis fases juntas con validación por bloques (script existente).

Spearman por píxel y fase, mínimo de pares válidos, p-valor por aproximación de Fisher
(z = atanh(r)·sqrt(n-3)) y corrección FDR de Benjamini-Hochberg por prueba, fase y escenario.
Escenarios de píxeles: 'todos' y 'solo_OK' (clase OK de la auditoría de rendimiento).
NO incluye MJO (solo hay seis fases diarias para 10 píxeles) ni SST (resultados aparte).
Uso: .venv/Scripts/python.exe correr_cadena_correlaciones_maiz.py
"""
import math, sys, time, json, subprocess, traceback
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from maize_amenazas_rendimiento import read_yield  # mismo lector ya validado

ROOT = Path('C:/Users/paola/Tesis')
BASE = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente'
SRC_COUNTS = BASE / 'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
SRC_ONI = BASE / 'correlaciones/maize_ONI_v6/pares_oni_amenaza.csv.gz'
SRC_AUDIT = BASE / 'auditoria_rendimiento/maize/auditoria_por_pixel.csv'
SRC_COORDS = ROOT / '02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
SRC_YIELD = ROOT / '02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc'
PHASES = ['EST', 'VEG', 'FLO', 'REP', 'FIL', 'MAT']
MIN_PARES = 20
ALFA = 0.05

STAMP = time.strftime('%Y%m%d_%H%M%S')
OUT = BASE / 'correlaciones' / f'maize_cadena_{STAMP}'
OUT.mkdir(parents=True, exist_ok=False)
LOG = open(OUT / 'registro.log', 'w', encoding='utf-8')
T0 = time.perf_counter()


def log(msg):
    line = f'[{time.perf_counter() - T0:7.0f} s] {msg}'
    print(line, flush=True)
    LOG.write(line + '\n'); LOG.flush()


def spearman_por_grupo(df, keys, x, y):
    """Spearman por grupo (vectorizado). Devuelve n, rho, p (Fisher) por grupo."""
    d = df[keys + [x, y]].dropna()
    g = d.groupby(keys, sort=False)
    d = d.assign(rx=g[x].rank(), ry=g[y].rank())
    d['rx2'], d['ry2'], d['rxy'] = d.rx ** 2, d.ry ** 2, d.rx * d.ry
    s = d.groupby(keys).agg(n=('rx', 'size'), sx=('rx', 'sum'), sy=('ry', 'sum'),
                            sxx=('rx2', 'sum'), syy=('ry2', 'sum'), sxy=('rxy', 'sum')).reset_index()
    cov = s.sxy - s.sx * s.sy / s.n
    vx, vy = s.sxx - s.sx ** 2 / s.n, s.syy - s.sy ** 2 / s.n
    with np.errstate(invalid='ignore', divide='ignore'):
        rho = cov / np.sqrt(vx * vy)
    s['rho'] = rho.where((vx > 1e-12) & (vy > 1e-12))          # varianza cero = sin correlación definible
    s.loc[s.n < MIN_PARES, 'rho'] = np.nan
    r = s.rho.clip(-0.999999, 0.999999)
    z = np.arctanh(r) * np.sqrt((s.n - 3).clip(lower=1))
    s['p'] = [math.erfc(abs(v) / math.sqrt(2)) if np.isfinite(v) else np.nan for v in z]
    return s[keys + ['n', 'rho', 'p']]


def fdr_bh(p):
    p = np.asarray(p, float); q = np.full_like(p, np.nan)
    ok = np.isfinite(p); m = ok.sum()
    if m == 0: return q
    idx = np.argsort(p[ok]); ranked = p[ok][idx] * m / np.arange(1, m + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1].clip(max=1)
    tmp = np.empty(m); tmp[idx] = ranked; q[ok] = tmp
    return q


def resumir(res):
    filas = []
    for (prueba, esc, fase), g in res.groupby(['prueba', 'escenario', 'fase']):
        v = g.dropna(subset=['rho'])
        filas.append(dict(prueba=prueba, escenario=esc, fase=fase, pixeles_con_rho=len(v),
                          rho_mediana=v.rho.median(), rho_p10=v.rho.quantile(.1), rho_p90=v.rho.quantile(.9),
                          pct_sig_p05=100 * (v.p < ALFA).mean() if len(v) else np.nan,
                          pct_sig_FDR=100 * (v.q_fdr < ALFA).mean() if len(v) else np.nan,
                          pct_FDR_negativos=100 * ((v.q_fdr < ALFA) & (v.rho < 0)).mean() if len(v) else np.nan,
                          pct_FDR_positivos=100 * ((v.q_fdr < ALFA) & (v.rho > 0)).mean() if len(v) else np.nan))
    return pd.DataFrame(filas)


def paso(nombre, fn):
    log(f'=== {nombre} ===')
    try:
        r = fn(); log(f'OK: {nombre}'); return r
    except Exception as e:
        log(f'ERROR en {nombre}: {e}\n{traceback.format_exc()}'); return None


# ---------- Carga ----------
def cargar():
    cols = ['pixel_id', 'season_year', 'phase', 'quality', 'mean_count_per_native_cell', 'end']
    partes = []
    for d in pd.read_csv(SRC_COUNTS, usecols=cols, chunksize=200_000):
        d = d[d.season_year.between(1981, 2016)]
        partes.append(d); log(f'  conteos leídos: {sum(map(len, partes)):,}')
    c = pd.concat(partes, ignore_index=True)
    c['freq'] = c.mean_count_per_native_cell.where(c.quality.eq('OK'))   # dato incompleto no es cero
    mat_end = c[c.phase == 'MAT'][['pixel_id', 'season_year', 'end']].copy()
    mat_end['anio_madurez'] = pd.to_datetime(mat_end.end).dt.year
    c = c.merge(mat_end[['pixel_id', 'season_year', 'anio_madurez']], on=['pixel_id', 'season_year'], how='left')
    c = c[['pixel_id', 'season_year', 'phase', 'freq', 'anio_madurez']]

    oni = pd.read_csv(SRC_ONI, usecols=['pixel_id', 'season_year', 'phase', 'oni_phase'])

    coords = pd.read_csv(SRC_COORDS).sort_values('h5_index').reset_index(drop=True)
    years, values, units = read_yield(SRC_YIELD, coords)
    y = pd.DataFrame(values, columns=years)
    y['pixel_id'] = coords.pixel_id.to_numpy()
    y = y.melt(id_vars='pixel_id', var_name='anio', value_name='rend_detrend')
    y['anio'] = y.anio.astype(int)
    log(f'  rendimiento: {y.pixel_id.nunique():,} píxeles, años {y.anio.min()}–{y.anio.max()}, unidades del archivo: {units}')

    audit = pd.read_csv(SRC_AUDIT, usecols=['pixel_id', 'clase'])
    ok = set(audit.loc[audit.clase.eq('OK'), 'pixel_id'])
    global plausibles   # OK + DUDOSO_RATIO_FAO: dudosos frente a FAO pero sin valores inverosímiles
    plausibles = set(audit.loc[audit.clase.isin(['OK', 'DUDOSO_RATIO_FAO']), 'pixel_id'])
    log(f'  conteos: {len(c):,} filas | ONI: {len(oni):,} | píxeles OK en auditoría: {len(ok):,}')
    json.dump(dict(unidades_rendimiento_archivo=str(units), pixeles_ok=len(ok), min_pares=MIN_PARES, alfa=ALFA,
                   fuentes={k: str(v) for k, v in dict(conteos=SRC_COUNTS, oni=SRC_ONI, auditoria=SRC_AUDIT,
                                                        coords=SRC_COORDS, rendimiento=SRC_YIELD).items()}),
              open(OUT / 'procedencia.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return c, oni, y, ok


datos = paso('Carga de datos', cargar)
if datos is None:
    log('No se pudo cargar; se detiene. Revisa registro.log'); sys.exit(1)
c, oni, y, ok = datos
resultados = []


def correr(prueba, df, x, yv):
    for esc, d in [('todos', df), ('solo_OK', df[df.pixel_id.isin(ok)]),
                   ('OK_mas_dudosos', df[df.pixel_id.isin(plausibles)])]:
        s = spearman_por_grupo(d, ['pixel_id', 'phase'], x, yv)
        s['prueba'], s['escenario'] = prueba, esc
        resultados.append(s.rename(columns={'phase': 'fase'}))
        log(f'  {prueba} [{esc}]: {s.rho.notna().sum():,} píxel-fase con correlación definida')


# Paso 1: ONI vs frecuencia de amenaza
paso('Paso 1 ONI vs frecuencia', lambda: correr('ONI~frecuencia',
     c.merge(oni, on=['pixel_id', 'season_year', 'phase']), 'oni_phase', 'freq'))

# Paso 2: frecuencia vs rendimiento, dos convenciones de año
def paso2():
    sl = c.merge(y, left_on=['pixel_id', 'season_year'], right_on=['pixel_id', 'anio'])
    correr('frecuencia~rendimiento|same-label', sl, 'freq', 'rend_detrend')
    my = c.dropna(subset=['anio_madurez']).merge(y, left_on=['pixel_id', 'anio_madurez'], right_on=['pixel_id', 'anio'])
    correr('frecuencia~rendimiento|maturity-year', my, 'freq', 'rend_detrend')
paso('Paso 2 frecuencia vs rendimiento', paso2)

# Paso 3: ONI vs rendimiento
paso('Paso 3 ONI vs rendimiento', lambda: correr('ONI~rendimiento|same-label',
     oni.merge(y, left_on=['pixel_id', 'season_year'], right_on=['pixel_id', 'anio']), 'oni_phase', 'rend_detrend'))


# FDR, tablas y cadena
def tabular():
    res = pd.concat(resultados, ignore_index=True)
    res['q_fdr'] = np.nan
    for _, idx in res.groupby(['prueba', 'escenario', 'fase']).groups.items():
        res.loc[idx, 'q_fdr'] = fdr_bh(res.loc[idx, 'p'])
    res.to_csv(OUT / 'correlaciones_por_pixel_fase.csv', index=False)
    resumen = resumir(res); resumen.to_csv(OUT / 'resumen_por_fase.csv', index=False)
    log('  resumen por fase:\n' + resumen.to_string(index=False, float_format=lambda v: f'{v:.3f}'))
    # Cadena ONI -> amenaza -> rendimiento (same-label)
    a = res[res.prueba == 'ONI~frecuencia'][['pixel_id', 'fase', 'escenario', 'rho', 'q_fdr']]
    b = res[res.prueba == 'frecuencia~rendimiento|same-label'][['pixel_id', 'fase', 'escenario', 'rho', 'q_fdr']]
    cad = a.merge(b, on=['pixel_id', 'fase', 'escenario'], suffixes=('_oni_amenaza', '_amenaza_rend'))
    cad['cadena_FDR'] = (cad.q_fdr_oni_amenaza < ALFA) & (cad.q_fdr_amenaza_rend < ALFA)
    cad['signo_ONI_a_rend'] = np.sign(cad.rho_oni_amenaza * cad.rho_amenaza_rend)
    cad.to_csv(OUT / 'cadena_ONI_amenaza_rendimiento.csv', index=False)
    t = cad.groupby(['escenario', 'fase']).agg(pixeles=('pixel_id', 'size'), cadena_FDR=('cadena_FDR', 'sum')).reset_index()
    t.to_csv(OUT / 'resumen_cadena.csv', index=False)
    log('  cadena ONI→amenaza→rendimiento (píxeles con ambos eslabones FDR<0,05):\n' + t.to_string(index=False))
paso('Paso 4 FDR, tablas y cadena', tabular)

# Paso 5: regresión seis fases (script existente, puede tardar)
def paso5():
    cmd = [sys.executable, str(HERE / 'maize_amenazas_rendimiento.py'), '--year-alignment', 'both']
    with open(OUT / 'paso5_regresion_seis_fases.log', 'w', encoding='utf-8') as fh:
        r = subprocess.run(cmd, cwd=HERE, stdout=fh, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        raise RuntimeError(f'código {r.returncode}; ver paso5_regresion_seis_fases.log')
paso('Paso 5 regresión de las seis fases (maize_amenazas_rendimiento.py)', paso5)

(OUT / 'LEEME.md').write_text(f"""# Cadena de correlaciones de maíz — {STAMP}

Archivos:
- `correlaciones_por_pixel_fase.csv`: una fila por prueba, escenario, píxel y fase (n, rho de Spearman, p, q_fdr).
- `resumen_por_fase.csv`: mediana de rho y % de píxeles significativos (p<0,05 y FDR<0,05) por fase.
- `cadena_ONI_amenaza_rendimiento.csv` y `resumen_cadena.csv`: píxeles donde ONI→amenaza y amenaza→rendimiento son significativos tras FDR.
- `paso5_regresion_seis_fases.log`: salida del script de regresión de seis fases (sus resultados en outputs/agroclima_vigente/rendimiento/maize_seis_fases/).
- `registro.log`, `procedencia.json`.

Cómo leer: rho<0 en frecuencia~rendimiento = más amenaza, menos rendimiento. Mira primero `pct_sig_FDR`, no `pct_sig_p05`:
con miles de pruebas, ~5 % sale significativo por azar. Compara 'todos' vs 'solo_OK' (sin píxeles con rendimientos inverosímiles)
y same-label vs maturity-year; no elijas la convención por la que dé mejor resultado.

No incluido: MJO (falta el cálculo diario de seis fases para todos los píxeles) y SST (resultados previos aparte).
Asociación no es causalidad ni daño demostrado. p-valor por aproximación de Fisher; las temporadas pueden tener autocorrelación.
""", encoding='utf-8')
log(f'TERMINÓ. Resultados en {OUT}')
