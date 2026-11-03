"""Authoritative thesis results location; independent of the script checkout."""
from pathlib import Path

TESIS_ROOT = Path('C:/Users/paola/Tesis')


def resultados_oni(root=TESIS_ROOT):
    return Path(root)/'03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_frecuencias'
