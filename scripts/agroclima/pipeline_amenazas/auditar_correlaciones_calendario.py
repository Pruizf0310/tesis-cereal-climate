"""Auditoría de la corrida correlaciones_calendario_maiz.py (solo lectura). Escribe auditoria.md en la carpeta de la corrida.

Revisa: (1) Y = z_rendimiento, (2) amenazas (rangos, umbrales, faltantes, píxeles sin variación), (3) ONI mensual contra la
tabla oficial, (4) MJO (fracciones suman 1, exclusión 2014–2016), (5) correspondencia temporada → año de cosecha,
(6) estabilidad del calendario por píxel, (7) autocorrelación del rendimiento, (8) Pearson vs Spearman,
(9) multiplicidad de la significancia de campo.
Uso: .venv/Scripts/python.exe auditar_correlaciones_calendario.py --corrida RUTA_CARPETA
"""
import argparse, re, sqlite3
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path('C:/Users/paola/Tesis')
SQL = ROOT / '03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_20261024_184932/cruce_rendimiento_v2.sqlite'
AUDIT = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
ONI_CSV = ROOT / 'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/correlaciones/maize_ONI_Pearson/20261008_095854_51632d/oni_v6_monthly_centers.csv'
ONI_HTML = ROOT / '01_Data/ONI/ONI_v6_2026-10-08.html'


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--corrida', required=True)
    a = ap.parse_args(); run = Path(a.corrida)
    L = []
    def sec(t): L.append(f'\n## {t}\n')
    def out(t): L.append(t); print(t, flush=True)

    plaus = set(pd.read_csv(AUDIT).query("clase in ['OK','DUDOSO_RATIO_FAO']").pixel_id)
    con = sqlite3.connect(f'file:{SQL.as_posix()}?mode=ro', uri=True)
    q = """select pixel_id, latitud, temporada, fase, inicio, fin, anio_rendimiento, z_rendimiento as z, rendimiento_sin_tendencia,
                  pct_dias_afectados, umbral, variable_climatica, pct_dias_racha_v2, umbral_v2, p_menos_et0, edd29, fraccion_dias_mjo_debil, """ + \
        ', '.join(f'fraccion_dias_mjo_{k}' for k in range(1, 9)) + """
           from pares_v2 where alineacion = 'maturity-year' and par_amenaza_rendimiento_valido = 1"""
    d = pd.concat(pd.read_sql_query(q, con, chunksize=500_000), ignore_index=True); con.close()
    d = d[d.pixel_id.isin(plaus)]
    base = d.drop_duplicates(['pixel_id', 'temporada'])

    sec('1. Rendimiento (Y = z_rendimiento)')
    st = base.groupby('pixel_id').z.agg(['mean', 'std', 'count'])
    out(f'- Píxeles: {len(st):,}. Años por píxel: mín {st["count"].min()}, mediana {st["count"].median():.0f}, máx {st["count"].max()}.')
    out(f'- Media de z por píxel: |media| máx {st["mean"].abs().max():.3f} (debe ser ≈ 0). DE de z por píxel: {st["std"].min():.3f}–{st["std"].max():.3f} (debe ser ≈ 1).')
    dup = base.groupby(['pixel_id', 'anio_rendimiento']).size()
    out(f'- Pares (píxel, año de cosecha) repetidos: {(dup > 1).sum()} (debe ser 0).')
    rel = (base.anio_rendimiento - base.temporada).value_counts().sort_index()
    out(f'- Año de cosecha − temporada: ' + ', '.join(f'{k}: {v:,} filas' for k, v in rel.items()) + ' (0 = cosecha el mismo año de siembra, 1 = al año siguiente).')

    sec('2. Amenazas')
    um = d.groupby(['fase', 'variable_climatica', 'umbral']).size().reset_index(name='filas')
    out('- Umbrales v1 en la base (pct_dias_afectados): ' + '; '.join(f'{r.fase} {r.variable_climatica} {r.umbral}' for r in um.itertuples()))
    u2 = d[d.fase == 'FIL'].umbral_v2.value_counts(dropna=False)
    out(f'- Umbral v2 en FIL (calor FIL usa pct_dias_racha_v2): {u2.to_dict()} (tabla v2: 32,9 °C).')
    for col, fases in [('pct_dias_afectados', ['EST', 'VEG', 'FLO', 'REP', 'MAT']), ('pct_dias_racha_v2', ['FIL']),
                       ('p_menos_et0', ['EST', 'VEG', 'FLO', 'FIL']), ('edd29', ['FLO', 'REP', 'FIL'])]:
        for f in fases:
            s = d.loc[d.fase == f, col]
            var = d[d.fase == f].groupby('pixel_id')[col].std()
            out(f'- {col} {f}: rango {s.min():.1f} a {s.max():.1f}; faltantes {100 * s.isna().mean():.2f} %; '
                f'píxeles sin variación en 36 años {100 * (var.fillna(0) < 1e-9).mean():.1f} % (no se puede calcular r en ellos).')

    sec('3. ONI mensual')
    oni = pd.read_csv(ONI_CSV, parse_dates=['month_center'])
    cells = [re.sub(r'<[^>]+>', '', c).strip() for c in
             re.findall(r'<td[^>]*>(.*?)</td>', ONI_HTML.read_text(encoding='utf-8', errors='ignore'), flags=re.S | re.I)]
    tab, i = {}, 0
    while i < len(cells) - 12:
        if re.fullmatch(r'(19|20)\d\d', cells[i]):
            try: tab[int(cells[i])] = [float(v) for v in cells[i + 1:i + 13]]; i += 13; continue
            except ValueError: pass
        i += 1
    if tab:
        dif = [abs(r.oni - tab[r.month_center.year][r.month_center.month - 1]) for r in oni.itertuples() if r.month_center.year in tab]
        out(f'- Comparado contra la tabla oficial ONI v6 ({ONI_HTML.name}): {len(dif)} meses, diferencia máxima {max(dif):.3f} (debe ser 0).')
    else:
        out(f'- No se pudo leer la tabla de {ONI_HTML.name}: revisar a mano.')
    rng = oni[(oni.month_center >= '1980-01-01') & (oni.month_center <= '2016-12-01')]
    out(f'- Meses 1980–2016 disponibles: {len(rng)} de 444; faltantes {int(rng.oni.isna().sum())}.')

    sec('4. MJO')
    fr = d[[f'fraccion_dias_mjo_{k}' for k in range(1, 9)] + ['fraccion_dias_mjo_debil']].sum(1)
    out(f'- Suma de fracciones MJO 1–8 + débil: {fr.quantile(.01):.3f}–{fr.quantile(.99):.3f} (percentiles 1–99; debe ser ≈ 1).')
    pp = pd.read_csv(run / 'correlacion_por_pixel.csv.gz', usecols=['variable', 'n', 'pearson', 'pixel_id', 'grupo'])
    nm = pp[pp.variable.str.startswith('MJO')].n.max(); na = pp[pp.variable == 'calor VEG'].n.max()
    out(f'- Años máximos por píxel: MJO {nm}, amenazas {na} (MJO debe tener 3 menos por excluir cosechas 2014–2016).')

    sec('5. Calendario y grupos')
    est = d[d.fase == 'EST'].assign(m=lambda t: pd.to_datetime(t.inicio).dt.month)
    nmes = est.groupby('pixel_id').m.nunique()
    out(f'- Meses de siembra distintos por píxel en 36 años: {nmes.value_counts().sort_index().to_dict()} (1 = calendario fijo).')
    dur = d.assign(i=pd.to_datetime(d.inicio), f=pd.to_datetime(d.fin)).groupby(['pixel_id', 'temporada']).agg(i=('i', 'min'), f=('f', 'max'))
    dias = (dur.f - dur.i).dt.days
    out(f'- Duración de la temporada (inicio EST a fin MAT): {dias.quantile(.05):.0f}–{dias.quantile(.95):.0f} días (percentiles 5–95).')
    g = pd.read_csv(run / 'grupos_calendario.csv')
    gd = g.merge(dias.groupby('pixel_id').median().rename('dias'), left_on='pixel_id', right_index=True)
    out('- Por grupo: ' + '; '.join(f'{k}: {len(s)} píx., latitud {s.latitud.min():.0f} a {s.latitud.max():.0f}, temporada mediana {s.dias.median():.0f} días'
                                 for k, s in gd.groupby('grupo')))

    sec('6. Supuestos de la prueba')
    Y = base.pivot(index='pixel_id', columns='temporada', values='z')
    a1 = pd.Series([pd.Series(r).dropna().autocorr(1) for r in Y.to_numpy()]).dropna()
    out(f'- Autocorrelación lag-1 de z por píxel: mediana {a1.median():.2f}; % de píxeles con > 0,3: {100 * (a1 > .3).mean():.1f} % '
        '(la prueba supone años independientes; si es alta, el p sale optimista).')
    sk = base.groupby('pixel_id').z.skew()
    out(f'- Asimetría de z por píxel: mediana {sk.median():.2f}; % con asimetría < −1 (cola de pérdidas larga): {100 * (sk < -1).mean():.1f} %.')

    sec('7. Multiplicidad de la significancia de campo')
    M = pd.read_csv(run / 'matriz_grupos.csv')
    for fam, s in M.groupby('familia'):
        out(f'- {fam}: {int(s.significancia_campo.sum())} de {len(s)} celdas con p de campo < 0,05; por azar se esperan ≈ {0.05 * len(s):.1f}. '
            f'Con Bonferroni (p < {0.05 / len(s):.4f}): {int((s.p_campo < 0.05 / len(s)).sum())}.')
    out(f'- Resolución mínima del p de campo con {int(round(1 / M.p_campo.min())) - 1} permutaciones: {M.p_campo.min():.4f}.')

    (run / 'auditoria.md').write_text('# Auditoría de la corrida ' + run.name + '\n' + '\n'.join(L) + '\n', encoding='utf-8')
    print(f'Escrito {run / "auditoria.md"}')


if __name__ == '__main__':
    main()
