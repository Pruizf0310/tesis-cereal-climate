from pathlib import Path
import ast
p=Path('maize_mjo_semanal.py')
s=p.read_text(encoding='utf-8-sig')
s=s[:s.index('def weekly_features(')]+s[s.index('def figures('):]
s=s.replace('Pearson semanal MJO–ocurrencias por fase; GEE reanudable y gráficos automáticos.','Pearson diario MJO–ocurrencias por fase; fechas persistentes y gráficos automáticos.')
s=s.replace('vs weekly climate-threshold occurrences','vs daily climate-threshold occurrences').replace('Pearson · same 7-day windows','Pearson · same-day UTC pairs · daily RMM').replace('Weekly observations are temporally dependent.','Daily observations are temporally dependent.')
s=s.replace("ap.add_argument('--min-weeks',type=int,default=20)","ap.add_argument('--min-days',type=int,default=20)\n    ap.add_argument('--cache-only',action='store_true',help='Usar exclusivamente fechas ya guardadas, sin iniciar GEE')")
s=s.replace('args.min_weeks','args.min_days').replace('min-weeks (≥3)','min-days (≥3)')
old="fp=hashlib.sha256((sha(calendar_path)+json.dumps(rules,sort_keys=True)+sha(Path(__file__))+sha(Path(__file__).with_name('fechas_ocurrencias_core.py'))).encode()).hexdigest()[:16]\n    cache=root/'02_Procesados/Clima_ERA5_Land_cache/MJO_fechas'/fp;cache.mkdir(parents=True,exist_ok=True)"
new="""base_fp=sha(calendar_path)+json.dumps(rules,sort_keys=True)
    helper_hash=sha(Path(__file__).with_name('fechas_ocurrencias_core.py'))
    fp=hashlib.sha256((base_fp+helper_hash+'native_daily_flags_v1').encode()).hexdigest()[:16]
    legacy=hashlib.sha256((base_fp+sha(Path(__file__).with_name('maize_mjo_semanal.py'))+helper_hash).encode()).hexdigest()[:16]
    cache_root=root/'02_Procesados/Clima_ERA5_Land_cache/MJO_fechas'
    cache=cache_root/(legacy if (cache_root/legacy).is_dir() else fp)
    cache.mkdir(parents=True,exist_ok=True)"""
assert old in s;s=s.replace(old,new)
s=s.replace("base/'correlaciones/maize_MJO_semanal'","base/'correlaciones/maize_MJO_diario'")
s=s.replace('NUEVO cálculo semanal, no reutiliza los conteos anuales como si fueran diarios. Puede ser costoso a escala global.','Cruce DIARIO: ocurrencias confirmadas y RMM1/RMM2 de la misma fecha. Sin promedios semanales.')
s=s.replace("ee=initialize_gee(plan['config'])","ee=None if args.cache_only else initialize_gee(plan['config'])")
s=s.replace("total=len(coords)*36;first=True;first_daily=True;first_events=True","total=len(coords)*36;first_daily=True;first_events=True")
s=s.replace("    with gzip.open(out/'weekly_pairs.csv.gz','wt',encoding='utf-8',newline='') as stream, \\\n         gzip.open", "    with gzip.open")
a=s.index("                for component in ['component1','component2']:frame[component]=np.nan")
b=s.index('                completed+=1',a)
s=s[:a]+"""                accumulate_daily(stats,daily,index,lookup)
"""+s[b:]
s=s.replace("t['n_weeks']=n.astype(int)","t['n_days']=n.astype(int)").replace('INSUFFICIENT_WEEKS','INSUFFICIENT_DAYS')
s=s.replace("out/'pearson_weekly_by_pixel_phase.csv'","out/'pearson_daily_by_pixel_phase.csv'")
s=s.replace('weekly_days=7,lag=0,min_weeks=args.min_days','aggregation_days=1,lag_days=0,min_days=args.min_days')
s=s.replace('All phase days saved, including trailing partial weeks. Only Pearson weekly aggregation discards final partial weeks; phases shorter than 7 days contribute no Pearson weekly observations.','All valid phase days included, including zero-event days and final partial weeks. No 7-day grouping.')
s=s.replace('Heat episodes counted on qualification day using full phase context before weekly slicing. Source phase boundary clipping retained.','Heat episodes counted on qualification day; precipitation occurrences are individual threshold days. Source phase boundary clipping retained.')
s=s.replace('Seven-day means may attenuate intraweek variability. RMM1/RMM2 coefficients separately do not establish a joint MJO effect.','Same-day RMM1/RMM2 values, no averaging. Separate coefficients do not establish a joint MJO effect.')
s=s.replace('No significance claim based on weekly sample size.','No significance claim based on daily sample size.')
s=s.replace("repo/'outputs/agroclima_vigente/correlaciones/maize_MJO_semanal'","repo/'outputs/agroclima_vigente/correlaciones/maize_MJO_diario'")
insert='''def accumulate_daily(stats,daily,index,lookup):
    """Pair exact dates, retain valid zero counts; no phase/month/year averaging."""
    values=index.reindex(pd.to_datetime(daily.date))
    for phase,positions in daily.groupby('phase').indices.items():
        part=daily.iloc[positions]
        y=part.mean_occurrences_qualified.to_numpy(dtype=float)
        climate=(part.quality=='OK').to_numpy() & np.isfinite(y)
        p=PHASES.index(phase);i=lookup[int(part.pixel_id.iloc[0])]
        for component in range(2):
            x=values.iloc[positions,component].to_numpy(dtype=float)
            ok=climate & np.isfinite(x);a=x[ok];b=y[ok]
            stats[component,p,i]+=np.array([len(a),a.sum(),b.sum(),(a*a).sum(),(b*b).sum(),(a*b).sum()])


'''
s=s.replace('def main():',insert+'def main():')
ast.parse(s)
Path('maize_mjo_diario.py').write_text(s,encoding='utf-8')
print('Script diario creado; sintaxis correcta; no se ejecutó el cálculo.')
