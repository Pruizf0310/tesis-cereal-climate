"""Arma la carpeta de figuras para revisar qué sirve: mapas nuevos (vigentes), figuras anteriores de referencia y un índice HTML.

Vigentes = salen de correlaciones_calendario_maiz.py (ONI mensual, año de cosecha, tabla v2).
Referencia = figuras anteriores aún válidas pero con otro método (regiones geográficas o reglas v1).
Descartadas = no se copian; se listan en el índice con la razón (ONI promediado en ventanas, same-label, pilotos).
Uso: .venv/Scripts/python.exe figuras_revision.py --corrida RUTA_correlaciones_calendario [--destino RUTA]
"""
import argparse, shutil, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from mapa_correlacion_pixel import contornos, SHP

HERE = Path(__file__).resolve().parent
V = Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente')
AMENAZAS = ['calor EST', 'sequia EST', 'calor VEG', 'sequia VEG', 'calor FLO', 'sequia FLO', 'EDD29 FLO',
            'calor REP', 'EDD29 REP', 'calor FIL', 'sequia FIL', 'EDD29 FIL', 'lluvia MAT']
ONI = ['ONI mes de cosecha', 'ONI mes-2', 'ONI mes-5']
REFERENCIA = [
    (V / 'rendimiento/cruce_v2_20261024_184932/analisis_v2_20261025_222548/E1_R2_fuera_muestra_por_region.png',
     'R² fuera de muestra por región, tabla v1 contra v2 (regiones geográficas, 25 oct).', '¿La tabla v2 explica más que la v1? Agrupación por región, no por calendario.'),
    (V / 'rendimiento/cruce_v2_20261024_184932/analisis_v2_20261025_222548/E2_AUC_perdida_por_region.png',
     'AUC de años de pérdida por región (25 oct).', '¿Qué regiones anticipan años malos? Mismo método regional.'),
    (V / 'correlaciones_rendimiento/maize/maturity-year_20261023_164328/resultados/mapas_r_seis_fases.png',
     'r de calor v1 (episodios por fase) contra rendimiento, seis fases (corrida oficial 23 oct).', 'Mismo mensaje que la carpeta 01 con las reglas v1; sirve para comparar v1 contra v2.'),
]
DESCARTADAS = [
    ('correlaciones/maize_ONI_v6, maize_ONI_Pearson, maize_ONI_frecuencias (8–20 oct)', 'Usan el ONI promediado dentro de la ventana de cada fase (promedio de promedios).'),
    ('rendimiento/verificacion_ONI_pixel_20261023 y atribucion_oni_20261023', 'Mismo ONI promediado; reemplazados por la carpeta 02.'),
    ('correlaciones_rendimiento/maize/same-label_*', 'Alineación same-label descartada: GDHY usa año de cosecha.'),
    ('correlaciones_rendimiento/maize/piloto200_*, tiempo_*', 'Pilotos y pruebas de tiempo, no corridas completas.'),
    ('probabilidades/maize_*_global_1981_2016 (8 oct)', 'Probabilidades condicionadas al ONI promediado y a la MJO en EST; método anterior.'),
    ('correlaciones/maize_MJO_diario/RMM_10pix', 'Piloto de 10 píxeles.'),
]


