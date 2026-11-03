"""Build a fully editable, vector methodological atlas from the documented ONI/MJO plan."""
import argparse
import json
import math
from pathlib import Path
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.pagesizes import A3, landscape

DEFAULT=Path('C:/Users/paola/Tesis/03_Resultados/Agroclima/vigente/correlaciones/maize_ONI_frecuencias/diagrama_metodologico_completo_20261020')
COLORS=dict(datos='#38677b',proceso='#447f78',tabla='#416d91',diagnostico='#9a743b',analisis='#786793',salida='#4c7353')
STATUS={'hecho':('CALCULADO / VERIFICADO','#28785d'),'parcial':('PARCIAL / POR CERRAR','#a77822'),
        'pendiente':('PLANIFICADO','#6c7f93'),'antecedente':('ANTECEDENTE DOCUMENTADO','#7e7b75'),
        'opcional':('EXTENSIÓN CONDICIONAL','#876895')}


def node(id,title,body,inputs='',status='pendiente',kind='proceso'):
    return dict(id=id,title=title,body=body.split('|'),inputs=inputs.split() if inputs else [],status=status,kind=kind)


SECTIONS=[
('01','Fuentes originales','Cinco entradas independientes; el rendimiento GDHY y el calendario de secano no son la misma fuente.',[
node('S1','Rendimiento GDHY original','Archivos anuales NetCDF / nc4.|Versión alineada v1.2 + v1.3.|1981–2016; cuadrícula de 0,5°.|Maíz; conservar unidades originales.|No atribuir al GDHY separación secano/riego.',status='antecedente',kind='datos'),
node('S2','Calendario y fenología','GGCMI Phase 3 v1.01: extremos.|Calendario operativo regional v4.|Sistema hídrico seleccionado: secano.|Correspondencia con estadios técnicos.|Las fechas intermedias son estimadas.',status='hecho',kind='datos'),
node('S3','Clima diario ERA5-Land','Colección diaria utilizada en GEE.|Temperatura máxima del aire a 2 m.|Precipitación diaria acumulada.|Celdas climáticas nativas; día UTC.|No promediar antes de detectar episodios.',status='hecho',kind='datos'),
node('S4','ONI mensual centrado','Archivo oficial ONI v6 archivado.|Índice trimestral con centro mensual.|Conservar valor continuo y fecha.|No confundir mes con dato diario nuevo.|Guardar fuente, versión y hash.',status='hecho',kind='datos'),
node('S5','MJO: índice diario RMM','Archivo oficial BoM / Wheeler–Hendon.|Fecha, RMM1, RMM2, fase y amplitud.|Conservar códigos de valores ausentes.|Documentar cambio metodológico 2014.|La fuente está disponible; integración pendiente.',status='parcial',kind='datos')]),
('02','Del rendimiento puro al dominio de análisis','La selección de píxeles heredada debe conservar su procedencia; no imponer 36 años como requisito universal.',[
node('Y1','Inventario y limpieza de GDHY','Revisar variable, unidades y fill values.|Concatenar años y comprobar duplicados.|Auditar/reconstruir el eje temporal.|Normalizar longitudes y coordenadas.|Preservar los datos originales intactos.','S1','antecedente'),
node('Y2','Detrendido del rendimiento','Ajuste lineal por píxel documentado.|Serie residual: y menos tendencia.|NetCDF limpio actualmente disponible.|Una tendencia no identifica su causa.|Auditar el procedimiento original y sus metadatos.','Y1','antecedente'),
node('Y3','Antecedente exploratorio SST','Cruces rendimiento–SST por mes.|Archivos HDF5 de correlación existentes.|Recuperar índices espaciales exactos.|No repetir aquí la correlación SST.|No asumir selección por significancia.','Y2','antecedente'),
node('Y4','Píxeles seleccionados','Extraer índices H5 y cruzar coordenadas.|pixel_id, latitud, longitud, h5_index.|Muestra vigente: 10.923 píxeles de maíz.|Conservar años válidos: 35 o 36, según píxel.|No eliminar el píxel por un año ausente.','Y2 Y3','hecho','tabla'),
node('Y5','Rendimiento estandarizado','z_rend = residual centrado / desviación.|Calcular por píxel con años disponibles.|Serie constante: z no estimable.|Auditar unidades y convención de año.|No inferir pérdidas porcentuales del residual.','Y2 Y4','pendiente')]),
('03','Calendario, reglas de amenaza y soporte espacial','La ventana cambia con el lugar; el calendario típico no observa las fechas reales de cada temporada.',[
node('C1','Calendario de secano por píxel','Emparejar coordenadas exactas con GGCMI.|Conservar siembra y madurez típicas.|Homologar seis fases, versión regional v4.|Mantener límites y aproximaciones.|La máscara hídrica es del calendario.','S2 Y4','hecho'),
node('C2','Ventanas anuales agrícolas','Expandir el ciclo para 1981–2016.|Guardar inicio y fin, ambos incluidos.|Permitir ventanas que cruzan año.|Orden del maíz: EST–VEG–FLO–REP–FIL–MAT.|season_year identifica la temporada.','C1','hecho'),
node('C3','Reglas según los papers','Calor: Tmax y racha mínima de 2 días.|EST 34; VEG 34,6; FLO/REP 33,7 °C.|FIL 32,7 °C: referencia adoptada Agronomy.|MAT: precipitación >10 mm por día.|Guardar operador, duración y fuente exactos.','S3','hecho'),
node('C4','Soporte climático válido','Intersectar celdas nativas y píxel GDHY.|Separar máscara espacial y hueco temporal.|58 píxeles: soporte espacial parcial fijo.|36 temporadas completas sobre ese soporte.|Guardar fracción disponible; no es área de maíz.','S3 Y4','hecho'),
node('C5','Detectar antes de agregar','Aplicar regla dentro de cada celda nativa.|Racha de calor que cumple duración = episodio.|Incluir todos sus días como afectados.|Recortar según la ventana de la fase.|No sumar episodios entre fases como eventos únicos.','C2 C3 C4','hecho')]),
('04','Dos escalas temporales y tablas limpias','Sin celdas combinadas: repetir las llaves; mantener cero válido y valor ausente como situaciones distintas.',[
node('T1','Base climática diaria','Una fila: píxel × temporada × fase × fecha.|Fracción del soporte afectada ese día.|Ponderar celdas por coseno de latitud.|Conservar flags, fechas y conteo diario.|Cachés completos; conservar soporte fijo.','C5','hecho','tabla'),
node('T2','Exposición anual por fase','Una fila: píxel × temporada × fase.|Episodios: promedio espacial de conteos.|Días afectados equivalentes = suma de fracciones.|episodios_100d = 100 × episodios / días válidos.|% afectado = 100 × días equivalentes / días válidos.','T1','hecho','tabla'),
node('T3','Tabla A0: frecuencias + ONI','ONI de ventana: promedio ponderado por días.|Frío ≤−0,5; cálido ≥+0,5; neutral entre ambos.|2.359.368 filas y pares climáticos–ONI válidos.|MAT: episodios y episodios/100 días vacíos.|SQLite + CSV; campos de cobertura y trazabilidad.','T2 S4','hecho','tabla'),
node('T4','Tabla A: añadir rendimiento','Unir por píxel y escenario de año de rendimiento.|Conservar yield_year, z_rend y par válido.|Dos escenarios: misma etiqueta / año de MAT.|Una temporada sin rendimiento queda sin pareja.|Cruce legado de conteos existe; ampliar a exposición/z.','T3 Y5 D1','parcial','tabla'),
node('T5','Tabla B: clima + ONI + MJO diarios','Una fila: píxel × temporada × fase × fecha.|Fecha, mes, fracción afectada y temporada.|ONI del mes y su categoría, distintos a ventana.|Fase MJO, amplitud, estado y validez.|Reconstruir desde cachés, sin nueva GEE si cubren todo.','T1 S4 S5','pendiente','tabla')]),
('05','Seis diagnósticos que condicionan la interpretación','Son controles metodológicos: su posición en el esquema no significa que todos estén resueltos.',[
node('D1','Año del rendimiento','Contrastar metadatos GDHY y fin del ciclo.|Revisar faltantes de 1981 y 2016.|Mantener ambos escenarios como sensibilidad.|El año final de MAT es una aproximación.|No elegir correspondencia por mayor R².','S1 C2 Y5','parcial','diagnostico'),
node('D2','Qué ONI usa Pearson','Código: ONI continuo ponderado por días.|El signo solo intervino en resúmenes auxiliares.|CSV antiguo sin columna llamada regla.|Auditar variable, operador y umbral guardados.|Categorías oficiales del análisis: ±0,5 °C.','S4 T3','hecho','diagnostico'),
node('D3','Tendencia y décadas ONI','Pendiente de exposición frente al año.|Reparto de categorías ONI entre décadas.|Diagnóstico global y por píxel calculado.|Sensibilidad sin tendencia ya calculada.|Diagnóstico por regiones aún pendiente.','T3 U1','parcial','diagnostico'),
node('D4','Dependencia del rendimiento','Correlación de z entre píxeles del mismo país.|Comparar con pares de países diferentes.|Cuantificar señal compartida del GDHY.|Conservar el detalle de píxel.|No tratar los píxeles como réplicas independientes.','Y5 U1','pendiente','diagnostico'),
node('D5','Colinealidad entre exposiciones','Matriz de correlación de seis fases.|VIF y número de condición por píxel.|Identificar exposición compartida entre fases.|OLS simultáneo de seis fases: diagnóstico.|No asignar importancia por máximo coeficiente.','T4','pendiente','diagnostico'),
node('D6','Solapamiento de ventanas','Comprobar fechas y límites de fases.|Si no se solapan: sumar días afectados.|Si se solapan: usar unión de días.|Los episodios no se suman entre fases.|Determina cómo construir bloques de exposición.','C2 T1','pendiente','diagnostico')]),
('06','Medidas descriptivas y ONI → amenaza','Resultado principal: diferencias absolutas de exposición; la sensibilidad conserva el análisis original.',[
node('A1','Medidas históricas por lugar','Promedio de temporadas completas.|Episodios/100 días y % afectado, separados.|Conservar ceros, n y duración de la ventana.|Calor con escala común; MAT independiente.|Mapa 1 y, si hace falta, percentiles por fase.','T2 U4','pendiente','analisis'),
node('A2','Categorías y contrastes ONI','Por píxel/fase: medias y n de frío/neutral/cálido.|Cálido−neutral y frío−neutral.|Calor: episodios/100 días; MAT: % afectado.|196.614 medias; 131.076 contrastes calculados.|129.405 IC estimados; 1.671 no estimados.','T3 U2','hecho','analisis'),
node('A3','Sensibilidad de tendencia','Residuos lineales de exposición por píxel/fase.|Reajustar la tendencia en cada réplica bootstrap.|Mismos sorteos que en el análisis original.|Comparar magnitud, signo e intervalos.|No recortar anomalías negativas a cero.','A2 D3','hecho','analisis'),
node('A4','Síntesis ONI por región','Usar regiones definidas antes del contraste.|Agregar por año con ponderación documentada.|Diferencias e IC por temporadas compartidas.|Reportar n por categoría y cobertura espacial.|Inferencia regional aún pendiente.','A2 A3 U1 U2','pendiente','analisis')]),
('07','Bloque 4: MJO → amenaza','Escala diaria: distinguir coincidencia meteorológica de la simple presencia de MJO durante una ventana.',[
node('M1','Control y estado diario MJO','Validar fecha, RMM1/RMM2 y amplitud.|Estado débil: amplitud ≤1.|Estado activo: amplitud >1; fases 1–8.|Valor ausente no equivale a débil.|Preservar orden circular 1→8→1.','S5 T5','pendiente','analisis'),
node('M2','Estratificar mes y ONI','Separar por fase agrícola, mes y ONI mensual.|Usar fracción afectada observada cada día.|Definir dominio trópicos/subtrópicos antes.|Fijar agrupaciones y rezagos 0/5/10 días.|Mantener n de días y temporadas por estado.','M1 T5 E3','pendiente','analisis'),
node('M3','Referencia comparable','Referencia del mismo mes y categoría ONI.|Promedio condicionado a la mezcla de estados.|Incluye los mismos días MJO analizados.|Δ = probabilidad del estado − referencia.|No etiquetar la referencia como “sin MJO”.','M2','pendiente','analisis'),
node('M4','Incertidumbre MJO','Bootstrap por temporada; mismos años por región.|No remuestrear días como si fueran independientes.|Documentar persistencia y pasajes MJO.|Mostrar estados con IC, n y tasa base.|Sensibilidad al cambio del índice desde 2014.','M3 U1 U2','pendiente','analisis'),
node('M5','Resultados y mapa MJO','Perfiles ONI × MJO con puntos e intervalos.|Diferencias en puntos porcentuales.|Mapa 3 trimestral en dominio predefinido.|Escalas simétricas congeladas y pocos paneles.|Resúmenes previos sin IC: solo antecedentes.','M4 U4','pendiente','salida')]),
('08','Cruces con rendimiento estandarizado','Análisis observacional, con correspondencia anual explícita y sin atribución causal ni conversión a pérdidas.',[
node('R1','Cobertura y pares completos','Validar unión Tabla A y escenario temporal.|Incluir años disponibles: 35 o 36 por píxel.|Conservar ceros climáticos y residuos negativos.|No duplicar un rendimiento anual por cada día.|Guardar n válido de cada asociación.','T4 D1','pendiente','analisis'),
node('R2','ONI → rendimiento','Media de z por frío, neutral y cálido.|Diferencias de medias con IC por años.|Pearson con ONI continuo de ventana.|n por categoría y escenario temporal.|Resultado directo, separado de las amenazas.','R1 S4 U2','pendiente','analisis'),
node('R3','Amenaza → rendimiento','Pearson marginal por fase: % afectado frente a z.|IC bootstrap por años y síntesis regional.|No detrendar exposición en el análisis principal.|Interpretar efecto compartido con fases vecinas.|No confundir r con pérdida o importancia única.','R1 D5 U2','pendiente','analisis'),
node('R4','Robustez e historias anuales','Spearman como comprobación secundaria.|Dispersión regional: un punto por año.|Series de z con eje común y ONI de fondo.|Revisar extremos, ceros y n; no excluirlos a conveniencia.|Rendimiento detrendido no es señal solo climática.','R2 R3 D4','pendiente','analisis'),
node('R5','Mapa 4 y síntesis regional','Pearson por fase; límites fijos ±0,6.|Banda |r|<0,33 solo referencia aproximada.|Ese corte no ajusta n, autocorrelación o multiplicidad.|Rayado por n<30; diagnosticar VIF por separado.|Inferencia formal regional e IC laterales.','R3 R4 U4','pendiente','salida')]),
('09','Bloques de exposición y modelos secundarios','Separar unidades y mantener explícita la variación compartida; el OLS de seis fases no es el resultado principal.',[
node('K1','Construir bloques a priori','Vegetativo: EST + VEG.|Reproductivo: REP + FLO + FIL.|MAT: lluvia de madurez, variable distinta.|Días afectados sobre unión de ventanas válidas.|Revisar D6; no sumar episodios.','T1 D6','pendiente','analisis'),
node('K2','Modelo de 2–3 predictores','Relacionar bloques y z de rendimiento.|Calcular VIF del diseño final.|Si VIF>5: no interpretar coeficientes separados.|Mantener diagnósticos y cobertura.|No repartir causalmente el R² entre fases.','K1 R1 D5','pendiente','analisis'),
node('K3','Aporte incremental','Modelo reproductivo frente a añadir vegetativo.|Cambio de R² ajustado.|IC bootstrap por años compartidos.|No llamar al cambio “importancia de una fase”.|Describir límites de n≈36 y colinealidad.','K2 U2','pendiente','analisis'),
node('K4','OLS legado: solo diagnóstico','Seis fases: hasta 36 años y 7 parámetros.|Conservar VIF, condición y avisos de inestabilidad.|Validación por bloques de 6 años: exploratoria.|Detrendido previo pudo usar toda la serie.|Mapa de “fase más importante”: pospuesto.','T4 D5','antecedente','diagnostico')]),
('10','Extensiones condicionales y decisiones previas','Estas ramas no se convierten automáticamente en resultados principales ni se deciden buscando significancia.',[
node('E1','Extensión 4b: MJO anual','Por temporada/fase: fracción de días en MJO activa.|O pares de fases fijados de antemano.|Pearson con amenaza y con z.|Examinar si añade información sobre la amenaza.|Agrupar antes de mirar; solo si se justifica.','T5 R1 M4','opcional','analisis'),
node('E2','Rendimiento bajo: solo regional','Definición previa: z ≤ percentil 20 por píxel.|Sensibilidades p10 y p25, predefinidas.|Riesgo relativo e intervalos regionales.|Marcar grupos sin estimación; no recortar infinitos.|Escala log2, centro RR=1; rango 1/4 a 4.','R1 U1 U2','opcional','analisis'),
node('E3','Protocolo antes de ampliar','Fijar regiones y lista de píxeles.|Dominio y agrupaciones MJO; rezagos 0/5/10 días.|Umbrales ENSO “severo” solo como sensibilidad previa.|MJO por estado: fijar mínimos; base previa 30 días/3 temporadas.|Congelar familias de comparaciones y escalas.','U1','pendiente','diagnostico')]),
('11','Controles transversales, incertidumbre y diseño','Se aplican a todas las ramas: no son una etapa que deba esperarse hasta el final.',[
node('U1','Regiones y dependencia espacial','Polígonos/regla definidos antes del resultado.|Guardar asignación pixel_id → región.|Explicitar ponderación regional.|D4: señal compartida dentro y entre países.|No contar píxeles como evidencia independiente.','Y4','pendiente','diagnostico'),
node('U2','Bootstrap por temporadas','ONI actual: 2.000 réplicas; semilla 20261019.|Mismos años para todos los píxeles de cada región.|Mínimo 5 temporadas/grupo para IC ONI actual.|IC si ≥95 % de réplicas son estimables.|No remuestrear píxeles, días o países como réplicas.|Persistencia entre temporadas: limitación explícita.','T3','parcial','diagnostico'),
node('U3','Multiplicidad y elegibilidad','Reportar número de comparaciones por familia.|FDR solo exploratorio, dominio documentado.|Días/temporadas mínimos según producto.|No ocultar estimaciones por IC que incluya cero.|Cero, faltante, no elegible y exterior: distintos.','E3','pendiente','diagnostico'),
node('U4','Escalas y figuras congeladas','Equal Earth; celdas 0,5°, sin interpolar.|Medidas: cuantiles positivos; cero propio.|Contrastes: 7–9 clases, ±P98 de |Δ|.|Calor común; MAT con unidad/escala propias.|Histogramas y recuadros regionales con misma escala.','A1 A2 M5 R5','parcial','salida'),
node('U5','Trazabilidad y límites','Llaves únicas; fuentes, versiones, hashes y código.|Par válido explícito y cobertura espacial/temporal.|Archivos completos: señal completed.json.|Asociación histórica; no causalidad o predicción validada.|No convertir residuos a pérdidas económicas.','T3 T4 T5','parcial','diagnostico')]),
('12','Productos finales para el manuscrito','Cada figura responde una pregunta y conserva sus unidades, cobertura e incertidumbre.',[
node('O1','Mapa 1 · exposición','Episodios/100 días y % afectado, separados.|Cinco fases de calor y lluvia de MAT.|Mismas escalas entre paneles comparables.|Versión absoluta y percentil por fase si se requiere.|Tablas de cobertura y descripción del dominio.','A1 U4','pendiente','salida'),
node('O2','Mapa 2 · ONI → amenaza','Dos contrastes × seis fases.|Original como principal; sin tendencia como sensibilidad.|Calor y MAT separados; n e IC en tablas.|Escalas idénticas entre versiones.|Mapas globales ya generados; síntesis regional pendiente.','A2 A3 A4 U4','parcial','salida'),
node('O3','Mapa 3 · MJO → amenaza','Dominio predefinido y paneles trimestrales.|Perfiles circulares ONI × MJO con intervalos.|Tasa base, días y temporadas por celda.|Diferencias estratificadas por mes y ONI.|Presentar también estados no concluyentes.','M5 U3 U4','pendiente','salida'),
node('O4','Mapa 4 · amenaza → rendimiento','Pearson marginal en seis fases.|Dispersión y series regionales por año.|Ambos escenarios de año como sensibilidad.|Bloques, VIF y aporte incremental como complemento.|Sin mapa de importancia máxima por fase.','R5 K3 U4','pendiente','salida'),
node('O5','Síntesis y entrega reproducible','Tablas de estimaciones, n, IC y supuestos.|Resultados principales frente a sensibilidades.|Límites GDHY, calendario, clima e índices.|Datos limpios SQLite/CSV y figuras vectoriales.|Redacción de asociaciones observadas, sin causalidad.','O1 O2 O3 O4 E1 E2 U5','pendiente','salida')]),
('13','Qué variables se van incorporando','Contratos de las tablas: campos presentes y campos previstos; los nombres diarios nuevos deben congelarse al construir la Tabla B.',[
node('V1','Identificación y tiempo','pixel_id; latitud; longitud.|temporada; fase agrícola.|inicio; fin; dias_ventana.|dias_validos; fecha y mes en Tabla B.|Llave anual: píxel, temporada, fase.|Llave diaria: añadir fecha.','Y4 C2 T3 T5','parcial','tabla'),
node('V2','Medidas y regla climática','episodios; conteo_original.|dias_afectados_equiv; pct_dias_afectados.|episodios_100d; fracción diaria afectada.|variable_climatica; operador; umbral.|duracion_min_dias; unidad_conteo_origen.|MAT: conteo en días, episodios no aplican.','C3 T1 T2','hecho','tabla'),
node('V3','Índices y rendimiento','Anual: oni_ventana; cat_oni.|Diario: oni_mes; cat_oni_mes.|Diario: RMM1, RMM2, amplitud y estado MJO.|yield_year; escenario temporal; z_rend.|Par válido exposición–rendimiento / ONI–rendimiento.|MJO anual opcional: fracción de días por estado.','T3 T4 T5 E1','parcial','tabla'),
node('V4','Cobertura y validez','calidad_origen; fraccion_cobertura_origen.|estado_cobertura; cobertura_temporal_completa.|estado_cobertura_espacial.|fraccion_area_climatica_util.|celdas_validas_soporte_fijo; celdas_excluidas_sin_datos.|recuperado_desde_cache; par_frecuencia_oni_valido.','C4 T3 U5','hecho','tabla'),
node('V5','Estimación e incertidumbre','medida; unidad; categoría / contraste.|n_temporadas; n_categoria; n_neutral.|media; diferencia; límites IC95.|replicas_estimables; estado_ic.|Pendiente; diferencia sin tendencia y cambio.|Pearson, Spearman, VIF y ΔR² ajustado según rama.','A2 A3 M4 R3 K3','parcial','tabla')])]


