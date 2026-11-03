"""Secuencia v2 de maíz: espera a que termine GEE v2 y luego integra la SQLite y corre las correlaciones.

1. Espera a que maize_variables_v2_GEE_1981_2016/estado.json diga COMPLETED (revisa cada 5 min).
   Si dice FAILED, se detiene: relanza maize_gee_variables_v2.py (reanuda desde los lotes guardados) y vuelve a correr esto.
2. integrar_variables_v2_sqlite.py → carpeta cruce_v2_<fecha> con cruce_rendimiento_v2.sqlite
3. correlaciones_v2_maiz.py sobre esa SQLite (1.000 permutaciones)
Uso: .venv/Scripts/python.exe secuencia_v2_maiz.py
"""
import json, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('C:/Users/paola/Tesis')
GEE = ROOT / '03_Resultados/Agroclima/vigente/ejecuciones/maize_variables_v2_GEE_1981_2016'
PY = sys.executable


def log(m):
    print(time.strftime('%Y-%m-%d %H:%M:%S'), m, flush=True)


MAX_REINTENTOS = 20
reintentos = 0
while True:
    est = GEE / 'estado.json'
    s = json.loads(est.read_text())['status'] if est.exists() else 'SIN_ESTADO'
    prog = GEE / 'progreso.json'
    p = json.loads(prog.read_text()) if prog.exists() else {}
    if s == 'COMPLETED' and (GEE / 'variables_v2_por_fase.csv').exists():
        log('GEE v2 terminado.'); break
    if s in ('FAILED', 'INTERRUPTED'):
        if reintentos >= MAX_REINTENTOS:
            log(f'GEE v2 falló {reintentos} veces; se detiene. Revisa el error en la pestaña.'); sys.exit(1)
        reintentos += 1
        espera = min(60 * reintentos, 900)
        log(f'GEE v2 se cayó (estado {s}). Reintento {reintentos}/{MAX_REINTENTOS} en {espera} s; reanuda desde los lotes guardados.')
        time.sleep(espera)
        subprocess.run([PY, '-u', str(HERE / 'correr_gee_v2_con_reintentos.py'), '--workers', '12', '--batch-size', '8'], cwd=HERE)
        continue
    log(f'Esperando GEE v2: estado={s} lotes={p.get("done")}/{p.get("total")} restante≈{(p.get("eta_s") or 0) / 3600:.1f} h')
    time.sleep(300)

destino = ROOT / f'03_Resultados/Agroclima/vigente/rendimiento/cruce_v2_{time.strftime("%Y%m%d_%H%M%S")}'
log('Paso 2: integración SQLite v2')
r = subprocess.run([PY, '-u', str(HERE / 'integrar_variables_v2_sqlite.py'), '--destino', str(destino)], cwd=HERE)
if r.returncode: log('Falló la integración; se detiene.'); sys.exit(1)
log('Paso 3: correlaciones v2')
r = subprocess.run([PY, '-u', str(HERE / 'correlaciones_v2_maiz.py'), '--sqlite', str(destino / 'cruce_rendimiento_v2.sqlite')], cwd=HERE)
log('Secuencia terminada.' if r.returncode == 0 else 'Fallaron las correlaciones; revisa el registro.')