def mapa_grupos(run, destino):
    g = pd.read_csv(run / 'grupos_calendario.csv')
    orden = g.grupo.value_counts().index.tolist()
    colores = ['#2f6b4f', '#c0532a', '#2a6f9e', '#a87612', '#7b4fa0', '#4f9a94', '#b23b6e', '#6d7a2f'][:len(orden)]
    code = g.grupo.map({k: i for i, k in enumerate(orden)}).to_numpy()
    fil = np.floor((g.latitud.to_numpy() + 90) / .5).astype(int); col = np.floor((g.longitud.to_numpy() + 180) / .5).astype(int)
    A = np.full((360, 720), np.nan); A[fil, col] = code
    fig, ax = plt.subplots(figsize=(13, 6.4), dpi=150)
    ax.pcolormesh(np.arange(-180, 180.01, .5), np.arange(-90, 90.01, .5), A, cmap=ListedColormap(colores), vmin=-.5, vmax=len(orden) - .5, shading='flat')
    for an in contornos(SHP): ax.plot(an[:, 0], an[:, 1], color='#55605a', lw=.35)
    ax.set_xlim(-180, 180); ax.set_ylim(-56, 72); ax.set_aspect('equal'); ax.tick_params(labelsize=8, colors='#55605a')
    for i, k in enumerate(orden):
        ax.plot([], [], 's', color=colores[i], ms=8, label=f'{k} ({(g.grupo == k).sum():,} píx.)'.replace(',', '.'))
    ax.legend(loc='lower left', fontsize=8, frameon=False)
    ax.set_title('Grupos de calendario: hemisferio × trimestre del mes de siembra', fontsize=12, loc='left')
    ax.text(0, -.1, f'Fuente: {run.name}/grupos_calendario.csv · mes de siembra = mes de inicio de EST (fijo por píxel)',
            transform=ax.transAxes, fontsize=8, va='top', color='#33403a')
    f = destino / 'grupos_calendario.png'; fig.savefig(f, bbox_inches='tight'); plt.close(fig); return f


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('--corrida', required=True)
    ap.add_argument('--destino', default=str(V / f'figuras_revision_{time.strftime("%Y%m%d")}'))
    a = ap.parse_args(); run = Path(a.corrida); D = Path(a.destino)
    carpetas = {k: D / k for k in ['01_amenazas_vs_rendimiento', '02_ONI_vs_rendimiento', '03_contexto', '04_referencia_anteriores']}
    for c in carpetas.values(): c.mkdir(parents=True, exist_ok=True)
    M = pd.read_csv(run / 'matriz_grupos.csv').query("grupo == 'todos'").set_index('variable')
    items = []  # (carpeta, archivo, título, qué responde, estado)
    for i, var in enumerate(AMENAZAS + ONI, 1):
        subprocess.run([sys.executable, str(HERE / 'mapa_correlacion_pixel.py'), '--corrida', str(run), '--variable', var, '--solo-significativos'], check=True)
        src = run / 'mapas' / (var.replace(' ', '_') + '_significativos.png')
        dest_c = carpetas['01_amenazas_vs_rendimiento'] if var in AMENAZAS else carpetas['02_ONI_vs_rendimiento']
        dst = dest_c / f'{i:02d}_{src.name}'; shutil.copy2(src, dst)
        m = M.loc[var]
        c = lambda v, k=1: f'{v:.{k}f}'.replace('.', ',')
        nota = (f'Píxeles significativos: {c(m.pct_sig_negativo)} % negativos y {c(m.pct_sig_positivo)} % positivos (azar ≈ 2,5 % cada uno); '
                f'p de campo {c(m.p_campo, 3)}{" (supera al azar)" if m.p_campo < .05 else " (no supera al azar)"}.')
        items.append((dest_c.name, dst.name, f'{var} contra rendimiento (solo significativos)', nota, 'vigente'))
    f = mapa_grupos(run, carpetas['03_contexto'])
    items.append(('03_contexto', f.name, 'Grupos de calendario', 'Dónde cae cada grupo. Explica por qué "N · siembra MAM" mezcla EE. UU., Europa y China.', 'vigente'))
    for src, tit, resp in REFERENCIA:
        if src.exists():
            dst = carpetas['04_referencia_anteriores'] / src.name; shutil.copy2(src, dst)
            items.append(('04_referencia_anteriores', dst.name, tit, resp, 'referencia'))
    filas = ''.join(f'<figure><figcaption><b>{t}</b><span class="e {e}">{e}</span><br>{r}<br><code>{c}/{a}</code></figcaption>'
                    f'<a href="{c}/{a}"><img src="{c}/{a}" alt="{t}" loading="lazy"></a></figure>' for c, a, t, r, e in items)
    desc = ''.join(f'<li><code>{c}</code>: {r}</li>' for c, r in DESCARTADAS)
    (D / 'INDICE.html').write_text(f"""<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Figuras para revisar</title>
<style>
:root{{--bg:#f6f7f3;--fg:#1d2420;--muted:#5d685f;--line:#d9ded6;--acc:#2f6b4f;--ref:#a87612}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141916;--fg:#e6ebe5;--muted:#9aa69c;--line:#2f3832;--acc:#7cc19b;--ref:#e0b350;color-scheme:dark}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 "Segoe UI",system-ui,sans-serif;margin:0 auto;max-width:1100px;padding:24px 16px}}
h1{{font-size:1.5rem;margin:0 0 6px}} h2{{font-size:1.1rem;margin:28px 0 8px;color:var(--acc)}} p,li{{max-width:85ch}}
figure{{margin:0 0 28px;border:1px solid var(--line);border-radius:8px;padding:12px;background:var(--bg)}}
figcaption{{font-size:.9rem;margin-bottom:8px}} img{{width:100%;height:auto;background:#fff;border-radius:4px}}
code{{font-size:.8rem;color:var(--muted)}} .e{{margin-left:8px;font-size:.72rem;padding:1px 8px;border-radius:99px;border:1px solid currentColor}}
.vigente{{color:var(--acc)}} .referencia{{color:var(--ref)}}
</style>
<h1>Figuras para revisar · maíz</h1>
<p>Corrida de origen: <code>{run}</code>. <b>Vigente</b> = método actual (ONI mensual, año de cosecha, tabla v2, grupos de calendario).
<b>Referencia</b> = figuras anteriores todavía válidas, pero con otro método. Los mapas muestran en color solo los píxeles con p &lt; 0,05;
gris = con dato pero no significativo; blanco = sin dato.</p>
<p>Para leer los mapas: con 36 años, por azar se esperan ≈ 2,5 % de píxeles significativos de cada signo. Una mancha grande de un solo color
es señal; puntos sueltos de ambos colores pueden ser azar. La auditoría de la corrida está en <code>{run.name}/auditoria.md</code>.</p>
{filas}
<h2>No incluidas (método descartado)</h2><ul>{desc}</ul>
""", encoding='utf-8')
    print(f'Escrito {D / "INDICE.html"} · {len(items)} figuras')


if __name__ == '__main__':
    main()
