"""A real branched methodological flow, matching the user's compact Mermaid reference."""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor

OUT=Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_frecuencias/flujo_explicativo_simple_20261020')
W,H=2770,1370
nodes={
 'Y0':(55,105,['Rendimiento GDHY','original · 1981–2016']),
 'Y1':(385,105,['Unir años y revisar','fechas, coordenadas','y valores ausentes']),
 'Y2':(715,105,['Quitar la tendencia','del rendimiento','por píxel']),
 'Y3':(1045,105,['Estandarizar','rendimiento → z']),
 'CAL':(55,355,['Calendario de secano','y estadios del maíz']),
 'WIN':(385,355,['Fechas de cada fase','por píxel y temporada']),
 'RULE':(385,520,['Reglas de los papers','umbral + duración']),
 'CLIM':(55,720,['ERA5-Land diario','Tmax y precipitación']),
 'MASK':(385,720,['Seleccionar celdas','climáticas válidas','y conservar su soporte']),
 'EVENT':(715,520,['Detectar episodios','en cada celda','y ventana agrícola']),
 'DAILY':(1045,520,['Fracción del área','afectada cada día']),
 'ANNUAL':(1375,520,['Agregar por temporada','episodios / 100 días','y % de días afectados']),
 'ONI':(1045,850,['ONI mensual','valor y categoría']),
 'A':(1705,520,['Tabla A anual','exposición + ONI','+ rendimiento z']),
 'OAN':(1705,285,['Comparar frecuencias','frío / neutral / cálido']),
 'OMAP':(2035,285,['Contrastes ONI','y sensibilidad','sin tendencia']),
 'OY':(2035,105,['Relacionar ONI','con rendimiento z']),
 'EY':(2035,520,['Relacionar exposición','con rendimiento z','Pearson por fase']),
 'BLOCK':(2035,705,['Agrupar fases','en bloques y revisar','su aporte incremental']),
 'MJO':(1045,1040,['MJO diaria','fase y amplitud']),
 'B':(1375,850,['Tabla B diaria','fracción afectada','+ mes + ONI + MJO']),
 'MAN':(1705,850,['Comparar estados MJO','dentro del mismo mes','y categoría ONI']),
 'MPLOT':(2035,920,['Probabilidades MJO','y diferencias frente','a referencia comparable']),
 'FINAL':(2400,520,['Mapas y perfiles','tablas, intervalos','y resultados regionales']),
}
edges=[('Y0','Y1'),('Y1','Y2'),('Y2','Y3'),('CAL','WIN'),('CLIM','MASK'),
 ('WIN','EVENT'),('RULE','EVENT'),('MASK','EVENT'),('EVENT','DAILY'),('DAILY','ANNUAL'),
 ('ANNUAL','A'),('Y3','A'),('ONI','A'),('A','OAN'),
 ('OAN','OMAP'),('A','OY'),('A','EY'),('A','BLOCK'),
 ('DAILY','B'),('ONI','B'),('MJO','B'),('B','MAN'),('MAN','MPLOT'),
 ('OMAP','FINAL'),('OY','FINAL'),('EY','FINAL'),('BLOCK','FINAL'),('MPLOT','FINAL')]
BW,BH=270,108


