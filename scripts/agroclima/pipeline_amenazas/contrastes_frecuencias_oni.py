"""Annual frequency means and ONI contrasts, with shared season bootstrap and trend diagnostics."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import warnings
import numpy as np
import pandas as pd
from rutas_resultados_oni import resultados_oni

PHASES=['EST','VEG','REP','FLO','FIL','MAT']
STATES=['frio','neutral','calido']
YEARS=np.arange(1981,2017)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()


def season_weights(replicates,seed):
    rng=np.random.default_rng(seed)
    draws=rng.integers(0,len(YEARS),size=(replicates,len(YEARS)))
    weights=np.zeros((replicates,len(YEARS)),dtype=float)
    for b in range(replicates):weights[b]=np.bincount(draws[b],minlength=len(YEARS))
    return weights


def interval(samples,eligible,min_fraction=.95):
    valid=np.isfinite(samples).sum(axis=0)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore',RuntimeWarning)
        low,high=np.nanquantile(samples,[.025,.975],axis=0)
    usable=eligible & (valid>=np.ceil(samples.shape[0]*min_fraction))
    return np.where(usable,low,np.nan),np.where(usable,high,np.nan),valid,usable


def summarize_block(values,categories,weights,min_years):
    """values/categories: pixel x 36. Resample the same years for all pixels."""
    groups={}
    for state in STATES:
        mask=(categories==state)&np.isfinite(values)
        counts=mask.sum(axis=1)
        mean=np.divide(np.where(mask,values,0).sum(axis=1),counts,
                       out=np.full(len(values),np.nan),where=counts>0)
        denominators=weights@mask.T.astype(float)
        numerators=weights@np.where(mask,values,0).T
        boot=np.divide(numerators,denominators,out=np.full_like(numerators,np.nan),where=denominators>0)
        low,high,n_boot,usable=interval(boot,counts>=min_years)
        groups[state]=dict(n=counts,mean=mean,boot=boot,low=low,high=high,n_boot=n_boot,usable=usable)
    contrasts={}
    for state in ['calido','frio']:
        a=groups[state];b=groups['neutral'];samples=a['boot']-b['boot']
        eligible=(a['n']>=min_years)&(b['n']>=min_years)
        low,high,n_boot,usable=interval(samples,eligible)
        contrasts[state]=dict(delta=a['mean']-b['mean'],low=low,high=high,n_boot=n_boot,usable=usable)
    return groups,contrasts


def slope(values):
    """OLS slope per decade, independently per pixel, ignoring missing years."""
    good=np.isfinite(values);n=good.sum(axis=1)
    t=YEARS-YEARS.mean();tx=np.where(good,t,0)
    mx=np.divide(tx.sum(axis=1),n,out=np.zeros(len(values)),where=n>0)
    my=np.divide(np.where(good,values,0).sum(axis=1),n,out=np.zeros(len(values)),where=n>0)
    centered=np.where(good,t-mx[:,None],0)
    num=(centered*np.where(good,values-my[:,None],0)).sum(axis=1)
    den=(centered**2).sum(axis=1)
    return np.divide(10*num,den,out=np.full(len(values),np.nan),where=(n>=3)&(den>0))


def write_table(frame,name,con,out):
    frame.to_csv(out/(name+'.csv'),index=False,encoding='utf-8-sig',na_rep='')
    frame.to_sql(name,con,index=False,if_exists='replace',chunksize=5000)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True,help='Carpeta de matriz corregida terminada')
    parser.add_argument('--output',type=Path,help='Carpeta nueva de salida')
    parser.add_argument('--bootstrap',type=int,default=2000)
    parser.add_argument('--seed',type=int,default=20261019)
    parser.add_argument('--min-years',type=int,default=5,help='Piso para intervalos por categoria, no suficiencia inferencial')
    parser.add_argument('--batch-size',type=int,default=128)
    parser.add_argument('--regions',type=Path,help='CSV opcional de regiones previamente definidas: pixel_id,region; una asignacion por pixel')
    args=parser.parse_args();started=time.perf_counter()
    if args.bootstrap<200 or not 2<=args.min_years<=36 or args.batch_size<1:parser.error('Revisar bootstrap >=200, min-years 2..36 y batch-size >=1')
    source=args.input.resolve();db=source/'matriz_frecuencias_ONI.sqlite'
    if not db.is_file() or not (source/'completed.json').is_file():parser.error('No es una matriz terminada')
    manifest=json.loads((source/'completed.json').read_text(encoding='utf-8'))
    if manifest.get('version')!='cobertura_espacial_fija_v2':parser.error('Usar la matriz corregida v2')
    out=args.output.resolve() if args.output else resultados_oni()/('contrastes_frecuencias_ONI_'+time.strftime('%Y%m%d_%H%M%S'))
    if out.exists():parser.error('La salida ya existe; indica otra carpeta')
    c=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    coords=pd.read_sql_query('SELECT DISTINCT pixel_id,latitud,longitud,estado_cobertura_espacial,fraccion_area_climatica_util FROM matriz ORDER BY pixel_id',c)
    if len(coords)!=10923 or coords.pixel_id.duplicated().any():raise ValueError('Coordenadas o soporte espacial no unicos por pixel')
    regions=None
    if args.regions:
        regions=pd.read_csv(args.regions,usecols=['pixel_id','region'])
        if regions.pixel_id.duplicated().any() or regions.region.isna().any() or not regions.pixel_id.isin(coords.pixel_id).all():raise ValueError('Regiones ambiguas o pixeles desconocidos')
        regions['region']=regions.region.astype(str)
        if regions.region.eq('CONJUNTO').any():raise ValueError('CONJUNTO es un nombre reservado')
    out.mkdir(parents=True,exist_ok=False)
    pending=out/'contrastes_ONI.pending.sqlite';con=sqlite3.connect(pending)
    weights=season_weights(args.bootstrap,args.seed)
    # Keep the exact same resampling weights across every phase/pixel/category.
    np.savez_compressed(out/'pesos_bootstrap_temporadas.npz',temporadas=YEARS,pesos=weights.astype(np.uint8),semilla=args.seed)
    summaries=[];contrasts=[];trends=[];annual_d3=[];decades_d3=[];trend_d3=[]
    for phase in PHASES:
        measure='pct_dias_afectados' if phase=='MAT' else 'episodios_100d'
        unit='puntos_porcentuales' if phase=='MAT' else 'episodios_por_100_dias'
        d=pd.read_sql_query('SELECT pixel_id,temporada,cat_oni,par_frecuencia_oni_valido,conteo_original,'+measure+' AS valor FROM matriz WHERE fase=?',c,params=(phase,))
        if len(d)!=10923*36 or d.duplicated(['pixel_id','temporada']).any():raise ValueError('Claves anuales incorrectas')
        d.loc[d.par_frecuencia_oni_valido.ne(1),'valor']=np.nan
        if not d.loc[d.valor.notna(),'cat_oni'].isin(STATES).all():raise ValueError('Categoria ONI desconocida')
        values=d.pivot(index='pixel_id',columns='temporada',values='valor').reindex(index=coords.pixel_id,columns=YEARS).to_numpy(float)
        categories=d.pivot(index='pixel_id',columns='temporada',values='cat_oni').reindex(index=coords.pixel_id,columns=YEARS).to_numpy()
        original_counts=d.pivot(index='pixel_id',columns='temporada',values='conteo_original').reindex(index=coords.pixel_id,columns=YEARS).to_numpy(float)
        for first in range(0,len(coords),args.batch_size):
            last=min(first+args.batch_size,len(coords));info=coords.iloc[first:last].reset_index(drop=True)
            v=values[first:last];cats=categories[first:last]
            groups,deltas=summarize_block(v,cats,weights,args.min_years)
            for state,g in groups.items():
                t=info.copy();t['fase']=phase;t['medida']=measure;t['unidad']=unit;t['cat_oni']=state
                t['n_temporadas']=g['n'];t['media']=g['mean']
                mask=(cats==state)&np.isfinite(v)&np.isfinite(original_counts[first:last])
                n=mask.sum(axis=1)
                t['media_conteo_original']=np.divide(np.where(mask,original_counts[first:last],0).sum(axis=1),n,out=np.full(len(v),np.nan),where=n>0)
                t['ic95_inferior']=g['low'];t['ic95_superior']=g['high'];t['replicas_estimables']=g['n_boot']
                t['estado_ic']=np.where(g['n']<args.min_years,'menos_del_minimo_temporadas',np.where(g['usable'],'estimado','replicas_insuficientes'))
                summaries.append(t)
            for state,g in deltas.items():
                a=groups[state];b=groups['neutral'];t=info.copy();t['fase']=phase;t['medida']=measure;t['unidad']=unit
                t['contraste']=state+'_menos_neutral';t['n_categoria']=a['n'];t['n_neutral']=b['n']
                t['media_categoria']=a['mean'];t['media_neutral']=b['mean'];t['diferencia']=g['delta']
                t['ic95_inferior']=g['low'];t['ic95_superior']=g['high'];t['replicas_estimables']=g['n_boot']
                t['estado_ic']=np.where((a['n']<args.min_years)|(b['n']<args.min_years),'menos_del_minimo_temporadas',np.where(g['usable'],'estimado','replicas_insuficientes'))
                contrasts.append(t)
            if first==0 or last==len(coords) or last%2048<args.batch_size:
                print(f'{phase}: {last:,}/{len(coords):,} pixeles; bootstrap {args.bootstrap}',flush=True)
        t=coords.copy();t['fase']=phase;t['medida']=measure;t['unidad']=unit;t['n_temporadas']=np.isfinite(values).sum(axis=1)
        t['pendiente_por_decada']=slope(values);t['media_1981_2016']=np.nanmean(values,axis=1);trends.append(t)
        # D3 descriptive global/regional diagnostics, without inventing regions.
        domains=[('CONJUNTO',d)]
        if regions is not None:
            joined=d.merge(regions,on='pixel_id',how='inner',validate='many_to_one')
            domains.extend((str(name),part) for name,part in joined.groupby('region'))
        for name,part in domains:
            valid=part[part.valor.notna() & part.cat_oni.isin(STATES)].copy()
            a=valid.groupby('temporada').agg(media_exposicion=('valor','mean'),n_pixeles=('pixel_id','nunique')).reset_index()
            a['dominio']=name;a['fase']=phase;a['medida']=measure;annual_d3.append(a)
            arr=np.full((1,36),np.nan)
            for row in a.itertuples():arr[0,int(row.temporada)-1981]=row.media_exposicion
            trend_d3.append(dict(dominio=name,fase=phase,medida=measure,pendiente_por_decada=float(slope(arr)[0]),n_temporadas=int(np.isfinite(arr).sum())))
            valid['decada']=(valid.temporada//10)*10
            b=valid.groupby(['decada','cat_oni']).size().rename('n_observaciones_pixel_temporada').reset_index()
            b['proporcion_en_decada']=b.n_observaciones_pixel_temporada/b.groupby('decada').n_observaciones_pixel_temporada.transform('sum')
            b['dominio']=name;b['fase']=phase;decades_d3.append(b)
    summary=pd.concat(summaries,ignore_index=True);delta=pd.concat(contrasts,ignore_index=True)
    if len(summary)!=10923*6*3 or len(delta)!=10923*6*2:raise ValueError('Dimension de resultados inesperada')
    if summary.duplicated(['pixel_id','fase','cat_oni']).any() or delta.duplicated(['pixel_id','fase','contraste']).any():raise ValueError('Resultados duplicados')
    if not np.allclose(summary.groupby(['pixel_id','fase']).n_temporadas.sum(),36):raise ValueError('Categorias no suman las 36 temporadas validas')
    if not np.allclose(delta.diferencia,delta.media_categoria-delta.media_neutral,equal_nan=True):raise ValueError('Diferencia incorrecta')
    if (delta.loc[delta.estado_ic.ne('estimado'),['ic95_inferior','ic95_superior']].notna().any().any()):raise ValueError('IC publicado sin suficiencia')
    for frame in [summary,delta]:
        if (frame.ic95_inferior>frame.ic95_superior).any():raise ValueError('Intervalo invertido')
    write_table(summary,'medias_por_categoria',con,out)
    write_table(delta,'contrastes_ONI',con,out)
    write_table(pd.concat(trends,ignore_index=True),'D3_tendencias_por_pixel',con,out)
    write_table(pd.concat(annual_d3,ignore_index=True),'D3_series_anuales_por_dominio',con,out)
    write_table(pd.DataFrame(trend_d3),'D3_tendencias_por_dominio',con,out)
    write_table(pd.concat(decades_d3,ignore_index=True),'D3_categorias_por_decada',con,out)
    con.execute('CREATE UNIQUE INDEX clave_medias ON medias_por_categoria(pixel_id,fase,cat_oni)')
    con.execute('CREATE UNIQUE INDEX clave_contrastes ON contrastes_ONI(pixel_id,fase,contraste)')
    if con.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite no integro')
    # Re-read exported tables and verify numerical values and missingness.
    for name,frame in [('medias_por_categoria',summary),('contrastes_ONI',delta)]:
        read=pd.read_csv(out/(name+'.csv'))
        if len(read)!=len(frame):raise ValueError('Exportacion CSV incompleta')
        for col in frame.select_dtypes(include='number').columns:
            if not np.allclose(read[col],frame[col],equal_nan=True,rtol=1e-10,atol=1e-12):raise ValueError(f'CSV distinto: {name}/{col}')
    con.commit();con.close();c.close();pending.rename(out/'contrastes_ONI.sqlite')
    record=dict(entrada=str(source),filas_medias=len(summary),filas_contrastes=len(delta),
        bootstrap_replicas=args.bootstrap,semilla=args.seed,min_temporadas_categoria=args.min_years,
        bootstrap='36 temporadas completas con reemplazo; mismos pesos para todos los pixeles/fases; categorias reevaluadas por sus etiquetas de ventana',
        intervalo='percentiles 2.5/97.5, minimo 95% de replicas estimables',
        ic_estimados=int(delta.estado_ic.eq('estimado').sum()),ic_no_estimados=int(delta.estado_ic.ne('estimado').sum()),
        regiones_aportadas=args.regions is not None,D3_regional_pendiente=args.regions is None,
        fuentes_sha256={str(db):sha(db),str(source/'completed.json'):sha(source/'completed.json'),str(Path(__file__).resolve()):sha(Path(__file__))},
        segundos=round(time.perf_counter()-started,2))
    if args.regions:record['fuentes_sha256'][str(args.regions.resolve())]=sha(args.regions)
    (out/'LEEME.txt').write_text(
        'ONI -> frecuencias: resumen descriptivo e intervalos exploratorios por pixel. No causalidad.\n'
        'Calor: episodios/100 dias. MAT: porcentaje de dias de lluvia afectados; contraste en puntos porcentuales.\n'
        'Cada categoria muestra n_temporadas. Medias con n>0 se conservan; IC requiere el minimo fijado y replicas suficientes.\n'
        'Bootstrap de temporadas: mismos anios sorteados para todos los pixeles/fases. No se remuestrean pixeles ni dias.\n'
        'IC por pixel sin FDR: no son inferencia regional ni evidencia independiente entre pixeles.\n'
        'No ajusta dependencia temporal entre temporadas de un mismo evento ENSO.\n'
        'Cobertura espacial parcial fija permanece identificada; area disponible no equivale a superficie de maiz.\n'
        'D3: pendientes por decada y reparto ONI por decada. CONJUNTO promedia pixeles con igual peso.\n'
        '1980 incluye 1981-1989; 2010 incluye 2010-2016: las decadas de borde son parciales.\n'
        'Los conteos decenales son observaciones pixel-temporada, no anios ENSO independientes.\n'
        'Sin CSV de regiones, D3 regional sigue pendiente. No se elige automaticamente si una tendencia es despreciable.\n'
        'No se calcula aun sensibilidad detrendida; revisar D3 antes de decidirla. No se generan mapas ni rendimiento.\n'
        'Los intervalos de distribuciones de remuestreo no son prediccion ni prueban causalidad.\n'
        'No usar ejecuciones sin completed.json. La matriz original se abre en solo lectura.\n',encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:record[k] for k in ['filas_medias','filas_contrastes','ic_estimados','ic_no_estimados','D3_regional_pendiente']},ensure_ascii=False,indent=2),flush=True)
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