class Painter:
    def __init__(self,w,h,pdf_path=None):
        self.w=w;self.h=h;self.parts=[];self.c=canvas.Canvas(str(pdf_path),pagesize=(w,h)) if pdf_path else None
    def rect(self,x,y,w,h,fill='#ffffff',stroke=None,r=9,dash=False):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke or "none"}" stroke-width="1"'+(' stroke-dasharray="6 4"' if dash else '')+'/>')
        if self.c:
            c=self.c;c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke or fill));c.setLineWidth(.8);c.setDash([5,4] if dash else [])
            c.roundRect(x,self.h-y-h,w,h,r,stroke=bool(stroke),fill=1);c.setDash([])
    def text(self,x,y,text,size=16,color='#263d46',bold=False):
        self.parts.append(f'<text x="{x}" y="{y}" font-family="Segoe UI,Arial,sans-serif" font-size="{size}" fill="{color}"'+(' font-weight="600"' if bold else '')+'>'+escape(text)+'</text>')
        if self.c:
            self.c.setFillColor(HexColor(color));self.c.setFont('FlowBold' if bold else 'Flow',size);self.c.drawString(x,self.h-y,text)
    def line(self,points,color='#9eacb2',width=1,arrow=False,dash=False):
        path=' '.join(('M' if i==0 else 'L')+f'{x},{y}' for i,(x,y) in enumerate(points))
        self.parts.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="{width}"'+(' stroke-dasharray="5 4"' if dash else '')+'/>')
        if self.c:
            c=self.c;c.setStrokeColor(HexColor(color));c.setLineWidth(width);c.setDash([5,4] if dash else []);p=c.beginPath();p.moveTo(points[0][0],self.h-points[0][1])
            for x,y in points[1:]:p.lineTo(x,self.h-y)
            c.drawPath(p);c.setDash([])
        if arrow:
            a,b=points[-2:];ang=math.atan2(b[1]-a[1],b[0]-a[0]);length=7
            for delta in [-.45,.45]:self.line([b,(b[0]-length*math.cos(ang+delta),b[1]-length*math.sin(ang+delta))],color,width)
    def save(self,svg_path=None):
        if self.c:self.c.showPage();self.c.save()
        if svg_path:Path(svg_path).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}pt" height="{self.h}pt" viewBox="0 0 {self.w} {self.h}"><title>Flujo completo rendimiento, amenazas, ONI y MJO</title><rect width="100%" height="100%" fill="white"/>'+''.join(self.parts)+'</svg>',encoding='utf-8')