def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=OUT);p.add_argument('--replace',action='store_true');args=p.parse_args()
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=args.replace)
 pdfmetrics.registerFont(TTFont('Flow','C:/Windows/Fonts/segoeui.ttf'))
 pdfmetrics.registerFont(TTFont('FlowBold','C:/Windows/Fonts/seguisb.ttf'))
 c=canvas.Canvas(str(out/'flujo_explicativo.pdf'),pagesize=(W,H));parts=[]
 def txt(x,y,text,size=19,color='#173b50',bold=False,center=False):
  anchor=' text-anchor="middle"' if center else ''
  parts.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" fill="{color}"{anchor}'+(' font-weight="600"' if bold else '')+'>'+escape(text)+'</text>')
  c.setFont('FlowBold' if bold else 'Flow',size);c.setFillColor(HexColor(color))
  if center:c.drawCentredString(x,H-y,text)
  else:c.drawString(x,H-y,text)
 def rect(x,y,w,h,fill,stroke='#3e647d',r=22):
  parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.1"/>')
  c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke));c.setLineWidth(1.1);c.roundRect(x,H-y-h,w,h,r,fill=1,stroke=1)
 def arrow(a,b):
  x,y,_=nodes[a];xx,yy,_=nodes[b]
  start=(x+BW,y+BH/2);end=(xx,yy+BH/2)
  if a=='ONI' and b=='A':
   # Separate annual-window ONI from the daily ONI route.
   start=(x+BW/2,y);end=(xx+BW/2,yy+BH)
   control1=(start[0],770);control2=(end[0],770)
  elif a=='Y3' and b=='A':
   start=(x+BW,y+BH/2);end=(xx,yy+20)
   control1=(1665,start[1]);control2=(1665,yy-35)
  elif x==xx and yy<y:
   start=(x+BW/2,y);end=(xx+BW/2,yy+BH)
   control1=(start[0],(start[1]+end[1])/2);control2=control1
  else:
   dx=max(35,(end[0]-start[0])*.5);control1=(start[0]+dx,start[1]);control2=(end[0]-dx,end[1])
  color='#9daeb6';sw=1.7
  d=f'M {start[0]} {start[1]} C {control1[0]} {control1[1]} {control2[0]} {control2[1]} {end[0]} {end[1]}'
  parts.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#arrow)"/>')
  c.setStrokeColor(HexColor(color));c.setLineWidth(sw);path=c.beginPath();path.moveTo(start[0],H-start[1]);path.curveTo(control1[0],H-control1[1],control2[0],H-control2[1],end[0],H-end[1]);c.drawPath(path)
  import math
  ang=math.atan2(end[1]-control2[1],end[0]-control2[0])
  for s in [-.45,.45]:c.line(end[0],H-end[1],end[0]-8*math.cos(ang+s),H-end[1]+8*math.sin(ang+s))
 txt(55,48,'Cómo se integran rendimiento, amenazas, ONI y MJO',32,bold=True)
 txt(55,78,'Maíz · píxel y temporada como llaves comunes · las flechas muestran qué información se añade en cada unión',17,color='#607987')
 for a,b in edges:arrow(a,b)
 for id,(x,y,lines) in nodes.items():
  fill='#063657' if id not in ['A','B','FINAL'] else '#0a546a'
  rect(x,y,BW,BH,fill)
  yy=y+BH/2-(len(lines)-1)*12+7
  for line in lines:txt(x+BW/2,yy,line,19,color='#bedff5',bold=True,center=True);yy+=24
 # Labels sit in genuinely empty channels, not on top of the cards.
 txt(1390,414,'ONI promedio de la ventana agrícola',14,color='#637d8a')
 txt(1390,1000,'ONI del mes correspondiente a cada día',14,color='#637d8a')
 rect(55,1195,2645,107,'#f1f5f6','#d7e0e4',18)
 txt(79,1227,'En todos los cruces: conservar ceros y faltantes, cobertura válida, número de temporadas e intervalos bootstrap.',19,bold=True)
 txt(79,1255,'Rendimiento: mantener ambos escenarios de año. MJO: controlar mes y ONI. Modelos por bloques: comprobar solapamientos y colinealidad.',16,color='#526f7e')
 txt(79,1280,'Las regiones y las comparaciones se definen antes de interpretar resultados; las asociaciones no representan efectos causales.',16,color='#526f7e')
 txt(55,1341,'MAT utiliza días de lluvia; sus unidades se separan de los episodios de calor. La Tabla A conserva datos anuales; la Tabla B conserva datos diarios.',15,color='#647d88')
 c.showPage();c.save()
 defs='<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M1,1 L7,4 L1,7" fill="none" stroke="#9daeb6" stroke-width="1.1"/></marker></defs>'
 (out/'flujo_explicativo.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}pt" height="{H}pt" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>{defs}'+''.join(parts)+'</svg>',encoding='utf-8')
 mmd=['flowchart LR']
 for id,(_,_,lines) in nodes.items():mmd.append(f'  {id}["'+ '<br/>'.join(lines)+'"]')
 for a,b in edges:mmd.append(f'  {a} --> {b}')
 mmd.extend(['  classDef datos fill:#063657,stroke:#3e647d,color:#bedff5','  classDef tabla fill:#0a546a,stroke:#3e647d,color:#bedff5','  class '+','.join(k for k in nodes if k not in ['A','B','FINAL'])+' datos','  class A,B,FINAL tabla'])
 (out/'flujo_explicativo.mmd').write_text('\n'.join(mmd),encoding='utf-8')
 (out/'LEEME.md').write_text('Flujo explicativo adicional al atlas previo. Cajas breves y conexiones reales: transformación, unión, análisis y producto. El flujo describe el diseño, no certifica ejecución de todas las ramas. Para detalle de diagnósticos, variables y extensiones consultar el atlas completo. La estandarización z y la correspondencia de año del rendimiento requieren su validación; los conteos climáticos originales son promedios sobre celdas. El origen de la selección H5 y la exploración SST permanecen en la documentación detallada. La MJO no se añade como una sola etiqueta a toda la temporada: se une por fecha a la Tabla B.\n',encoding='utf-8')
 print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
