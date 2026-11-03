"""Mapa de r SST–rendimiento de un mes para el píxel típico (salida de pixel_tipico_sst.py), con el estilo de la PPT.

Fondo K, divergente cian (r < 0) – magenta (r > 0) con centro oscuro para |r| < ~0,17, tierra en gris oscuro, estrella en el píxel y caja Niño 3.4.
Uso: python figura_sst_pixel.py --sst <carpeta sst_...> [--mes 7] [--salida figura.png]
"""
import argparse, json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Rectangle


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sst', required=True); ap.add_argument('--mes', type=int, default=7); ap.add_argument('--salida')
    a = ap.parse_args()
    z = np.load(Path(a.sst) / 'mapas_r.npz'); info = json.loads((Path(a.sst) / 'resumen.json').read_text(encoding='utf-8'))
    r = z['despues'][a.mes - 1]; lat, lon = z['lat'], z['lon']
    lon2 = np.where(lon > 180, lon - 360, lon); o = np.argsort(lon2); r = r[:, o]; lon2 = lon2[o]
    cmap = LinearSegmentedColormap.from_list('cmk', [(0, '#22D3EE'), (0.225, '#0E7490'), (0.36, '#0B1730'), (0.64, '#0B1730'), (0.775, '#9D174D'), (1, '#E91E8C')])
    cmap.set_bad('#1E293B')
    fig = plt.figure(figsize=(10, 5.2), dpi=220, facecolor='#050B1A')
    ax = fig.add_axes([0, 0.1, 1, 0.9]); ax.set_facecolor('#050B1A')
    im = ax.imshow(np.ma.masked_invalid(r), origin='lower', extent=[-180, 180, -90, 90], cmap=cmap, vmin=-.6, vmax=.6,
                   interpolation='nearest', aspect='auto')
    ax.add_patch(Rectangle((-170, -5), 50, 10, fill=False, ec='#F8FAFC', lw=1.2, ls='--'))
    ax.text(-145, 7.5, 'Niño 3.4', color='#F8FAFC', fontsize=9, ha='center')
    ax.plot(info['lon'], info['lat'], marker='*', ms=16, mfc='#FACC15', mec='#050B1A', mew=0.8)
    ax.set_xlim(-180, 180); ax.set_ylim(-60, 75); ax.axis('off')
    cax = fig.add_axes([0.3, 0.04, 0.4, 0.025])
    cb = fig.colorbar(im, cax=cax, orientation='horizontal', ticks=[-.6, -.33, 0, .33, .6])
    cb.ax.set_xticklabels(['−0,6', '−0,33', '0', '0,33', '0,6'], color='#CBD5E1', fontsize=9)
    cb.outline.set_visible(False); cb.ax.tick_params(color='#475569', length=3)
    out = Path(a.salida or Path(a.sst) / f'mapa_r_mes{a.mes:02d}.png'); fig.savefig(out, facecolor='#050B1A'); print(out)


if __name__ == '__main__':
    main()
