"""Build a local, georeferenced SQLite database from completed maize results."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

import numpy as np
import pandas as pd
from correlacion_oni_amenazas import read_oni


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def indices(oni_path, rmm_path):
    monthly, *_ = read_oni(oni_path)
    rmm = pd.read_csv(rmm_path, sep=r'\s+', skiprows=2, header=None,
                      usecols=range(7), names=['year', 'month', 'day', 'rmm1', 'rmm2', 'phase', 'amplitude'])
    rmm['date'] = pd.to_datetime(rmm[['year', 'month', 'day']])
    if rmm.date.duplicated().any():
        raise ValueError('Duplicate RMM dates')
    dates = pd.date_range(monthly.index.min(), monthly.index.max() + pd.offsets.MonthEnd(), freq='D')
    d = pd.DataFrame({'date': dates})
    d['oni'] = dates.to_period('M').to_timestamp().map(monthly)
    d = d.merge(rmm[['date', 'phase', 'amplitude', 'rmm1', 'rmm2']], how='left', on='date', validate='one_to_one')
    valid = d.phase.between(1, 8) & d.amplitude.between(0, 100, inclusive='left') & (d[['rmm1', 'rmm2']].abs() < 100).all(axis=1)
    d['mjo'] = np.where(valid, np.where(d.amplitude <= 1, 0, d.phase), np.nan)
    d['oni_state'] = np.where(d.oni.isna(), 'Missing', np.where(d.oni <= -.5, 'Nina', np.where(d.oni >= .5, 'Nino', 'Neutral')))
    # Operational episodes: >=5 consecutive monthly ONI centers beyond +/-0.5.
    # The peak is retained numerically; no undocumented severity classification.
    episodes = []
    m = monthly.reindex(pd.date_range(monthly.index.min(), monthly.index.max(), freq='MS'))
    states = np.where(m.isna(), 'Missing', np.where(m <= -.5, 'Nina', np.where(m >= .5, 'Nino', 'Neutral')))
    first = 0
    for end in range(1, len(m) + 1):
        if end == len(m) or states[end] != states[first]:
            if states[first] in ('Nina', 'Nino') and end - first >= 5:
                s = m.iloc[first:end]
                episodes.append(dict(episode_id=len(episodes)+1, state=states[first], start=str(s.index[0].date()),
                                     end=str((s.index[-1]+pd.offsets.MonthEnd()).date()), n_monthly_centers=len(s),
                                     peak_oni=float(s.max() if states[first]=='Nino' else s.min())))
            first = end
    e = pd.DataFrame(episodes, columns=['episode_id', 'state', 'start', 'end', 'n_monthly_centers', 'peak_oni'])
    return d[['date', 'oni', 'oni_state', 'mjo']], e


def exposure(windows, daily):
    """Inclusive calendar windows; missing indices are never neutral/weak."""
    dates = pd.DatetimeIndex(daily.date)
    if not dates.equals(pd.date_range(dates.min(), dates.max(), freq='D')):
        raise ValueError('Daily index must be continuous')
    a = (pd.to_datetime(windows.start)-dates[0]).dt.days.to_numpy()
    b = (pd.to_datetime(windows.end)-dates[0]).dt.days.to_numpy()+1
    if ((a < 0) | (b > len(daily)) | (b <= a)).any():
        raise ValueError('Index coverage does not contain every phase window')
    def total(values):
        prefix = np.r_[0, np.cumsum(np.asarray(values))]
        return prefix[b]-prefix[a]
    out = windows[['start', 'end']].copy()
    out['window_days'] = b-a
    n = total(daily.oni.notna())
    out['oni_valid_days'] = n
    out['oni_mean'] = np.divide(total(daily.oni.fillna(0)), n, out=np.full(len(n), np.nan), where=n>0)
    out['oni_state'] = np.where(n != b-a, 'Incomplete', np.where(out.oni_mean <= -.5, 'Nina', np.where(out.oni_mean >= .5, 'Nino', 'Neutral')))
    out['mjo_valid_days'] = total(daily.mjo.notna())
    joints = [{} for _ in range(len(out))]
    for state in ['Nina', 'Neutral', 'Nino']:
        out[f'{state}_days'] = total(daily.oni_state.eq(state))
        for phase in range(9):
            values = total(daily.oni_state.eq(state) & daily.mjo.eq(phase))
            for i in np.flatnonzero(values):
                joints[i][f'{state}_{phase}'] = int(values[i])
    for phase in range(9):
        out[f'mjo_{phase}_days'] = total(daily.mjo.eq(phase))
    out['joint_days_json'] = [json.dumps(v, separators=(',', ':')) for v in joints]
    return out


def graph(db, pixel, destination):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d = pd.read_sql_query('SELECT * FROM annual WHERE pixel_id=? ORDER BY season_year', db, params=[pixel])
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True, layout='constrained')
    for phase in ['EST', 'VEG', 'FLO', 'REP', 'FIL']:
        axes[0].plot(d.season_year, d[phase], label=phase)
    axes[0].set_ylabel('Episodios medios por celda'); axes[0].legend(ncol=5)
    axes[1].plot(d.season_year, d.yield_detrended, 'o-', label='Rendimiento sin tendencia')
    axes[1].plot(d.season_year, d.blocked_cv_prediction, '--', label='Predicción en bloques excluidos')
    axes[1].set_ylabel('Unidades del archivo original'); axes[1].set_xlabel('Año de siembra'); axes[1].legend()
    fig.suptitle(f'Maíz · píxel {pixel} · {destination.name}\nMAT (días de lluvia) se consulta por separado en SQL')
    fig.savefig(destination/'historia_pixel.png', dpi=160); plt.close(fig)
    s = pd.read_sql_query('SELECT * FROM comparisons WHERE pixel_id=?', db, params=[pixel])
    fig, ax = plt.subplots(figsize=(10, 6), layout='constrained')
    for state, offset, color in [('Nina', -.2, '#2166ac'), ('Neutral', 0, '#777777'), ('Nino', .2, '#b2182b')]:
        g = s[s.oni_state.eq(state)]
        for _, row in g.iterrows():
            x = ['EST','VEG','FLO','REP','FIL','MAT'].index(row.phase)+offset
            ax.scatter(x, row.mean_yield, color=color, marker='o' if row.eligible else 'x')
            ax.annotate(f'n={row.n_years}', (x, row.mean_yield), xytext=(0, 6), textcoords='offset points', fontsize=7)
        ax.scatter([], [], color=color, label=state)
    ax.set_xticks(range(6), ['EST','VEG','FLO','REP','FIL','MAT']); ax.set_ylabel('Rendimiento medio sin tendencia')
    ax.legend(); ax.set_title('ONI medio de cada ventana · x: menos de 5 años\nAsociación descriptiva; un año aparece en varias fases, no son réplicas independientes')
    fig.savefig(destination/'rendimiento_por_ONI.png', dpi=160); plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=Path('C:/Users/paola/Tesis'))
    ap.add_argument('--run', type=Path, help='Completed six-phase yield run; defaults to latest completed run')
    ap.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1]/'outputs/maize_sql')
    ap.add_argument('--alignment', choices=['same-label', 'maturity-year'], default='same-label')
    ap.add_argument('--pixel', type=int)
    ap.add_argument('--limit-pixels', type=int, help='Explicit pilot subset; omit for all pixels')
    args = ap.parse_args()
    base = args.root/'03_Resultados/Agroclima/vigente'
    runs = sorted((base/'rendimiento/maize_seis_fases').glob('*/completed.json'))
    run = args.run or (runs[-1].parent if runs else None)
    if run is None: raise FileNotFoundError('Run maize_amenazas_rendimiento.py first')
    meta = json.loads((run/'completed.json').read_text(encoding='utf-8'))
    source = Path(meta['source'])
    if sha(source) != meta['source_sha256']: raise ValueError('Hazard source differs from completed yield run')
    oni = args.root/'01_Data/ONI/ONI_v6_2026-10-08.html'
    rmm = args.root/'01_Data/RMM/rmm_official.txt'
    daily, episodes = indices(oni, rmm)
    folder = run/args.alignment
    pixels = pd.read_csv(folder/'pixel_model_summary.csv')
    if args.limit_pixels is not None:
        if args.limit_pixels < 1: ap.error('--limit-pixels must be positive')
        pixels = pixels.head(args.limit_pixels)
    ids = set(pixels.pixel_id)
    if args.pixel is not None and args.pixel not in ids: ap.error('--pixel outside selection')
    out = args.output/args.alignment
    out.mkdir(parents=True, exist_ok=True)
    final = out/'maize.sqlite'; pending = out/'maize.pending.sqlite'
    if final.exists() or pending.exists(): raise FileExistsError('Choose a new --output; existing databases are preserved')
    with closing(sqlite3.connect(pending)) as db, db:
        pixels.to_sql('pixel_models', db, index=False)
        p = pixels[['pixel_id','latitude','longitude']]
        p.to_sql('pixels', db, index=False)
        db.execute('CREATE UNIQUE INDEX pixel_key ON pixels(pixel_id)')
        db.execute('CREATE VIRTUAL TABLE pixel_bounds USING rtree(pixel_id,min_lon,max_lon,min_lat,max_lat)')
        db.executemany('INSERT INTO pixel_bounds VALUES (?,?,?,?,?)', [(int(r.pixel_id),r.longitude,r.longitude,r.latitude,r.latitude) for r in p.itertuples()])
        annual_path = folder/'paired_annual_counts_yield.csv.gz'
        for chunk in pd.read_csv(annual_path, chunksize=50000):
            chunk[chunk.pixel_id.isin(ids)].to_sql('annual', db, if_exists='append', index=False)
        db.execute('CREATE UNIQUE INDEX annual_key ON annual(pixel_id,season_year)')
        db.execute('CREATE INDEX annual_year ON annual(season_year)')
        pd.read_csv(folder/'phase_associations.csv').query('pixel_id in @ids').to_sql('phase_associations', db, index=False)
        daily.assign(date=daily.date.dt.strftime('%Y-%m-%d')).to_sql('daily_indices', db, index=False)
        episodes.to_sql('oni_episodes', db, index=False)
        processed = 0
        for chunk in pd.read_csv(source, chunksize=50000):
            chunk = chunk[chunk.pixel_id.isin(ids)].copy()
            if chunk.empty: continue
            w = chunk[['start','end']].drop_duplicates().reset_index(drop=True)
            chunk = chunk.merge(exposure(w,daily), on=['start','end'], validate='many_to_one')
            chunk.to_sql('phase_exposure', db, if_exists='append', index=False)
            processed += len(chunk)
            print(f'Fases integradas: {processed:,}', flush=True)
        db.execute('CREATE UNIQUE INDEX exposure_key ON phase_exposure(pixel_id,season_year,phase)')
        db.execute('CREATE INDEX exposure_state ON phase_exposure(oni_state,phase)')
        db.executescript('''
        CREATE VIEW consultation AS
        SELECT e.*,p.latitude,p.longitude,a.yield_year,a.yield_detrended,a.complete_pair,a.year_alignment
        FROM phase_exposure e JOIN pixels p USING(pixel_id) JOIN annual a USING(pixel_id,season_year);
        CREATE VIEW episode_overlap AS
        SELECT e.pixel_id,e.season_year,e.phase,o.episode_id,o.state,o.peak_oni,
               max(e.start,o.start) overlap_start,min(e.end,o.end) overlap_end
        FROM phase_exposure e JOIN oni_episodes o ON e.start<=o.end AND e.end>=o.start;
        CREATE TABLE comparisons AS
        SELECT pixel_id,phase,oni_state,count(*) n_years,avg(yield_detrended) mean_yield,
               count(*)>=5 eligible
        FROM consultation WHERE complete_pair=1 AND oni_state!='Incomplete'
        GROUP BY pixel_id,phase,oni_state;
        CREATE UNIQUE INDEX comparison_key ON comparisons(pixel_id,phase,oni_state);
        CREATE VIEW differences AS
        SELECT c.*,n.mean_yield neutral_mean,n.n_years neutral_n,
               CASE WHEN c.eligible AND n.eligible THEN c.mean_yield-n.mean_yield END difference_from_neutral
        FROM comparisons c LEFT JOIN comparisons n
        ON c.pixel_id=n.pixel_id AND c.phase=n.phase AND n.oni_state='Neutral';
        CREATE VIEW joint_seasons AS
        SELECT c.pixel_id,c.season_year,c.phase,c.yield_detrended,
               j.key index_combination,cast(j.value AS INTEGER) exposure_days
        FROM consultation c,json_each(c.joint_days_json) j
        WHERE c.complete_pair=1;
        CREATE VIEW joint_yield AS
        SELECT pixel_id,phase,index_combination,count(*) n_years,
               sum(exposure_days) total_exposure_days,avg(yield_detrended) mean_yield,
               count(*)>=5 eligible
        FROM joint_seasons WHERE exposure_days>=10
        GROUP BY pixel_id,phase,index_combination;
        ''')
        report = dict(pixels=len(p),annual_rows=db.execute('SELECT count(*) FROM annual').fetchone()[0],
                      phase_rows=processed,alignment=args.alignment,yield_units=meta['yield_units'],
                      source_run=str(run),pilot=args.limit_pixels is not None,
                      hashes={str(f):sha(f) for f in [source,annual_path,oni,rmm,Path(__file__)]},
                      caveats=['Calendar windows include both endpoints; MJO 0 means amplitude <=1.',
                               'ONI window categories use mean ONI, not episode intensity. See oni_episodes for episodes.',
                               'Joint index days measure exposure, not exact coincidence with hazard days.',
                               'Annual detrended yield: no percentage loss, monetary loss or causal attribution.',
                               'Coordinates EPSG:4326 are pixel centers, not field boundaries.',
                               'Five years is a display minimum, not a statistical significance test.'])
        pd.DataFrame([{'key':k,'value':json.dumps(v,ensure_ascii=False)} for k,v in report.items()]).to_sql('metadata',db,index=False)
        graph(db,args.pixel if args.pixel is not None else int(p.pixel_id.iloc[0]),out)
    pending.replace(final)
    features = [dict(type='Feature',geometry=dict(type='Point',coordinates=[r.longitude,r.latitude]),
                     properties=dict(pixel_id=int(r.pixel_id))) for r in p.itertuples()]
    (out/'pixels.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=features)),encoding='utf-8')
    (out/'completed.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'Terminado: {final}',flush=True)


if __name__ == '__main__':
    main()
