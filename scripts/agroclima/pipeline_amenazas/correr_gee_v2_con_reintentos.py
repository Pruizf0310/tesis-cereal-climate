"""Lanza maize_gee_variables_v2.py sin modificarlo (así los lotes ya guardados siguen siendo válidos),
pero con reintentos largos cuando Earth Engine responde 'Too Many Requests' (modo restringido / límite de concurrencia).
Uso: .venv/Scripts/python.exe correr_gee_v2_con_reintentos.py --workers 4 --batch-size 8
"""
import random, sys, time
import pipeline as core

_original = core.fetch_pages


def fetch_con_espera(ee, expression):
    for intento in range(12):
        try:
            return _original(ee, expression)
        except Exception as e:
            msg = str(e)
            if 'Too Many Requests' not in msg and 'concurrency' not in msg.lower() and '429' not in msg:
                raise
            espera = min(30 * 2 ** intento, 600) * (0.5 + random.random())
            print(f'  GEE pidió bajar el ritmo (intento {intento + 1}/12); espero {espera:.0f} s', flush=True)
            time.sleep(espera)
    return _original(ee, expression)


core.fetch_pages = fetch_con_espera
import maize_gee_variables_v2 as m  # noqa: E402  (después del parche)
m.core.fetch_pages = fetch_con_espera
m.main()
