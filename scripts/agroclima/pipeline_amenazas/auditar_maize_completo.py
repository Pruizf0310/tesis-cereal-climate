"""Read-only Excel/rules/result comparison; stream the complete annual output."""
import csv
import hashlib
import json
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


def main():
    import numpy as np
    import pandas as pd
    base=Path(r'C:\Users\paola\Tesis\03_Resultados\Agroclima\vigente')
    run=base/'ejecuciones/maize_seis_fases_GEE_1981_2016'
    plan=json.loads((run/'plan_ejecucion.json').read_text(encoding='utf-8'))
    status=json.loads((run/'estado_paquete.json').read_text())
    workbook=base/'amenazas/tabla_maestra_revision_humana.xlsx'
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    master={}
    with zipfile.ZipFile(workbook) as z:
        shared=[''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)] if 'xl/sharedStrings.xml' in z.namelist() else []
        for row in ET.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:sheetData/m:row',ns):
            values={}
            for cell in row.findall('m:c',ns):
                v=cell.find('m:v',ns); inline=cell.find('m:is',ns)
                value=v.text if v is not None else ''.join(inline.itertext()) if inline is not None else ''
                if cell.get('t')=='s':value=shared[int(value)]
                values[re.sub('[0-9]','',cell.get('r'))]=value
            if values.get('A')=='Maíz':master[values['B']]=values
    phases=['EST','VEG','REP','FLO','FIL','MAT']
    assert set(master)==set(phases)
    pixels=pd.read_csv(Path(plan['config']['yield_nc']).parent.parent/'Pixeles_correlacion_vigentes/pixeles_maize.csv')
    mapping=dict(zip(pixels.pixel_id,range(len(pixels))))
    first,last=plan['first_year'],plan['last_year'];ny=last-first+1
    expected=len(pixels)*ny
    seen=np.zeros(expected*6,dtype=bool)
    checks={p:dict(rows=0,complete=0,incomplete=0,positive_complete=0,expected_rows=expected,values={}) for p in phases}
    duplicates=0;invalid=0;coverage_errors=0;total=0
    columns=['variable','threshold','operator','min_days','count_unit','source']
    path=run/'resumen_GDHY_anual.csv'
    for chunk in pd.read_csv(path,chunksize=100000):
        idx=chunk.pixel_id.map(mapping)
        phaseidx=chunk.phase.map(dict(zip(phases,range(6))))
        valid=idx.notna() & phaseidx.notna() & chunk.season_year.between(first,last)
        invalid+=int((~valid).sum())
        slots=((idx[valid].astype('int64')*ny+chunk.loc[valid,'season_year']-first)*6+phaseidx[valid].astype('int64')).to_numpy()
        unique=np.unique(slots)
        duplicates+=len(slots)-len(unique)+int(seen[unique].sum());seen[unique]=True
        good=chunk.quality=='OK'
        coverage_errors+=int((good & ((chunk.complete_cells!=chunk.native_cells) | (chunk.valid_cell_days!=chunk.expected_cell_days))).sum())
        for phase,sub in chunk.groupby('phase'):
            c=checks[phase];complete=sub[sub.quality=='OK']
            c['rows']+=len(sub);c['complete']+=len(complete);c['incomplete']+=len(sub)-len(complete)
            c['positive_complete']+=int((complete.mean_count_per_native_cell>0).sum())
            for col in columns:c['values'].setdefault(col,set()).update(sub[col].dropna().unique().tolist())
        total+=len(chunk)
        print(f'Revisadas {total:,} filas',flush=True)
    rows=[]
    for phase in phases:
        m=master[phase];c=checks[phase];rule=next(r for r in plan['rules'] if r['phase']==phase)
        assert all(c['values'][key]=={rule[key]} for key in columns),(phase,c['values'],rule)
        threshold=float(re.search(r'(\d+(?:[.,]\d+)?)',m['E'])[1].replace(',','.'))
        assert threshold==rule['threshold']
        assert all(m[k]==rule['original_rule'][field] for k,field in [('C','amenaza'),('D','variable_estadistico'),('E','umbral'),('F','duracion'),('G','conteo_eventos'),('I','fuente')])
        rows.append(dict(fase=phase,amenaza_excel=m['C'],variable_excel=m['D'],umbral_excel=m['E'],duracion_excel=m['F'],
                         variable_calculada=rule['variable'],umbral_calculado=rule['threshold'],operador=rule['operator'],
                         minimo_dias=rule['min_days'],unidad_conteo=rule['count_unit'],fuente=m['I'],
                         ventana_calculada='+'.join(plan['stages'][phase]),filas_calculadas=c['rows'],
                         cobertura_completa=c['complete'],cobertura_incompleta=c['incomplete'],
                         positivos_cobertura_completa=c['positive_complete'],coincide_variable_umbral_duracion=True,
                         limites_excel=m['J']))
        c['values']={k:sorted(v) for k,v in c['values'].items()}
    report=dict(status=status,workbook=str(workbook),workbook_sha256=hashlib.sha256(workbook.read_bytes()).hexdigest(),
                results=str(path),selected_pixels=len(pixels),years=[first,last],expected_rows=expected*6,
                actual_rows=total,missing_pixel_year_phase=int((~seen).sum()),duplicate_rows=duplicates,
                invalid_keys=invalid,complete_coverage_inconsistencies=coverage_errors,phases=checks,
                output_semantics='GEE queried daily maximum air temperature and daily precipitation; annual summaries downloaded. Daily arrays and episode dates not downloaded by this engine.',
                caveats='Variable/threshold match does not establish exact paper-window equivalence. VEG proxy V7-VT; REP R2 and FLO R1 split source R1-R3 and clip runs; MAT terminal R6 proxy for post-R6 dry-down. FIL table 32.7 vs documentary 32.9 remains unresolved.')
    assert status['status']=='COMPLETED' and total==expected*6 and not any([duplicates,invalid,coverage_errors,int((~seen).sum())])
    out=base/'diagnosticos/verificacion_maize_completo';out.mkdir(parents=True,exist_ok=True)
    (out/'verificacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with (out/'comparativo_excel_calculo.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    repo=Path(r'C:\Users\paola\Tesis\Repositorio\tesis-cereal-climate\outputs\agroclima_vigente\diagnosticos\verificacion_maize_completo')
    repo.mkdir(parents=True,exist_ok=True)
    for file in out.iterdir():
        if file.is_file():shutil.copy2(file,repo/file.name)
    print(json.dumps({'rows':total,'duplicates':duplicates,'missing':int((~seen).sum()),'phases':rows},ensure_ascii=False))


if __name__=='__main__':main()
