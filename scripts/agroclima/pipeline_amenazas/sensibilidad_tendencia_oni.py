"""Sensitivity of annual ONI contrasts to a linear exposure trend, refitted in each bootstrap."""
import argparse
import json
from pathlib import Path
import sqlite3
import time
import numpy as np
import pandas as pd
from contrastes_frecuencias_oni import PHASES, YEARS, interval, sha
from rutas_resultados_oni import resultados_oni


def residual_contrasts(values,categories,weights,min_years=5):
    if not np.isfinite(values).all():raise ValueError('Esta version exige las 36 temporadas climaticas completas')
    t=(YEARS-YEARS.mean()).astype(float);n=len(t)
    slope=(values@t)/(t@t)
    wt=weights@t;wy=weights@values.T;wty=weights@(values*t).T
    denominator=weights@(t*t)-wt*wt/n
    bs=np.divide(wty-wt[:,None]*wy/n,denominator[:,None],out=np.full_like(wy,np.nan),where=denominator[:,None]>0)
    groups={}
    for state in ['frio','neutral','calido']:
        mask=categories==state;count=mask.sum(axis=1)
        mean=np.divide(np.where(mask,values,0).sum(axis=1),count,out=np.full(len(values),np.nan),where=count>0)
        mt=np.divide((mask*t).sum(axis=1),count,out=np.full(len(values),np.nan),where=count>0)
        count_b=weights@mask.T.astype(float)
        mean_b=np.divide(weights@np.where(mask,values,0).T,count_b,out=np.full_like(count_b,np.nan),where=count_b>0)
        time_b=np.divide(weights@(mask*t).T,count_b,out=np.full_like(count_b,np.nan),where=count_b>0)
        groups[state]=dict(n=count,mean=mean,time=mt,mean_b=mean_b,time_b=time_b)
    result={}
    for state in ['calido','frio']:
        a=groups[state];b=groups['neutral']
        raw=a['mean']-b['mean'];delta=raw-slope*(a['time']-b['time'])
        boot=a['mean_b']-b['mean_b']-bs*(a['time_b']-b['time_b'])
        low,high,n_boot,usable=interval(boot,(a['n']>=min_years)&(b['n']>=min_years))
        result[state]=dict(raw=raw,delta=delta,low=low,high=high,n_boot=n_boot,usable=usable,slope=slope)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True,help='Carpeta de contrastes originales terminados')
    p.add_argument('--output',type=Path)
    args=p.parse_args();source=args.input.resolve();meta=json.loads((source/'completed.json').read_text(encoding='utf-8'))
    matrix=Path(meta['entrada'])/'matriz_frecuencias_ONI.sqlite'
    expected=meta['fuentes_sha256'].get(str(matrix))
    if expected is None or sha(matrix)!=expected:raise ValueError('La matriz no coincide con los contrastes originales')
    out=args.output.resolve() if args.output else resultados_oni()/('sensibilidad_ONI_'+time.strftime('%Y%m%d_%H%M%S'))
    if out.exists():p.error('La salida ya existe')
    out.mkdir(parents=True);started=time.perf_counter()
    with np.load(source/'pesos_bootstrap_temporadas.npz') as z:
        if not np.array_equal(z['temporadas'],YEARS):raise ValueError('Temporadas distintas')
        w=z['pesos'].astype(float)
    if w.shape!=(meta['bootstrap_replicas'],36) or not (w.sum(axis=1)==36).all():raise ValueError('Pesos no validos')
    c=sqlite3.connect(matrix.as_uri()+'?mode=ro',uri=True)
    raw=pd.read_csv(source/'contrastes_ONI.csv')
    pieces=[]
    for phase in PHASES:
        measure='pct_dias_afectados' if phase=='MAT' else 'episodios_100d'
        d=pd.read_sql_query('SELECT pixel_id,temporada,cat_oni,'+measure+' valor FROM matriz WHERE fase=? AND par_frecuencia_oni_valido=1',c,params=(phase,))
        v=d.pivot(index='pixel_id',columns='temporada',values='valor').reindex(columns=YEARS)
        cats=d.pivot(index='pixel_id',columns='temporada',values='cat_oni').reindex(index=v.index,columns=YEARS).to_numpy()
        if v.shape!=(10923,36):raise ValueError('Matriz de fase incompleta')
        for start in range(0,len(v),128):
            end=min(start+128,len(v));r=residual_contrasts(v.iloc[start:end].to_numpy(float),cats[start:end],w,meta['min_temporadas_categoria'])
            for state,g in r.items():
                pieces.append(pd.DataFrame(dict(pixel_id=v.index[start:end],fase=phase,contraste=state+'_menos_neutral',
                    diferencia_recalculada=g['raw'],diferencia_sin_tendencia=g['delta'],
                    ic95_sin_tendencia_inferior=g['low'],ic95_sin_tendencia_superior=g['high'],
                    replicas_sin_tendencia_estimables=g['n_boot'],ic_sin_tendencia_estimado=g['usable'],pendiente_anual=g['slope'])))
        print(f'{phase}: sensibilidad completa; tendencia reajustada en cada replica bootstrap',flush=True)
    compare=raw.merge(pd.concat(pieces,ignore_index=True),on=['pixel_id','fase','contraste'],validate='one_to_one')
    if len(compare)!=131076 or not np.allclose(compare.diferencia,compare.diferencia_recalculada,equal_nan=True,atol=1e-10):raise ValueError('No se reproducen contrastes originales')
    compare['cambio_por_detrendido']=compare.diferencia_sin_tendencia-compare.diferencia
    compare['cambia_signo']=(compare.diferencia*compare.diferencia_sin_tendencia < -1e-12)
    compare.drop(columns='diferencia_recalculada',inplace=True)
    compare.to_csv(out/'comparacion_sensibilidad.csv',index=False,encoding='utf-8-sig',na_rep='')
    reports=[]
    for (phase,contrast),g in compare.groupby(['fase','contraste']):
        reports.append(dict(fase=phase,contraste=contrast,n_pixeles=len(g),
            mediana_cambio_absoluto=float(g.cambio_por_detrendido.abs().median()),
            p95_cambio_absoluto=float(g.cambio_por_detrendido.abs().quantile(.95)),
            cambios_signo=int(g.cambia_signo.sum()),
            mediana_diferencia_original=float(g.diferencia.median()),
            mediana_diferencia_sin_tendencia=float(g.diferencia_sin_tendencia.median())))
    pd.DataFrame(reports).to_csv(out/'resumen_sensibilidad.csv',index=False,encoding='utf-8-sig')
    c.close()
    (out/'completed.json').write_text(json.dumps(dict(entrada=str(source),matriz=str(matrix),filas=len(compare),
        metodo='Residuos de tendencia lineal por pixel/fase; pendiente e intercepto reajustados en cada replica con los mismos pesos bootstrap originales',
        original_se_conserva=True,bootstrap_replicas=len(w),semilla=meta['semilla'],
        limites='Sensibilidad descriptiva por pixel; no causal, sin FDR. D3 regional sigue pendiente. Cambios de signo incluyen valores cercanos a cero; no son evidencia independiente.',
        fuentes_sha256={str(source/'contrastes_ONI.csv'):sha(source/'contrastes_ONI.csv'),str(source/'pesos_bootstrap_temporadas.npz'):sha(source/'pesos_bootstrap_temporadas.npz'),str(matrix):expected,str(Path(__file__).resolve()):sha(Path(__file__))},
        resumen=reports,segundos=round(time.perf_counter()-started,2)),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'COMPLETO: {out}',flush=True)


if __name__=='__main__':main()
