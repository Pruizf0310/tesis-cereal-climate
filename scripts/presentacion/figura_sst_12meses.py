"""Figura de 12 mapas (un mes por panel) de la correlación SST–rendimiento de un píxel, leída del H5 de correlaciones.

H5: correlacion (n_pix, 12 meses, 360×720 a 0,5°) con la fila h5_index de pixeles_maize.csv. Cada mes es la SST
mensual sin tendencia del mismo año de la cosecha (correlacion_masiva.py). Rojo = r > 0, azul = r < 0, tierra en gris
con contorno suave. Meses del ciclo del cultivo en amarillo; después de la cosecha, en gris.
Uso: python figura_sst_12meses.py [--pixel 191325] [--h5 D:/maize_correlacion_vectorizada.h5] [--salida ruta.png]
"""
import argparse
from pathlib import Path

import h5py
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

PIX = Path('C:/Users/paola/Tesis/02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv')
CAL = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/calendario/calendario_seis_fases_secano.csv')
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
BG, TIERRA, COSTA, TXT, TXT2, AMARILLO = '#050B1A', '#2A3852', '#7C8BA3', '#F8FAFC', '#94A3B8', '#FACC15'


def meses_ciclo(lat, lon):
    c = pd.read_csv(CAL)
    g = c[(c.crop == 'maize') & (c.lat == lat) & (c.lon == lon)]
    ini, fin = g.start_doy.min(), g.end_doy.max()
    d0 = pd.Timestamp('2001-01-01')
    m0, m1 = (d0 + pd.Timedelta(days=int(ini) - 1)).month, (d0 + pd.Timedelta(days=int(fin) - 1)).month
    return set(range(m0, m1 + 1)) if m1 >= m0 else set(range(m0, 13)) | set(range(1, m1 + 1)), m1


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--pixel', type=int, default=191325)
    ap.add_argument('--h5', default='D:/maize_correlacion_vectorizada.h5')
    ap.add_argument('--salida')
    a = ap.parse_args()
    px = pd.read_csv(PIX).set_index('pixel_id').loc[a.pixel]
    lat, lon, hi = float(px.latitude), float(px.longitude), int(px.h5_index)
    with h5py.File(a.h5, 'r') as f:
        C = f['correlacion'][hi].reshape(12, 360, 720)
    lats = np.arange(-89.75, 90, .5); lons = np.arange(.25, 360, .5)
    o = np.argsort(np.where(lons > 180, lons - 360, lons)); lons2 = np.sort(np.where(lons > 180, lons - 360, lons))
    C = C[:, :, o]
    tierra = np.isnan(C[0])
    ciclo, m_cosecha = meses_ciclo(lat, lon)
    cmap = LinearSegmentedColormap.from_list('rb', [(0, '#2B6CD9'), (.2, '#1D4E9E'), (.38, '#0E1A33'), (.62, '#0E1A33'),
                                                    (.8, '#A3243B'), (1, '#E5484D')])
    cmap.set_bad(TIERRA)
    fig, axs = plt.subplots(3, 4, figsize=(16, 6.6), dpi=200, facecolor=BG)
    plt.subplots_adjust(left=.005, right=.995, top=.95, bottom=.1, wspace=.03, hspace=.2)
    for m, ax in enumerate(axs.flat):
        ax.set_facecolor(BG)
        im = ax.imshow(np.ma.masked_invalid(C[m]), origin='lower', extent=[-180, 180, -90, 90], cmap=cmap,
                       vmin=-.4, vmax=.4, interpolation='bilinear', aspect='auto')
        ax.contour(lons2, lats, tierra.astype(float), levels=[.5], colors=COSTA, linewidths=.35)
        ax.plot(lon, lat, marker='*', ms=9, mfc=AMARILLO, mec=BG, mew=.5)
        ax.set_xlim(-180, 180); ax.set_ylim(-58, 72); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values(): sp.set_visible(False)
        en_ciclo = (m + 1) in ciclo; despues = (m + 1) > m_cosecha
        color = AMARILLO if en_ciclo else TXT2
        ax.set_title(MESES[m] + ('  · después de la cosecha' if despues else ''), color=color, fontsize=10.5,
                     loc='left', pad=3, fontweight='bold' if en_ciclo else 'normal')
    cax = fig.add_axes([.35, .035, .3, .022])
    cb = fig.colorbar(im, cax=cax, orientation='horizontal', ticks=[-.4, -.2, 0, .2, .4])
    cb.ax.set_xticklabels(['−0,4', '−0,2', '0', '0,2', '0,4'], color=TXT2, fontsize=9)
    cb.outline.set_visible(False); cb.ax.tick_params(color='#475569', length=3)
    fig.text(.335, .045, 'r  ', color=TXT2, fontsize=10, ha='right', va='center')
    out = Path(a.salida or Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/pixel_tipico') / f'mapas_sst_12meses_{a.pixel}.png')
    fig.savefig(out, facecolor=BG); print(out)
    print('pct |r|>=0,33 por mes:', [round(100 * float(np.mean(np.abs(C[m][np.isfinite(C[m])]) >= .33)), 1) for m in range(12)])


if __name__ == '__main__':
    main()
