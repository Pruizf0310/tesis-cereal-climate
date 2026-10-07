"""Resumable maize six-rule runner; bounded memory, shared monthly climate cache."""
import argparse
import csv
import hashlib
import json
import re
import shutil
import time
from datetime import timedelta
from pathlib import Path

import pipeline as core

STAGES = {'EST': ['VE'], 'VEG': ['V7_VT'], 'REP': ['R2'],
          'FLO': ['R1'], 'FIL': ['R3', 'R4_R5'], 'MAT': ['R6']}


def windows(data, pixel, phase, first, last):
    key = f"{pixel['lat']:.2f},{pixel['lon']:.2f}"
    value = data['pixels'][key]
    indices = [i for i, t in enumerate(data['templates']) if t['code'] in STAGES[phase]]
    if len(indices) != len(STAGES[phase]):
        raise ValueError(f'Faltan bloques del calendario: {phase}')
    start_offset, end_offset = value[3+min(indices)], value[4+max(indices)]
    result = []
    for year in range(first, last+1):
        start = core.absolute_reference_date(year, value[0]-1+start_offset)
        end = core.absolute_reference_date(year, value[0]-1+end_offset)-timedelta(days=1)
        if end < start:
            raise ValueError('Ventana vacía o invertida')
        result.append(dict(pixel_id=pixel['pixel_id'], season_year=year, phase=phase,
                           start=start.isoformat(), end=end.isoformat(),
                           calendar_quality='estimated_intermediate_dates',
                           technical_stages='+'.join(STAGES[phase])))
    return result


def load_rules(path):
    rows = [r for r in csv.DictReader(path.open(encoding='utf-8-sig')) if r['cultivo']=='Maíz']
    if len(rows)!=6 or {r['fase'] for r in rows}!=set(STAGES):
        raise ValueError('Se requieren exactamente seis reglas vigentes de maíz')
    rules = []
    for row in rows:
        rain = row['fase']=='MAT'
        if ('Precipitación' if rain else 'Tmax') not in row['variable_estadistico']:
            raise ValueError(f"Variable no implementada: {row['variable_estadistico']}")
        if row['estado']!='REGLA DEFINIDA':
            raise ValueError(f"Regla pendiente: {row['fase']}")
        number = re.search(r'(\d+(?:[.,]\d+)?)', row['umbral'])
        if not number:
            raise ValueError('Umbral no numérico')
        rules.append(dict(phase=row['fase'], variable='precip_mm' if rain else 'tmax_c',
                          operator='>' if rain else '>=', threshold=float(number[1].replace(',','.')),
                          min_days=1 if rain else 2, count_unit='days' if rain else 'episodes',
                          source=row['fuente'], original_rule=row))
    return rules