def wrap(text,width,size,font='Flow'):
    lines=[];current=''
    for word in text.split():
        trial=(current+' '+word).strip()
        if pdfmetrics.stringWidth(trial,font,size)>width and current:lines.append(current);current=word
        else:current=trial
    if current:lines.append(current)
    return lines


def draw_node(p,n,box,operational=True,scale=1):
    x,y,w,h=box;pad=18*scale;size=15.5*scale;line_height=21*scale
    color=COLORS[n['kind']];p.rect(x,y,w,h,stroke='#ccd6d9',dash=n['status']=='opcional')
    p.rect(x,y,5*scale,h,fill=color,r=0)
    p.text(x+pad,y+24*scale,n['id'],12*scale,color,True)
    if operational:
        label,sc=STATUS[n['status']];p.text(x+pad+40*scale,y+24*scale,label,9*scale,sc,True)
    title=wrap(n['title'],w-2*pad,19*scale,'FlowBold')
    yy=y+52*scale
    for text in title:p.text(x+pad,yy,text,19*scale,color,True);yy+=24*scale
    yy+=6*scale
    for item in n['body']:
        lines=wrap(item,w-2*pad-11*scale,size)
        for i,line in enumerate(lines):
            p.text(x+pad+(0 if i==0 else 10*scale),yy,('• ' if i==0 else '')+line,size);yy+=line_height
        yy+=3*scale
    footer='Entradas: '+(', '.join(n['inputs']) if n['inputs'] else 'fuente original')
    if yy>y+h-38*scale+1e-5:raise ValueError(f'Texto desborda {n["id"]}: {yy} > {y+h-38*scale}')
    for i,line in enumerate(wrap(footer,w-2*pad,10.5*scale)):
        p.text(x+pad,y+h-22*scale+i*12*scale,line,10.5*scale,'#647984')


