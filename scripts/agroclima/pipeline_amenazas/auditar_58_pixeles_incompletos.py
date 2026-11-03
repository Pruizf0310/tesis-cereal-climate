"""Read-only source audit of pixels rejected by the all-native-cells coverage rule."""
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import sqlite3
import h5py
import numpy as np

ROOT = Path('C:/Users/paola/Tesis')
BASE = ROOT/'03_Resultados/Agroclima/vigente'
OUTPUT = Path(__file__).resolve().parent.parent/'outputs/revision_58_pixeles_20261019'
MATRIX = OUTPUT.parent/'matriz_frecuencias_ONI_20261019_152551/matriz_frecuencias_ONI.sqlite'
RUNS = dict(EST='01118480a325e93d',VEG='0955242f426ffa57',REP='ba9e0e3286c7e384',
            FLO='4e3c0e35ac33f725',FIL='a445419ee76712f0',MAT='a7342fb2d9bf24a2')


def save_csv(path, rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    OUTPUT.mkdir(exist_ok=False)
    con=sqlite3.connect(MATRIX.resolve().as_uri()+'?mode=ro',uri=True)
    coords={p:(la,lo) for p,la,lo in con.execute('SELECT DISTINCT pixel_id,latitud,longitud FROM matriz WHERE par_frecuencia_oni_valido=0')}
    per_pixel={p:dict(pixel_id=p,latitud=coords[p][0],longitud=coords[p][1],ventanas=0,
        ventanas_con_celdas_utiles=0,ventanas_con_huecos_temporales=0,mask_estable=True,
        celdas_totales_min=99999,celdas_totales_max=0,celdas_utiles_min=99999,celdas_utiles_max=0,
        fraccion_area_util_min=1.,fraccion_area_util_max=0.,clima_temporadas_completas_sobre_soporte_fijo=0)
        for p in coords}
    signatures={p:set() for p in coords}; good_windows={p:set() for p in coords}
    details=[]; lookup={}
    for phase,run in RUNS.items():
        plan=json.loads((BASE/f'probabilidades/maize_{phase}_global_1981_2016'/run/'plan.json').read_text(encoding='utf-8'))
        cache=Path(plan['cache']); rule=plan['identity']['rule']; minimum=1 if phase=='MAT' else rule['min_days']
        for pid in coords:
            path=cache/f'{pid}.json.gz'
            expected=json.loads(path.with_suffix('.sha.json').read_text())['sha256']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==expected
            with gzip.open(path,'rt',encoding='utf-8') as f:data=json.load(f)
            assert set(data)==set(map(str,range(1981,2017)))
            for year, cells in data.items():
                assert cells
                n_days=len(cells[0]['valid']); full=[]; empty=[]; partial=[]; weighted=0.; area=0.; total_area=0.
                signature=[]
                for cell in cells:
                    valid=np.asarray(cell['valid']).ravel().astype(bool)
                    hits=np.asarray(cell['hits']).ravel().astype(bool)
                    assert len(valid)==n_days and len(hits)==n_days
                    key=(cell['x'],cell['y']);weight=math.cos(math.radians(cell['latitude']));total_area+=weight
                    state='complete' if valid.all() else 'empty' if not valid.any() else 'partial'
                    signature.append((key,state))
                    if state=='empty':empty.append(key);continue
                    if state=='partial':partial.append(key);continue
                    full.append(key);area+=weight
                    if phase=='MAT': count=int(hits.sum())
                    else:
                        edges=np.diff(np.r_[False,hits,False].astype(int))
                        starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
                        count=int(((ends-starts)>=minimum).sum())
                    weighted+=weight*count
                signatures[pid].add(tuple(sorted(signature)))
                s=per_pixel[pid];s['ventanas']+=1
                s['ventanas_con_celdas_utiles']+=bool(full)
                s['ventanas_con_huecos_temporales']+=bool(partial)
                s['celdas_totales_min']=min(s['celdas_totales_min'],len(cells));s['celdas_totales_max']=max(s['celdas_totales_max'],len(cells))
                s['celdas_utiles_min']=min(s['celdas_utiles_min'],len(full));s['celdas_utiles_max']=max(s['celdas_utiles_max'],len(full))
                s['fraccion_area_util_min']=min(s['fraccion_area_util_min'],area/total_area)
                s['fraccion_area_util_max']=max(s['fraccion_area_util_max'],area/total_area)
                if full and not partial:good_windows[pid].add((int(year),phase))
                row=dict(pixel_id=pid,temporada=int(year),fase=phase,dias_ventana=n_days,
                    celdas_totales=len(cells),celdas_completas=len(full),celdas_siempre_vacias_en_ventana=len(empty),
                    celdas_parcialmente_validas=len(partial),fraccion_area_util=area/total_area,
                    conteo_sobre_celdas_completas=weighted/area if area else None,
                    conteo_original=None,coincide_conteo_original=None)
                details.append(row);lookup[(pid,int(year),phase)]=row
        print(f'{phase}: caches de {len(coords)} pixeles verificados',flush=True)
    print('Contrastando con resumen anual original...',flush=True)
    with (BASE/'ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            pid=int(row['pixel_id'])
            if pid not in coords:continue
            key=(pid,int(row['season_year']),row['phase']);d=lookup[key]
            if row['mean_count_per_native_cell']:
                d['conteo_original']=float(row['mean_count_per_native_cell'])
                d['coincide_conteo_original']=math.isclose(d['conteo_sobre_celdas_completas'],d['conteo_original'],rel_tol=1e-8,abs_tol=1e-8)
    # Independently inspect yield years: these do not determine climate availability.
    yield_path=ROOT/'02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc'
    with h5py.File(yield_path,'r') as f:
        lat=np.asarray(f['lat']);lon=(np.asarray(f['lon'])+180)%360-180;var=f['var']
        assert var.shape[2]==36
        for pid,s in per_pixel.items():
            la,lo=coords[pid];ii=np.flatnonzero(np.isclose(lat,la,rtol=0,atol=1e-7));jj=np.flatnonzero(np.isclose(lon,lo,rtol=0,atol=1e-7))
            assert len(ii)==len(jj)==1
            values=var[int(ii[0]),int(jj[0]),:].astype(float)
            for attr in ['_FillValue','missing_value']:
                if attr in var.attrs:
                    for value in np.asarray(var.attrs[attr]).ravel():values[values==value]=np.nan
            s['rendimiento_anios_validos']=int(np.isfinite(values).sum())
            s['mask_estable']=len(signatures[pid])==1
            s['clima_temporadas_completas_sobre_soporte_fijo']=sum(all((year,phase) in good_windows[pid] for phase in RUNS) for year in range(1981,2017)) if s['mask_estable'] else 0
    save_csv(OUTPUT/'diagnostico_por_pixel.csv',list(per_pixel.values()))
    save_csv(OUTPUT/'diagnostico_por_temporada_fase.csv',details)
    summary=dict(pixeles=len(coords),ventanas=len(details),
        pixeles_mascara_espacial_fija=sum(s['mask_estable'] for s in per_pixel.values()),
        ventanas_con_huecos_temporales=sum(s['ventanas_con_huecos_temporales'] for s in per_pixel.values()),
        pixeles_36_temporadas_clima_sobre_soporte_fijo=sum(s['clima_temporadas_completas_sobre_soporte_fijo']==36 for s in per_pixel.values()),
        rendimiento_distribucion={str(n):sum(s['rendimiento_anios_validos']==n for s in per_pixel.values()) for n in sorted(set(s['rendimiento_anios_validos'] for s in per_pixel.values()))},
        conteos_originales_presentes=sum(d['conteo_original'] is not None for d in details),
        discrepancias_conteo=sum(d['coincide_conteo_original'] is False for d in details),
        fraccion_area_util_min=min(s['fraccion_area_util_min'] for s in per_pixel.values()),
        fraccion_area_util_max=max(s['fraccion_area_util_max'] for s in per_pixel.values()),
        matriz_modificada=False)
    (OUTPUT/'resumen.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
