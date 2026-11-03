"""Fixed-pixel standardized ONI contrasts for explicit regions; bootstrap shared seasons, never pixels."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
from contrastes_frecuencias_oni import PHASES,YEARS,season_weights,sha
from rutas_resultados_oni import resultados_oni


def measure_spec(phase,mode):
    if mode=='seasonal':
        label='dias_lluvia_por_temporada' if phase=='MAT' else 'episodios_por_temporada'
        return 'conteo_original',label,label
    return ('pct_dias_afectados','pct_dias_afectados','puntos_porcentuales') if phase=='MAT' else ('episodios_100d','episodios_100d','episodios_por_100_dias')


def region_contrast(values,categories,weights,state,min_years=5):
    """Average within-pixel contrasts on a fixed eligible support (equal pixel weights)."""
    ma=(categories==state)&np.isfinite(values);mb=(categories=='neutral')&np.isfinite(values)
    na=ma.sum(axis=1);nb=mb.sum(axis=1);support=(na>=min_years)&(nb>=min_years)
    n=int(support.sum());B=len(weights)
    report=dict(n_pixeles_region=len(values),n_pixeles_elegibles=n,n_pixeles_excluidos=len(values)-n,
        media_categoria=np.nan,media_neutral=np.nan,diferencia=np.nan,ic95_inferior=np.nan,ic95_superior=np.nan,
        replicas_estimables=0,estado_ic='sin_pixeles_con_cobertura_suficiente',
        n_temporadas_categoria_min=np.nan,n_temporadas_categoria_mediana=np.nan,n_temporadas_categoria_max=np.nan,
        n_temporadas_neutral_min=np.nan,n_temporadas_neutral_mediana=np.nan,n_temporadas_neutral_max=np.nan)
    if not n:return report,support
    a=np.where(ma,values,0).sum(axis=1)[support]/na[support]
    b=np.where(mb,values,0).sum(axis=1)[support]/nb[support]
    report.update(media_categoria=float(a.mean()),media_neutral=float(b.mean()),diferencia=float((a-b).mean()))
    for label,counts in [('categoria',na[support]),('neutral',nb[support])]:
        report[f'n_temporadas_{label}_min']=int(counts.min());report[f'n_temporadas_{label}_mediana']=float(np.median(counts));report[f'n_temporadas_{label}_max']=int(counts.max())
    v=values[support];ca=ma[support];cb=mb[support]
    sums=np.zeros(B);bad=np.zeros(B,bool)
    for start in range(0,n,128):
        end=min(start+128,n)
        da=weights@ca[start:end].T.astype(float);db=weights@cb[start:end].T.astype(float)
        aa=np.divide(weights@np.where(ca[start:end],v[start:end],0).T,da,out=np.full_like(da,np.nan),where=da>0)
        bb=np.divide(weights@np.where(cb[start:end],v[start:end],0).T,db,out=np.full_like(db,np.nan),where=db>0)
        delta=aa-bb;bad|=~np.isfinite(delta).all(axis=1);sums+=np.where(np.isfinite(delta),delta,0).sum(axis=1)
    sample=sums[~bad]/n;report['replicas_estimables']=len(sample)
    if len(sample)>=np.ceil(.95*B):
        report['ic95_inferior'],report['ic95_superior']=map(float,np.quantile(sample,[.025,.975]));report['estado_ic']='estimado'
    else:report['estado_ic']='replicas_insuficientes_en_soporte_fijo'
    return report,support


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--regions',type=Path,required=True,help='CSV explicito pixel_id,region, previamente revisado')
    p.add_argument('--matrix',type=Path)
    p.add_argument('--output',type=Path)
    p.add_argument('--bootstrap',type=int,default=2000)
    p.add_argument('--seed',type=int,default=20261019)
    p.add_argument('--min-years',type=int,default=5)
    p.add_argument('--measure-mode',choices=['normalized','seasonal'],default='normalized',help='normalized: por 100 dias / porcentaje; seasonal: conteos por temporada')
    p.add_argument('--regionalization-status',choices=['provisional','fixed'],default='provisional',help='No asumir que la propuesta geográfica ya esta fijada')
    args=p.parse_args();started=time.perf_counter()
    if args.bootstrap<200 or not 2<=args.min_years<=36:p.error('Revisar bootstrap y minimo de temporadas')
    matrix=args.matrix.resolve() if args.matrix else resultados_oni()/'matriz_frecuencias_ONI_corregida_20261019_165114/matriz_frecuencias_ONI.sqlite'
    if not (matrix.parent/'completed.json').is_file():p.error('Matriz no terminada')
    assignment=pd.read_csv(args.regions)
    if not {'pixel_id','region'}<=set(assignment):p.error('Se requieren pixel_id y region')
    if assignment.pixel_id.isna().any() or assignment.pixel_id.duplicated().any():p.error('Pixel nulo o duplicado; no se admiten regiones solapadas')
    assignment['pixel_id']=pd.to_numeric(assignment.pixel_id,errors='raise')
    if not (assignment.pixel_id%1==0).all():p.error('pixel_id debe ser entero')
    assignment.pixel_id=assignment.pixel_id.astype(int)
    assignment['region']=assignment.region.astype('string').str.strip();assignment.loc[assignment.region.eq(''),'region']=pd.NA
    c=sqlite3.connect(matrix.as_uri()+'?mode=ro',uri=True)
    known={r[0] for r in c.execute('SELECT DISTINCT pixel_id FROM matriz')}
    if not set(assignment.pixel_id)<=known:p.error('La asignacion contiene pixeles desconocidos')
    missing=assignment[assignment.region.isna()].copy();regions=assignment.dropna(subset=['region'])[['pixel_id','region']].copy()
    if regions.empty:p.error('No hay regiones asignadas')
    prefix='ONI_regional_conteos_temporada_' if args.measure_mode=='seasonal' else 'ONI_regional_'
    out=args.output.resolve() if args.output else resultados_oni()/(prefix+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=False)
    assignment.to_csv(out/'regiones_utilizadas.csv',index=False,encoding='utf-8-sig');missing.to_csv(out/'pixeles_sin_region_en_archivo.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame({'pixel_id':sorted(known-set(regions.pixel_id))}).to_csv(out/'pixeles_fuera_del_dominio_regional.csv',index=False)
    w=season_weights(args.bootstrap,args.seed)
    np.savez_compressed(out/'pesos_bootstrap_temporadas.npz',temporadas=YEARS,pesos=w.astype(np.uint8),semilla=args.seed)
    contrasts=[];series=[];trends=[];decades=[];supports=[]
    for phase in PHASES:
        measure,label,unit=measure_spec(phase,args.measure_mode)
        d=pd.read_sql_query('SELECT pixel_id,temporada,cat_oni,par_frecuencia_oni_valido,estado_cobertura_espacial,'+measure+' valor FROM matriz WHERE fase=?',c,params=(phase,))
        d=d.merge(regions,on='pixel_id',how='inner',validate='many_to_one');d.loc[d.par_frecuencia_oni_valido.ne(1),'valor']=np.nan
        if d.duplicated(['pixel_id','temporada']).any():raise ValueError('Claves duplicadas')
        for region,part in d.groupby('region',sort=True):
            v=part.pivot(index='pixel_id',columns='temporada',values='valor').reindex(columns=YEARS)
            cat=part.pivot(index='pixel_id',columns='temporada',values='cat_oni').reindex(index=v.index,columns=YEARS).to_numpy()
            values=v.to_numpy(float)
            for state in ['calido','frio']:
                row,support=region_contrast(values,cat,w,state,args.min_years)
                row.update(region=str(region),fase=phase,medida=label,columna_origen=measure,unidad=unit,modo_medida=args.measure_mode,contraste=state+'_menos_neutral',ponderacion='igual_por_pixel',
                    n_pixeles_soporte_parcial=int(part.loc[part.pixel_id.isin(v.index[support]) & part.estado_cobertura_espacial.eq('parcial_fija'),'pixel_id'].nunique()))
                contrasts.append(row)
                supports.extend(dict(region=str(region),fase=phase,contraste=state+'_menos_neutral',pixel_id=int(pid),elegible=bool(ok)) for pid,ok in zip(v.index,support))
            # Descriptive annual series: category composition may change by year.
            for year,g in part.groupby('temporada'):
                valid=g[g.valor.notna()]
                series.append(dict(region=str(region),fase=phase,medida=label,unidad=unit,temporada=int(year),cat_oni='TODAS',media_exposicion=float(valid.valor.mean()),n_pixeles=int(len(valid))))
                for state in ['frio','neutral','calido']:
                    a=valid[valid.cat_oni.eq(state)]
                    series.append(dict(region=str(region),fase=phase,medida=label,unidad=unit,temporada=int(year),cat_oni=state,media_exposicion=float(a.valor.mean()) if len(a) else np.nan,n_pixeles=int(len(a))))
            annual=np.nanmean(values,axis=0);good=np.isfinite(annual)
            slope=float(np.polyfit(YEARS[good]-YEARS.mean(),annual[good],1)[0]*10) if good.sum()>=3 else np.nan
            trends.append(dict(region=str(region),fase=phase,medida=label,unidad=unit,pendiente_por_decada=slope,n_temporadas=int(good.sum())))
            part=part[part.valor.notna()].copy();part['decada']=(part.temporada//10)*10
            counts=part.groupby(['decada','cat_oni']).size().rename('n_observaciones_pixel_temporada').reset_index()
            counts['proporcion']=counts.n_observaciones_pixel_temporada/counts.groupby('decada').n_observaciones_pixel_temporada.transform('sum')
            counts['region']=str(region);counts['fase']=phase;decades.append(counts)
        print(f'{phase}: {regions.region.nunique()} regiones procesadas',flush=True)
    tables=dict(contrastes_regionales=pd.DataFrame(contrasts),series_anuales_descriptivas=pd.DataFrame(series),D3_tendencias_regionales=pd.DataFrame(trends),D3_categorias_por_decada=pd.concat(decades,ignore_index=True),soporte_por_contraste=pd.DataFrame(supports))
    pending=out/'ONI_regional.pending.sqlite';dest=sqlite3.connect(pending)
    for name,df in tables.items():df.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig',na_rep='');df.to_sql(name,dest,index=False,chunksize=5000)
    result=tables['contrastes_regionales']
    if len(result)!=regions.region.nunique()*6*2:raise ValueError('Dimension de resultados inesperada')
    if not np.allclose(result.diferencia,result.media_categoria-result.media_neutral,equal_nan=True):raise ValueError('Contrastes inconsistentes')
    if (result.ic95_inferior>result.ic95_superior).any():raise ValueError('Intervalos invertidos')
    if dest.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    dest.commit();dest.close();pending.rename(out/'ONI_regional.sqlite');c.close()
    is_proposal=args.regionalization_status!='fixed'
    (out/'LEEME.txt').write_text('Estimacion principal: promedio con igual peso de los contrastes dentro de cada pixel, usando un soporte fijo de pixeles elegibles para cada region/fase/contraste.\nLa categoria ONI es local a cada ventana; no se impone una categoria unica a la region.\nBootstrap: mismos 36 anios con reemplazo para todos los pixeles y fases. No remuestrea pixeles ni dias.\nEn cada replica se exige que todos los pixeles del soporte fijo tengan categoria y neutral estimables; no se cambia la composicion de la region silenciosamente. IC solo con >=95% replicas estimables.\nMinimo 5 temporadas en ambos grupos por pixel. Se publican n_pixeles y min/mediana/max de temporadas; los grupos de pixeles no son anios independientes.\nLas series anuales por categoria son descriptivas y cambian de composicion; no son el estimador principal.\nLos contrastes calido y frio pueden tener soportes elegibles diferentes: consultar soporte_por_contraste.\nPonderacion por pixel, no area cultivada; soporte espacial parcial fijo se conserva y se cuenta.\nIC exploratorios sin ajuste por autocorrelacion ENSO o multiplicidad. Regiones amplias no equivalen a regiones agroclimaticas.\nSi se usa la propuesta geográfica sin cerrar su revision, los resultados siguen siendo provisionales.\n',encoding='utf-8')
    with (out/'LEEME.txt').open('a',encoding='utf-8') as guide:
        guide.write('Modo de medida: '+args.measure_mode+'\n')
        if args.measure_mode=='seasonal':guide.write('Calor: episodios medios espaciales por temporada y fase. MAT: dias medios espaciales con lluvia >10 mm por temporada y fase. No se divide por duracion. Puede haber decimales; no redondear a episodios enteros. Las ventanas tienen duraciones distintas: no interpretar conteos como tasas comparables entre fases o lugares. La comparacion ONI se hace dentro del mismo pixel y fase antes de promediar. Los resultados normalizados anteriores se conservan.\n')
    report=dict(regiones=int(regions.region.nunique()),pixeles_asignados=int(len(regions)),pixeles_fuera_del_dominio=len(known-set(regions.pixel_id)),
        filas_contrastes=len(result),ic_estimados=int(result.estado_ic.eq('estimado').sum()),bootstrap=args.bootstrap,semilla=args.seed,min_temporadas=args.min_years,
        regionalizacion_provisional=is_proposal,modo_medida=args.measure_mode,unidades_por_fase={phase:measure_spec(phase,args.measure_mode)[2] for phase in PHASES},estimador='Media de contrastes dentro de pixel; soporte elegible fijo; igual peso por pixel',
        fuentes_sha256={str(matrix):sha(matrix),str(args.regions.resolve()):sha(args.regions),str(Path(__file__).resolve()):sha(Path(__file__))},segundos=round(time.perf_counter()-started,2))
    (out/'completed.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['regiones','pixeles_asignados','filas_contrastes','ic_estimados','regionalizacion_provisional']},ensure_ascii=False,indent=2),flush=True)
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