def height_node(n,width,scale=1):
    title_lines=len(wrap(n['title'],width-36*scale,19*scale,'FlowBold'))
    nlines=sum(len(wrap(t,width-47*scale,15.5*scale)) for t in n['body'])
    return (52+6+38)*scale+title_lines*24*scale+nlines*21*scale+len(n['body'])*3*scale


def layout_master():
    width=2240;margin=70;gap=24;y=190;layouts={};sections=[]
    for code,title,subtitle,nodes in SECTIONS:
        header_y=y;y+=82
        columns=3 if len(nodes)==6 else len(nodes);boxw=(width-2*margin-gap*(columns-1))/columns
        for first in range(0,len(nodes),columns):
            row=nodes[first:first+columns];h=max(height_node(n,boxw) for n in row)
            for j,n in enumerate(row):layouts[n['id']]=(margin+j*(boxw+gap),y,boxw,h)
            y+=h+30
        sections.append((code,title,subtitle,header_y,y,nodes));y+=26
    return width,y+150,layouts,sections


def draw_master(out,operational):
    W,H,boxes,sections=layout_master();stem='flujo_completo_estado_actual' if operational else 'flujo_completo_manuscrito'
    p=Painter(W,H,out/(stem+'.pdf'))
    p.text(70,68,'Rendimiento agrícola, amenazas por fase, ONI y MJO',36,bold=True)
    p.text(70,108,'Flujo metodológico completo · maíz · 10.923 píxeles · 0,5° · 1981–2016',21,'#56707d')
    p.text(70,143,'Cada flecha indica una dependencia de datos o un control; los ID permiten seguir las conexiones entre módulos.',15,'#647984')
    # Cross-module dependencies travel outside the cards. Inputs are repeated inside
    # each card so that every edge remains traceable in modular/printed versions.
    allnodes={n['id']:n for s in SECTIONS for n in s[3]}
    links=[]
    for n in allnodes.values():
        for src in n['inputs']:
            if src not in allnodes:raise ValueError('Entrada desconocida '+src)
            a=boxes[src];b=boxes[n['id']]
            if abs(a[1]-b[1])<1 and a[0]<b[0] and abs((a[0]+a[2]+24)-b[0])<2:
                points=[(a[0]+a[2],a[1]+a[3]/2),(b[0],b[1]+b[3]/2)]
            else:
                left=(len(links)%2==0);lane=18+(len(links)%5)*7 if left else W-18-(len(links)%5)*7
                sy=a[1]+a[3]+10;ty=b[1]-12
                points=[(a[0]+a[2]/2,a[1]+a[3]),(a[0]+a[2]/2,sy),(lane,sy),(lane,ty),(b[0]+b[2]/2,ty),(b[0]+b[2]/2,b[1])]
            p.line(points,'#c4d0d4',.7,arrow=True,dash=n['status']=='opcional');links.append([src,n['id']])
    for code,title,subtitle,top,bottom,nodes in sections:
        p.rect(61,top-7,W-122,66,fill='#edf2f3',r=6)
        p.text(78,top+18,code,21,'#527786',True);p.text(126,top+18,title,23,bold=True)
        p.text(78,top+45,subtitle,14,'#5b717b')
        for n in nodes:draw_node(p,n,boxes[n['id']],operational)
    y=H-110
    p.text(70,y,'Lectura: las ramas ONI, MJO y rendimiento se conectan mediante llaves; no todas las asociaciones son causales.',16,bold=True)
    p.text(70,y+29,'Borde discontinuo: extensión condicional. Las entradas citadas por ID siguen siendo legibles al separar módulos.',15,'#647984')
    if operational:p.text(70,y+57,'Estado al 20-10-2026: calculado/verificado, parcial, planificado, antecedente o extensión; no confundir disponibilidad con validación completa.',14,'#647984')
    else:p.text(70,y+57,'Esquema del diseño completo: incluye análisis principales, diagnósticos, sensibilidades y extensiones; no certifica que todos estén ejecutados.',14,'#647984')
    p.save(out/(stem+'.svg'))
    return W,H,boxes,sections,links


