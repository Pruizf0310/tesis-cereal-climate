"""Read a fixed sample of completed GEE batches without modifying the running job."""
import argparse
import hashlib
import itertools
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main():
    import pandas as pd
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lotes',type=int,default=200)
    parser.add_argument('--tesis',default=r'C:\Users\paola\Tesis')
    parser.add_argument('--refresh',action='store_true',help='Seleccionar una muestra nueva de los lotes disponibles')
    args=parser.parse_args()
    if args.lotes<1:parser.error('--lotes debe ser positivo')
    thesis=Path(args.tesis)
    source=thesis/'03_Resultados/Agroclima/vigente/ejecuciones/maize_seis_fases_GEE_1981_2016'
    out=source.parent/'muestra_frecuencias_maize';out.mkdir(exist_ok=True)
    frames=[];files={};skipped=[]
    # Freeze the marker names now; no scan of every scientific data file.
    prior=out/'provenance_muestra.json'
    if prior.exists() and not args.refresh:
        frozen=json.loads(prior.read_text(encoding='utf-8'))['files']
        markers=[source/'lotes'/Path(name).with_suffix('.json') for name in list(frozen)[:args.lotes]]
    else:
        markers=list(itertools.islice((source/'lotes').glob('batch_*.json'),args.lotes))
    for marker in markers:
        try:
            meta=json.loads(marker.read_text())
            path=marker.with_suffix('.csv')
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if digest!=meta['sha256']:raise ValueError('Hash incorrecto')
            frame=pd.read_csv(path)
            if len(frame)!=meta['rows']:raise ValueError('Cantidad de filas incorrecta')
            frame['source_batch']=path.name
            frames.append(frame);files[path.name]=digest
        except (OSError,ValueError,KeyError) as exc:
            skipped.append(dict(file=marker.name,error=str(exc)))
    if not frames:raise ValueError('No hay lotes terminados válidos')
    data=pd.concat(frames,ignore_index=True)
    if data.duplicated(['pixel_id','season_year','phase']).any():
        raise ValueError('Muestra con observaciones duplicadas')
    coords=pd.read_csv(thesis/'02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv')
    data=data.merge(coords[['pixel_id','latitude','longitude']],on='pixel_id',how='left',validate='many_to_one')
    if data.latitude.isna().any():raise ValueError('Coordenadas no identificadas')
    ok=data[(data.quality=='OK') & data.mean_count_per_native_cell.notna()].copy()
    if ok.empty:raise ValueError('No hay ventanas con cobertura completa')
    phases=['EST','VEG','REP','FLO','FIL','MAT']
    names=['Establecimiento','Vegetativo tardío','Desarrollo reproductivo','Floración','Llenado','Maduración / secado']
    summary=[];examples=[]
    for phase in phases:
        sub=ok[ok.phase==phase]
        if sub.empty:continue
        positive=sub[sub.mean_count_per_native_cell>0]
        summary.append(dict(phase=phase,unit='días' if phase=='MAT' else 'eventos',
            pixel_years=len(sub),pixels=sub.pixel_id.nunique(),with_events=len(positive),
            without_events=len(sub)-len(positive),percent_with_events=100*len(positive)/len(sub),
            mean_count=float(sub.mean_count_per_native_cell.mean()),
            max_count=float(sub.mean_count_per_native_cell.max()),
            mean_exposed_area_fraction=float(sub.evaluated_area_fraction_with_event.mean()),
            threshold=float(sub.threshold.iloc[0]),operator=sub.operator.iloc[0],
            min_days=int(sub.min_days.iloc[0])))
        examples.append(positive.nlargest(3,'mean_count_per_native_cell'))
    summary=pd.DataFrame(summary).set_index('phase').reindex(phases).reset_index()
    summary.to_csv(out/'resumen_frecuencias_muestra.csv',index=False,encoding='utf-8-sig')
    data.to_csv(out/'datos_muestra.csv',index=False,encoding='utf-8-sig')
    pd.concat(examples,ignore_index=True).to_csv(out/'ejemplos_con_amenaza.csv',index=False,encoding='utf-8-sig')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(3,2,figsize=(12,11))
    for ax,phase,name in zip(axes.flat,phases,names):
        r=summary[summary.phase==phase].iloc[0]
        ax.bar(['Sin excedencias','Con excedencias'],[r.without_events,r.with_events],
               color=['#cbd5e1','#d97706'],width=.6)
        ax.set_title(f'{phase} · {name}',loc='left',fontweight='bold',pad=12)
        ax.set_ylabel('Observaciones píxel–año')
        ax.set_ylim(0,max(r.without_events,r.with_events,1)*1.65)
        for x,value in enumerate([r.without_events,r.with_events]):
            ax.text(x,value+max(r.pixel_years*.015,1),f'{int(value):,}',ha='center',fontweight='bold')
        rule=f"P diaria >{r.threshold:g} mm" if phase=='MAT' else f"Tmax diaria ≥{r.threshold:g} °C · ≥{r.min_days} días seguidos"
        ax.text(.98,.96,f'{rule}\n{r.percent_with_events:.1f}% con excedencias\n'
                f'Media: {r.mean_count:.2f} {r.unit}/celda\nMáximo: {r.max_count:.2f} {r.unit}/celda',
                transform=ax.transAxes,ha='right',va='top',fontsize=9,
                bbox=dict(facecolor='white',edgecolor='none',alpha=.9))
        ax.yaxis.grid(True,alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('Maíz · ¿Aparecen las amenazas en los resultados calculados?',fontsize=17,fontweight='bold',y=.99)
    fig.text(.5,.955,f'Muestra de {len(files)} lotes terminados · {data.pixel_id.nunique()} píxeles · '
             f'{int(data.season_year.min())}–{int(data.season_year.max())} · {len(ok):,} ventanas completas',ha='center',fontsize=11)
    fig.text(.06,.018,'Con excedencias = al menos una celda ERA5-Land con evento dentro de la fase.\n'
             'Conteos medios entre celdas del píxel GDHY; MAT cuenta días. Muestra parcial, no representa todo el maíz ni demuestra daño al rendimiento.',fontsize=9,color='#475569')
    fig.tight_layout(rect=[0,.06,1,.93]);fig.savefig(out/'presencia_amenazas_seis_fases.png',dpi=170);plt.close(fig)
    fig,axes=plt.subplots(3,2,figsize=(12,10))
    for ax,phase,name in zip(axes.flat,phases,names):
        sub=ok[(ok.phase==phase)&(ok.mean_count_per_native_cell>0)]
        ax.set_title(f'{phase} · {name}',loc='left',fontweight='bold')
        if len(sub):
            ax.hist(sub.mean_count_per_native_cell,bins=min(14,max(3,int(np.sqrt(len(sub))))),color='#0f766e',edgecolor='white')
        else:ax.text(.5,.5,'Sin casos positivos en esta muestra',ha='center',transform=ax.transAxes)
        ax.set_xlabel('Días medios por celda y temporada' if phase=='MAT' else 'Eventos medios por celda y temporada')
        ax.set_ylabel('Observaciones píxel–año')
        ax.yaxis.grid(True,alpha=.15);ax.set_axisbelow(True)
    fig.suptitle('Frecuencias de amenazas · distribución de los casos positivos',fontsize=16,fontweight='bold',y=.99)
    fig.text(.05,.014,'Solo casos con conteo >0; los ceros están incluidos en el gráfico de presencia. Valores fraccionarios porque se promedian celdas climáticas.',fontsize=9,color='#475569')
    fig.tight_layout(rect=[0,.04,1,.96]);fig.savefig(out/'distribucion_frecuencias_positivas.png',dpi=170);plt.close(fig)
    manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),completed_batches_sampled=len(files),
                  source=str(source),files=files,skipped=skipped,rows=len(data),complete_rows=len(ok),
                  pixels=int(data.pixel_id.nunique()),years=[int(data.season_year.min()),int(data.season_year.max())],
                  coverage_quality=data.quality.value_counts().to_dict(),
                  selection='First completed marker filenames returned by filesystem; arbitrary partial sample, not representative. All six phases retained; positive rows not preferentially selected.',
                  interpretation='Threshold exceedance under adopted rules and estimated calendar, not demonstrated yield damage. Mean native-cell counts; MAT days, other phases episodes.')
    (out/'provenance_muestra.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    repo=thesis/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/ejecuciones/muestra_frecuencias_maize'
    if repo.parent.exists():
        repo.mkdir(exist_ok=True)
        for file in out.iterdir():
            if file.is_file():shutil.copy2(file,repo/file.name)
    print(summary.to_string(index=False))
    print('Gráficos guardados en',out)


if __name__=='__main__':main()
