"""Mapa de la correlación por píxel de UNA variable contra el rendimiento (salida de correlaciones_calendario_maiz.py).

Cada píxel de 0,5° se pinta con su r de Pearson (rojo = negativo, azul = positivo).
Con --solo-significativos se colorean solo los píxeles con p < 0,05 (con 34–36 años ≈ |r| ≥ 0,33); los demás con dato
quedan en gris y los píxeles sin dato (sin maíz plausible o sin variación de la variable) en blanco.
Contornos de países: Natural Earth 110 m (01_Data/Shapefiles), leídos sin librerías externas.
Uso: .venv/Scripts/python.exe mapa_correlacion_pixel.py --corrida RUTA --variable "EDD29 FIL" [--solo-significativos] [--grupo "S · siembra SON"]
"""
import argparse, struct
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

SHP = Path('C:/Users/paola/Tesis/01_Data/Shapefiles/ne_110m_admin_0_countries.shp')


def contornos(path):
    """Lee los anillos de los polígonos de un .shp (tipo 5) como listas de (lon, lat)."""
    b = path.read_bytes(); i = 100; anillos = []
    while i < len(b):
        largo = struct.unpack('>i', b[i + 4:i + 8])[0] * 2; r = b[i + 8:i + 8 + largo]; i += 8 + largo
        if struct.unpack('<i', r[:4])[0] != 5: continue
        npar, npts = struct.unpack('<2i', r[36:44])
        partes = list(struct.unpack(f'<{npar}i', r[44:44 + 4 * npar])) + [npts]
        pts = np.frombuffer(r[44 + 4 * npar:44 + 4 * npar + 16 * npts], '<f8').reshape(-1, 2)
        anillos += [pts[partes[k]:partes[k + 1]] for k in range(npar)]
    return anillos


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--corrida', required=True); ap.add_argument('--variable', required=True)
    ap.add_argument('--solo-significativos', action='store_true'); ap.add_argument('--grupo', default=None)
    ap.add_argument('--objetivo', default=None, help='para corridas de teleconexión: amenaza objetivo (Y); --variable es el predictor')
    ap.add_argument('--grupos-csv', default=None, help='grupos_calendario.csv si no está en la carpeta de la corrida')
    a = ap.parse_args(); run = Path(a.corrida)
    pp = pd.read_csv(run / 'correlacion_por_pixel.csv.gz')
    if a.objetivo:
        pp = pp[pp.objetivo == a.objetivo].rename(columns={'predictor': 'variable'})
    if a.variable not in set(pp.variable):
        raise SystemExit(f'Variable no encontrada. Disponibles: {sorted(pp.variable.unique())}')
    G = pd.read_csv(a.grupos_csv or run / 'grupos_calendario.csv').set_index('pixel_id')
    t = pp[pp.variable == a.variable].join(G[['latitud', 'longitud']], on='pixel_id')
    if a.grupo: t = t[t.grupo == a.grupo]
    ok = t.pearson.notna(); sig = ok & (t.p < .05)
    n, nneg, npos = int(ok.sum()), int((sig & (t.pearson < 0)).sum()), int((sig & (t.pearson > 0)).sum())

    # rejilla global de 0,5°: fila por latitud, columna por longitud (centros en ±x,25 / ±x,75)
    fil = np.floor((t.latitud.to_numpy() + 90) / .5).astype(int); col = np.floor((t.longitud.to_numpy() + 180) / .5).astype(int)
    R = np.full((360, 720), np.nan); GRIS = np.full((360, 720), np.nan)
    pinta = sig if a.solo_significativos else ok
    R[fil[pinta.to_numpy()], col[pinta.to_numpy()]] = t.pearson[pinta]
    if a.solo_significativos:
        resto = (ok & ~sig).to_numpy(); GRIS[fil[resto], col[resto]] = 1
    lon = np.arange(-180, 180.01, .5); lat = np.arange(-90, 90.01, .5)

    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=150)
    ax.set_facecolor('white')
    ax.pcolormesh(lon, lat, GRIS, cmap=ListedColormap(['#c9cdc7']), vmin=0, vmax=1, shading='flat')
    m = ax.pcolormesh(lon, lat, R, cmap='RdBu', vmin=-.8, vmax=.8, shading='flat')
    for an in contornos(SHP):
        ax.plot(an[:, 0], an[:, 1], color='#55605a', lw=.35)
    ax.set_xlim(-180, 180); ax.set_ylim(-56, 72); ax.set_aspect('equal')
    ax.set_xticks(range(-180, 181, 60)); ax.set_yticks(range(-40, 61, 20))
    ax.tick_params(labelsize=8, colors='#55605a')
    for s in ax.spines.values(): s.set_color('#c9cdc7')
    cb = fig.colorbar(m, ax=ax, shrink=.75, pad=.015)
    cb.set_label(f'r de Pearson con {a.objetivo}' if a.objetivo else 'r de Pearson con el z de rendimiento', fontsize=9)
    tit = (f'{a.variable} vs {a.objetivo} (maíz) · 1981–2016' if a.objetivo else
           f'{a.variable} vs rendimiento de maíz · 1981–2016 · año de cosecha')
    if a.grupo: tit += f' · grupo {a.grupo}'
    ax.set_title(tit, fontsize=12, loc='left')
    mil = lambda v: f'{v:,}'.replace(',', '.'); pct = lambda v: f'{v:.1f}'.replace('.', ',')
    sub = (f'{mil(n)} píxeles con dato · significativos (p < 0,05): {mil(nneg)} negativos ({pct(100 * nneg / n)} %) y {mil(npos)} positivos '
           f'({pct(100 * npos / n)} %) · por azar se esperan ≈ 2,5 % de cada signo')
    if a.solo_significativos: sub += '\nColor = solo significativos · gris = con dato pero no significativo · blanco = sin dato'
    sub += f'\nFuente: {run.name}/correlacion_por_pixel.csv.gz'
    ax.text(0, -.1, sub, transform=ax.transAxes, fontsize=8.5, va='top', color='#33403a', linespacing=1.5)
    out = run / 'mapas'; out.mkdir(exist_ok=True)
    nombre = (f'{a.objetivo}_vs_' if a.objetivo else '') + a.variable.replace(' ', '_') + ('_significativos' if a.solo_significativos else '_todos') + (f'_{a.grupo}' if a.grupo else '')
    f = out / (nombre.replace('·', '').replace('  ', ' ').replace(' ', '_') + '.png')
    fig.savefig(f, bbox_inches='tight'); print(f'Escrito {f}')
    print(f'píxeles {n} · sig. negativos {nneg} · sig. positivos {npos}')


if __name__ == '__main__':
    main()
