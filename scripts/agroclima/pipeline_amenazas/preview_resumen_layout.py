from pathlib import Path
import json
import numpy as np
import pandas as pd
import resumen_amenazas_maize as m
from resumen_amenazas_maize import *
src=Path('resumen_amenazas_maize.py').read_text(encoding='utf-8-sig')
root=Path('C:/Users/paola/Tesis')
out=root/'03_Resultados/Agroclima/vigente/diagnosticos/resumen_visual_maize'
d=pd.read_csv(out/'acumulado_amenazas_por_pixel_fase.csv')
coords=d[d.phase=='EST'][['pixel_id','latitude','longitude']].reset_index(drop=True)
accumulated=np.stack([d[d.phase==p].set_index('pixel_id').reindex(coords.pixel_id).accumulated_1981_2016.to_numpy() for p in PHASES])
info=json.loads((out/'procedencia_acumulado.json').read_text(encoding='utf-8'))
labels=info['displayed_rules']
outline=boundaries(root/'Repositorio/tesis-cereal-climate/web-v2/public/data/world_outline.geojson')
r=np.rint((coords.latitude.to_numpy()+89.75)/.5).astype(int)
c=np.rint((coords.longitude.to_numpy()+179.75)/.5).astype(int)
block=src[src.index('    heat=LinearSegmentedColormap'):src.index('    # Never overwrite')]
import textwrap
exec(textwrap.dedent(block))
fig.savefig('preview_layout.png',dpi=120,facecolor='white')
print('Preview generated from existing aggregate CSV; full analysis not run.')