def aggregate(root, destination):
    # Stream completed partitions, never load the full experiment in RAM.
    destination.mkdir(parents=True, exist_ok=True)
    for name in ['resumen_GDHY.csv','frecuencia_historica.csv','eventos.csv']:
        temporary = destination/(name+'.tmp')
        header = None
        with temporary.open('w',encoding='utf-8',newline='') as output:
            writer = csv.writer(output)
            for marker in sorted(root.glob('pixel_*/*/COMPLETED.json')):
                with (marker.parent/name).open(encoding='utf-8-sig',newline='') as source:
                    reader = csv.reader(source)
                    current = next(reader)
                    if header is None:
                        header=current; writer.writerow(header)
                    elif header!=current:
                        raise ValueError(f'Columnas incompatibles: {marker.parent/name}')
                    writer.writerows(reader)
        temporary.replace(destination/name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config',default=str(Path(__file__).with_name('config_maize_seis_fases.json')))
    parser.add_argument('--limit',type=int,default=0,help='0=todos; N=primeros N para comprobar')
    parser.add_argument('--aggregate',action='store_true',help='Solo consolidar particiones terminadas')
    args=parser.parse_args()
    if args.limit < 0:
        parser.error('--limit debe ser >=0')
    config_path=Path(args.config)
    c=json.loads(config_path.read_text(encoding='utf-8'))
    root=Path(c['output']); root.mkdir(parents=True,exist_ok=True)
    if args.aggregate:
        aggregate(root,root/'consolidado')
        if c.get('repository_results'):
            shutil.copytree(root/'consolidado',Path(c['repository_results'])/'consolidado',dirs_exist_ok=True)
        return
    import h5py
    with h5py.File(c['h5']) as f:
        ii,jj=f['lat_idx'][...],f['lon_idx'][...]
    with h5py.File(c['yield_nc']) as f:
        lat,lon=f['lat'][...],f['lon'][...]
    pixels=[dict(pixel_id=int(i)*len(lon)+int(j),h5_index=k,lat=float(lat[i]),
                 lon=float((lon[j]+180)%360-180)) for k,(i,j) in enumerate(zip(ii,jj))]
    if args.limit: pixels=pixels[:args.limit]
    rules=load_rules(Path(c['rules_csv']))
    data=json.loads((Path(c['calendar_dir'])/'maize-maize__rf.json').read_text(encoding='utf-8'))
    plan=dict(config=c,rules=rules,technical_windows=STAGES,selected_pixels=len(pixels),
              note='R1 FLO and R2 REP are disjoint operational proxies within the broader R1-R3 source window. Runs are clipped to these phase windows; do not sum phases as unique meteorological episodes. V7-VT is the available calendar proxy for source V6-VT. FIL uses the current master-table threshold, including any documentary discrepancy. MAT counts days >10 mm, not multi-day episodes. Calendar year is planting year; yield-year alignment remains pending.')
    fingerprint=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
    # Limit is a scheduling option: it must not invalidate completed partitions.
    scientific=dict(config=c,rules=rules,stages=STAGES,
                    calendar_sha256=hashlib.sha256((Path(c['calendar_dir'])/'maize-maize__rf.json').read_bytes()).hexdigest(),
                    code_sha256=hashlib.sha256(Path(__file__).read_bytes()+Path(core.__file__).read_bytes()).hexdigest())
    fingerprint=hashlib.sha256(json.dumps(scientific,sort_keys=True).encode()).hexdigest()
    (root/'plan_ejecucion.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    core.authenticate_gee()
    started=time.monotonic(); completed=0; measured=0; seconds=0.0
    print(f'Maíz: {len(pixels)} píxeles, seis fases, {c["start_year"]}-{c["end_year"]}. Ctrl+C permite retomar.',flush=True)
    try:
        for index,pixel in enumerate(pixels,1):
            tick=time.monotonic(); fresh=False
            for rule in rules:
                phase=rule['phase']; out=root/f'pixel_{pixel["pixel_id"]}'/phase
                marker=out/'COMPLETED.json'
                if marker.exists():
                    if json.loads(marker.read_text())['fingerprint']!=fingerprint:
                        raise ValueError(f'Cambió código/regla/calendario; usar otra carpeta: {out}')
                    continue
                fresh=True; out.mkdir(parents=True,exist_ok=True)
                run=c|{k:v for k,v in rule.items() if k!='original_rule'}
                run.pop('repository_results',None)
                core.save_csv(out/'pixels.csv',[pixel])
                core.save_csv(out/'windows_candidate.csv',windows(data,pixel,phase,c['start_year'],c['end_year']))
                print(f'Píxel {index}/{len(pixels)}: {pixel["pixel_id"]}, fase {phase}',flush=True)
                core.download(run,out)
                core.analyze(run,out)
                marker.write_text(json.dumps({'fingerprint':fingerprint,'status':'COMPLETED'}),encoding='utf-8')
            completed+=1
            if fresh:
                measured+=1; seconds+=time.monotonic()-tick
            remaining=(len(pixels)-index)*seconds/measured if measured else None
            progress=dict(status='RUNNING',pixels_completed=completed,pixels_selected=len(pixels),
                          elapsed_seconds=time.monotonic()-started,
                          estimated_remaining_seconds=remaining,measured_pixels=measured,
                          note='ETA based on completed pixels; cached pixels and quota changes affect speed.')
            (root/'progreso_paquete.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
            print(f'Completados {completed}/{len(pixels)} píxeles con seis fases. '
                  f'Restante estimado: {remaining/3600:.2f} horas.' if remaining is not None else
                  f'Completados {completed}/{len(pixels)} (reutilizados).',flush=True)
    except KeyboardInterrupt:
        (root/'estado_paquete.json').write_text(json.dumps({'status':'INTERRUPTED','pixels_completed':completed}),encoding='utf-8')
        print('Interrumpido: meses y fases terminados conservados. Repite el comando para retomar.',flush=True)
        return
    except Exception as exc:
        (root/'estado_paquete.json').write_text(json.dumps({'status':'FAILED','error':str(exc)}),encoding='utf-8')
        raise
    aggregate(root,root/'consolidado')
    (root/'estado_paquete.json').write_text(json.dumps({'status':'COMPLETED','pixels_completed':completed}),encoding='utf-8')
    if c.get('repository_results'):
        dest=Path(c['repository_results']);dest.mkdir(parents=True,exist_ok=True)
        shutil.copytree(root/'consolidado',dest/'consolidado',dirs_exist_ok=True)
        for name in ['plan_ejecucion.json','estado_paquete.json','progreso_paquete.json']:
            shutil.copy2(root/name,dest/name)
    print('Paquete completo. Resultados:',root/'consolidado',flush=True)


if __name__=='__main__': main()