def modules_pdf(out):
    W,H=landscape(A3);c=canvas.Canvas(str(out/'flujo_por_modulos_A3.pdf'),pagesize=(W,H))
    for code,title,subtitle,nodes in SECTIONS:
        p=Painter(W,H);p.c=c
        p.text(42,52,code+' · '+title,21,bold=True)
        lines=wrap(subtitle,W-84,11.5)
        for i,line in enumerate(lines):p.text(42,78+i*15,line,11.5,'#647984')
        cols=3 if len(nodes)>3 else len(nodes);gap=18;margin=42;bw=(W-2*margin-gap*(cols-1))/cols;s=1.05;y=122
        while s>.6:
            used=122+sum(max(height_node(n,bw,s) for n in nodes[start:start+cols])+22 for start in range(0,len(nodes),cols))
            if used<=H-42:break
            s-=.02
        for start in range(0,len(nodes),cols):
            row=nodes[start:start+cols];h=max(height_node(n,bw,s) for n in row)
            for j,n in enumerate(row):draw_node(p,n,(margin+j*(bw+gap),y,bw,h),True,s)
            y+=h+22
        if y>H-42:raise ValueError('Página modular desborda: '+code)
        p.text(42,H-22,'Maíz · 1981–2016 · Las entradas por ID enlazan con los demás módulos del diagrama completo.',9,'#647984')
        c.showPage()
    c.save()


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=DEFAULT);p.add_argument('--replace',action='store_true');args=p.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=args.replace)
    for name,file in [('Flow','segoeui.ttf'),('FlowBold','seguisb.ttf')]:pdfmetrics.registerFont(TTFont(name,str(Path('C:/Windows/Fonts')/file)))
    W,H,boxes,sections,edges=draw_master(out,False);draw_master(out,True);modules_pdf(out)
    payload=dict(titulo='Flujo completo rendimiento–amenazas–ONI–MJO',fecha='2026-10-20',ancho_pt=W,alto_pt=H,secciones=SECTIONS,conexiones=edges)
    (out/'contenido_editable.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    mmd=['flowchart TB']
    for code,title,subtitle,nodes in SECTIONS:
        mmd.append(f'  subgraph MOD{code}["{code} · {title}"]')
        for n in nodes:mmd.append('    '+n['id']+'["'+n['id']+' · '+n['title'].replace('"','')+'<br/>'+'<br/>'.join(n['body']).replace('"','')+'"]')
        mmd.append('  end')
    for a,b in edges:mmd.append(f'  {a} --> {b}')
    (out/'flujo_completo.mmd').write_text('\n'.join(mmd),encoding='utf-8')
    (out/'LEEME.md').write_text('''# Diagrama completo para el manuscrito

**flujo_completo_manuscrito.pdf / .svg**: póster vectorial completo, sin etiquetas de avance. SVG permite editar textos y cajas; PDF se amplía sin pixelarse. Esquema del diseño completo, no declaración de ejecución de todas las ramas.

**flujo_completo_estado_actual.pdf / .svg**: mismo diagrama con estados al 20 de octubre de 2026. Distingue antecedentes documentados, cálculos verificados, trabajo parcial, planificación y extensiones condicionales.

**flujo_por_modulos_A3.pdf**: 13 módulos legibles, un módulo por página A3 horizontal. Sirve para lectura y revisión cuando el póster gigante no cabe en una página del manuscrito. Reducir todo el póster a A4 haría ilegible su detalle; usarlo como lámina desplegable/material suplementario o distribuir los módulos.

**contenido_editable.json** y **flujo_completo.mmd** conservan contenidos y dependencias para editar o regenerar el esquema. El script de generación queda en la carpeta de scripts de trabajo.

## Pie sugerido

Flujo de integración de rendimiento GDHY, calendario fenológico, amenazas climáticas diarias e índices ONI y MJO para el análisis observacional de maíz en 10.923 píxeles de 0,5° durante 1981–2016. Se distinguen las tablas anual y diaria, los diagnósticos de correspondencia temporal y dependencia, los análisis principales y sus sensibilidades. Las extensiones condicionales no se interpretan como resultados principales. El rendimiento anual no se replica como observación independiente por cada día o fase.

## Fuentes y alcance

- Plan aportado: arquitectura_analisis_ONI_MJO_rendimiento (2).md, versión final v3; las afirmaciones se contrastaron con scripts, tablas y registros de ejecución locales.
- GDHY: Iizumi y Sakai (2020), https://www.nature.com/articles/s41597-020-0433-7 ; datos alineados https://doi.pangaea.de/10.1594/PANGAEA.909132 .
- Calendario: procedencia GGCMI Phase 3 v1.01, DOI https://doi.org/10.5281/zenodo.5062513 y correspondencia operativa regional-v4 del proyecto.
- ERA5-Land: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land ; para los cálculos, colección diaria y reglas registradas en plan_ejecucion.json.
- MJO: https://www.bom.gov.au/climate/mjo/index.shtml ; método https://www.bom.gov.au/climate/mjo/about/WH04.pdf .
- ONI: archivo local ONI_v6_2026-10-08.html; no se sustituyó la versión usada.
- Reglas: tabla humana y plan de seis fases; FIL conserva 32,7 °C conforme a la referencia adoptada de Agronomy. La discrepancia 32,9 °C en otra publicación no se corrige silenciosamente.

La limpieza/detrendido históricos están documentados y existen archivos procesados, pero aquí no se volvieron a ejecutar desde el rendimiento bruto. El esquema no presenta ese antecedente como una auditoría nueva. La muestra de secano deriva del calendario; no se atribuye automáticamente al GDHY una desagregación hídrica. D1, D4, D5, D6, regiones y la integración diaria MJO requieren trabajo antes de cerrar el manuscrito final. D3 global, sensibilidad ONI y mapas actuales sí están calculados. El corte |r|≈0,33 es orientativo para n≈36 y una sola prueba, no una regla universal de significancia.
''',encoding='utf-8')
    print(json.dumps(dict(carpeta=str(out),nodos=sum(len(s[3]) for s in SECTIONS),conexiones=len(edges),dimensiones_pt=[W,H]),ensure_ascii=False),flush=True)


if __name__=='__main__':main()
