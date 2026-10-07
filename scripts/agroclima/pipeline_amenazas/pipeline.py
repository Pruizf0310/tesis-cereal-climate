"""CLI: prepare, export, status, analyze. Originals are read only."""
import argparse
import calendar
import csv
import hashlib
import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

DATASET = 'ECMWF/ERA5_LAND/DAILY_AGGR'
BANDS = ['temperature_2m_max', 'temperature_2m', 'temperature_2m_min']
AUTH_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


def authenticate_gee(force=False):
    """Cloud-only OAuth: direct downloads do not require Google Drive access."""
    import ee
    import shutil
    if not shutil.which('gcloud'):
        candidates = [Path.home()/'AppData/Local/Google/Cloud SDK/google-cloud-sdk/bin',
                      Path('C:/Program Files (x86)/Google/Cloud SDK/google-cloud-sdk/bin'),
                      Path('C:/Program Files/Google/Cloud SDK/google-cloud-sdk/bin')]
        for directory in candidates:
            if (directory/'gcloud.cmd').exists():
                os.environ['PATH'] = str(directory)+os.pathsep+os.environ.get('PATH','')
                break
    mode = 'gcloud' if shutil.which('gcloud') else 'localhost'
    print(f'Autenticación {mode}: Google Cloud; no se solicita acceso a Google Drive.',flush=True)
    ee.Authenticate(auth_mode=mode, scopes=AUTH_SCOPES, force=force)


def save_csv(path, rows, fields=None):
    if not rows and fields is None:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def phase_date(year, doy):
    # Calendar DOY denotes a climatological 365-day year: preserve month/day.
    if not 1 <= int(doy) <= 365:
        raise ValueError('Calendario requiere DOY de 1 a 365; revisar convención.')
    d = date(2001, 1, 1) + timedelta(days=int(doy)-1)
    return date(year, d.month, d.day)


def pixel_phase_windows(data, lat, lon):
    """Same intact technical blocks and half-open bounds as pixel-phenology.ts."""
    key = f'{lat:.2f},{((lon+180)%360-180):.2f}'
    value = data['pixels'].get(key)
    if value is None:
        return []
    phases = {}
    for i, stage in enumerate(data['templates']):
        labels = stage['macro_phases']
        if len(labels) != 1:
            raise ValueError('Correspondencia ambigua: revisar calendario vigente.')
        code = labels[0]
        start, end = value[3+i], value[4+i]
        phase = phases.setdefault(code, {'start': start, 'end': start, 'stages': []})
        if phase['end'] != start:
            raise ValueError('Bloques de fase no contiguos.')
        phase['end'] = end; phase['stages'].append(stage['code'])
    return [(code, phase, value[0]) for code, phase in phases.items()]


def absolute_reference_date(year, absolute_day):
    offset, day = divmod(absolute_day, 365)
    return phase_date(year+offset, day+1)


def prepare_versioned_calendar(c, selected, out):
    directory = Path(c['calendar_dir'])
    manifest = json.loads((directory/'manifest.json').read_text(encoding='utf8'))
    season_id = c['season']+'__'+c['water_system']
    entry = manifest['crops'][c['crop']]['seasons'][season_id]
    data = json.loads((directory/Path(entry['url']).name).read_text(encoding='utf8'))
    windows, unmatched = [], []
    for p in selected:
        phases = pixel_phase_windows(data, p['lat'], p['lon'])
        phase = next((v for code, v, planting in phases if code == c['phase']), None)
        if phase is None:
            unmatched.append(p['pixel_id']); continue
        planting = phases[0][2]
        for year in range(c['start_year'], c['end_year']+1):
            start = absolute_reference_date(year, planting-1+phase['start'])
            end_exclusive = absolute_reference_date(year, planting-1+phase['end'])
            windows.append(dict(pixel_id=p['pixel_id'], season_year=year, phase=c['phase'],
                start=start.isoformat(), end=(end_exclusive-timedelta(days=1)).isoformat(),
                calendar_id=season_id, timing_method='archived_blocks_six_phase_v4',
                calendar_quality='estimated_intermediate_dates', calendar_version=manifest['version']))
    if not windows:
        raise ValueError('Ningún píxel tiene la fase seleccionada en el calendario vigente.')
    save_csv(out/'windows_candidate.csv', windows)
    return dict(selected=len(selected), matched=len(selected)-len(unmatched), unmatched=unmatched,
        calendar_selection_confirmed=c['calendar_selection_confirmed'], calendar_version=manifest['version'],
        season_id=season_id, phase_year_label='planting year; yield-year alignment not yet verified',
        calendar_date_convention='365-day reference, half-open boundary preserves leap days')


def runs(dates, values, threshold, operator, min_days):
    """Gaps/missing values break runs. Return qualifying runs only."""
    import math
    compare = {'>=': lambda x: x >= threshold, '>': lambda x: x > threshold,
               '<=': lambda x: x <= threshold, '<': lambda x: x < threshold}[operator]
    result, active = [], []
    for d, v in list(zip(dates, values)) + [(None, None)]:
        hit = v is not None and math.isfinite(float(v)) and compare(float(v))
        if active and (not hit or d != active[-1][0] + timedelta(days=1)):
            if len(active) >= min_days:
                result.append(active)
            active = []
        if hit:
            active.append((d, float(v)))
    return result


def prepare(c, out):
    import h5py
    import numpy as np
    with h5py.File(c['h5']) as h:
        ii, jj = h['lat_idx'][...], h['lon_idx'][...]
    with h5py.File(c['yield_nc']) as h:
        lat, lon = h['lat'][...], h['lon'][...]
    if len(set(zip(ii.tolist(), jj.tolist()))) != len(ii):
        raise ValueError('Índices H5 duplicados.')
    pixels = []
    for k, (i, j) in enumerate(zip(ii, jj)):
        pixels.append(dict(pixel_id=int(i)*len(lon)+int(j), h5_index=k,
                           lat=float(lat[i]), lon=float((lon[j]+180)%360-180)))
    selected = pixels[:c['pixel_limit']] if c['pixel_limit'] else pixels
    if c.get('calendar_dir'):
        save_csv(out/'pixels.csv', selected)
        report = prepare_versioned_calendar(c, selected, out)
        report['h5_pixels'] = len(pixels)
        (out/'preparation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
        print(json.dumps(report, indent=2))
        return
    by_coord = {(round(p['lat'], 6), round(p['lon'], 6)): p for p in selected}
    windows = {}
    with open(c['calendar_csv'], encoding='utf-8-sig') as f:
        for r in csv.DictReader(f):
            if any(r[k] != c[k] for k in ['crop', 'season', 'water_system', 'crop_type']):
                continue
            if r['phase_code'] != c['calendar_phase'] or r['phase_axis'] != 'operational_exclusive':
                continue
            key = (round(float(r['latitude']), 6), round((float(r['longitude'])+180)%360-180, 6))
            if key not in by_coord:
                continue
            p = by_coord[key]
            for year in range(c['start_year'], c['end_year']+1):
                start = phase_date(year+int(r['start_year_offset']), r['phase_start_doy'])
                end = phase_date(year+int(r['end_year_offset']), r['phase_end_doy'])
                if end < start:
                    raise ValueError('Fecha final anterior a inicial.')
                row = dict(pixel_id=p['pixel_id'], season_year=year, phase=c['phase'],
                           start=start.isoformat(), end=end.isoformat(),
                           calendar_id=r['calendar_id'], timing_method=r['timing_method'],
                           calendar_quality=r['calendar_quality_flag'])
                wk = (p['pixel_id'], year)
                if wk in windows and windows[wk] != row:
                    raise ValueError(f'Calendarios ambiguos para {wk}')
                windows[wk] = row
    matched = {k[0] for k in windows}
    save_csv(out/'pixels.csv', selected)
    save_csv(out/'windows_candidate.csv', list(windows.values()))
    report = dict(h5_pixels=len(pixels), selected=len(selected), matched=len(matched),
                  unmatched=[p['pixel_id'] for p in selected if p['pixel_id'] not in matched],
                  calendar_selection_confirmed=c['calendar_selection_confirmed'],
                  phase_year_label='base year of source calendar; yield-year alignment not yet verified',
                  calendar_date_convention='365-day DOY converted to month/day; leap day included within windows')
    (out/'preparation.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


def initialize(c):
    import ee
    project = c['project']
    if not project or project.startswith('PONER_'):
        project = os.environ.get('EE_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT') or project
    if not project or project.startswith('PONER_'):
        raise ValueError('Indica --project ID_PROYECTO, EE_PROJECT o project en config.json.')
    ee.Initialize(project=project)
    return ee


def fetch_pages(ee, expression):
    """Fetch every computeFeatures page; bounded retries for transient errors."""
    params = {'expression': expression, 'pageSize': 1000}
    records = []
    while True:
        for attempt in range(4):
            try:
                response = ee.data.computeFeatures(params)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep([2, 5, 10][attempt])
        records.extend(feature['properties'] for feature in response.get('features', []))
        token = response.get('nextPageToken')
        if not token:
            return records
        params = params | {'pageToken': token}


def download(c, out):
    """Automatic local climate cache; monthly native-grid chunks, no Drive step."""
    if not c['calendar_selection_confirmed']:
        raise ValueError('Falta confirmar calendario.')
    if c['climate_day'] != 'UTC':
        raise ValueError('Este extractor requiere día UTC.')
    ee = initialize(c)
    pixels = list(csv.DictReader((out/'pixels.csv').open(encoding='utf-8-sig')))
    windows = list(csv.DictReader((out/'windows_candidate.csv').open(encoding='utf-8-sig')))
    if not windows:
        raise ValueError('No hay ventanas de calendario.')
    first = date.fromisoformat(min(w['start'] for w in windows)).year
    last = date.fromisoformat(max(w['end'] for w in windows)).year
    total = len(pixels)*(last-first+1)*12
    cache_dir = Path(c.get('climate_cache', out/'clima'))
    cache_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    pending = sum(
        not ((cache_dir/f"era5_UTC_{int(p['pixel_id'])}_{year}_{month:02d}.csv").exists()
             and (cache_dir/f"era5_UTC_{int(p['pixel_id'])}_{year}_{month:02d}.json").exists())
        for p in pixels for year in range(first, last+1) for month in range(1, 13))
    downloaded = 0
    download_seconds = 0.0
    def duration(seconds):
        seconds = int(round(seconds))
        return f'{seconds//86400}d {(seconds%86400)//3600:02d}h {(seconds%3600)//60:02d}m {seconds%60:02d}s'
    print(f'Descarga: {total} bloques mensuales; {pending} pendientes. '
          'Estimación disponible después del primer bloque nuevo; no incluye análisis final.', flush=True)
    number = 0
    for p in pixels:
        lat, lon, pid = float(p['lat']), float(p['lon']), int(p['pixel_id'])
        region = ee.Geometry.Rectangle([lon-.25, lat-.25, lon+.25, lat+.25], geodesic=False)
        for year in range(first, last+1):
            for month in range(1, 13):
                number += 1
                path = cache_dir/f'era5_UTC_{pid}_{year}_{month:02d}.csv'
                meta_path = path.with_suffix('.json')
                if path.exists() and meta_path.exists():
                    meta = json.loads(meta_path.read_text(encoding='utf8'))
                    if meta.get('dataset') == DATASET and meta.get('bands') == BANDS and meta.get('sha256') == hashlib.sha256(path.read_bytes()).hexdigest():
                        print(f'[{number}/{total}] Caché: {path.name}', flush=True)
                        continue
                    raise ValueError(f'Caché incompatible o alterada: {path}')
                start = date(year, month, 1)
                end = date(year+1, 1, 1) if month == 12 else date(year, month+1, 1)
                print(f'[{number}/{total}] GEE: {path.name}', flush=True)
                block_started = time.monotonic()
                images = ee.ImageCollection(DATASET).filterDate(start.isoformat(), end.isoformat()).select(BANDS)
                projection = ee.Image(images.first()).select(0).projection()
                def sample(image):
                    image = ee.Image(image)
                    values = image.subtract(273.15).rename(['tmax_c', 'tmean_c', 'tmin_c'])
                    values = values.addBands(ee.Image.pixelLonLat()).addBands(ee.Image.pixelCoordinates(projection))
                    return values.sample(region=region, projection=projection, dropNulls=False,
                        geometries=False, tileScale=4).map(lambda f: f.set({
                            'pixel_id': pid, 'date': image.date().format('YYYY-MM-dd')}))
                expression = ee.FeatureCollection(images.toList(images.size()).map(sample)).flatten()
                records = fetch_pages(ee, expression)
                if not records:
                    raise RuntimeError(f'GEE no devolvió celdas en {path.name}; no se registra como cero eventos.')
                fields = ['pixel_id','date','x','y','longitude','latitude','tmax_c','tmean_c','tmin_c']
                rows = [{key: r.get(key) for key in fields} for r in records]
                if len({(r['date'],r['x'],r['y']) for r in rows}) != len(rows):
                    raise ValueError('GEE devolvió celdas/fechas duplicadas.')
                temporary = path.with_suffix('.csv.tmp')
                save_csv(temporary, rows)
                temporary.replace(path)
                meta = {'dataset':DATASET,'bands':BANDS,'day':'UTC','pixel_id':pid,
                        'start':start.isoformat(),'end_exclusive':end.isoformat(),'rows':len(rows),
                        'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
                meta_path.write_text(json.dumps(meta,indent=2),encoding='utf8')
                downloaded += 1
                download_seconds += time.monotonic()-block_started
                remaining = max(0, pending-downloaded)
                eta = remaining*download_seconds/downloaded
                progress = {'stage':'download', 'blocks_visited':number, 'total_blocks':total,
                            'new_blocks_completed':downloaded, 'pending_new_blocks':remaining,
                            'elapsed_seconds':time.monotonic()-started,
                            'mean_seconds_per_new_block':download_seconds/downloaded,
                            'estimated_download_remaining_seconds':eta,
                            'note':'Estimate updates after each new block; excludes final analysis and future quota delays.'}
                (out/'progreso_descarga.json').write_text(json.dumps(progress,indent=2),encoding='utf8')
                print(f'Progreso {number}/{total} | Transcurrido: {duration(progress["elapsed_seconds"])} '
                      f'| Descarga restante estimada: {duration(eta)} '
                      f'| Media: {download_seconds/downloaded:.1f} s/bloque '
                      f'({downloaded} bloques medidos)', flush=True)
    print('Descarga terminada; las tres temperaturas quedan disponibles para otras reglas.',flush=True)


def export(c, out):
    if not c['calendar_selection_confirmed']:
        raise ValueError('Confirma selección de calendario antes de exportar.')
    if c['climate_day'] != 'UTC':
        raise ValueError('Este primer extractor es diario UTC. Día local requiere extractor horario.')
    ee = initialize(c)
    pixels = list(csv.DictReader((out/'pixels.csv').open(encoding='utf-8-sig')))
    windows = list(csv.DictReader((out/'windows_candidate.csv').open(encoding='utf-8-sig')))
    if not windows:
        raise ValueError('No hay ventanas de calendario.')
    first = date.fromisoformat(min(w['start'] for w in windows)).year
    last = date.fromisoformat(max(w['end'] for w in windows)).year
    tasks_path = out/'tasks.json'
    tasks = json.loads(tasks_path.read_text()) if tasks_path.exists() else {}
    for p in pixels:
        lat, lon, pid = float(p['lat']), float(p['lon']), p['pixel_id']
        region = ee.Geometry.Rectangle([lon-.25, lat-.25, lon+.25, lat+.25], geodesic=False)
        for year in range(first, last+1):
            key = f'era5_UTC_{pid}_{year}'
            if key in tasks:
                continue
            images = ee.ImageCollection(DATASET).filterDate(f'{year}-01-01', f'{year+1}-01-01').select(BANDS)
            projection = ee.Image(images.first()).select(0).projection()
            def sample(img):
                img = ee.Image(img)
                values = img.subtract(273.15).rename(['tmax_c', 'tmean_c', 'tmin_c'])
                values = values.addBands(ee.Image.pixelLonLat()).addBands(ee.Image.pixelCoordinates(projection))
                # Keep the native ERA grid; no temperature averaging before thresholds.
                return values.sample(region=region, projection=projection, dropNulls=False,
                                     geometries=False, tileScale=4).map(lambda f: f.set({
                                         'pixel_id': int(pid), 'date': img.date().format('YYYY-MM-dd')}))
            rows = ee.FeatureCollection(images.toList(images.size()).map(sample)).flatten()
            task = ee.batch.Export.table.toDrive(collection=rows, description=key,
                folder='Tesis_ERA5_cache', fileNamePrefix=key, fileFormat='CSV',
                selectors=['pixel_id', 'date', 'x', 'y', 'longitude', 'latitude', 'tmax_c', 'tmean_c', 'tmin_c'])
            task.start()
            tasks[key] = {'id': task.id, 'pixel_id': int(pid), 'year': year,
                          'dataset': DATASET, 'day': 'UTC'}
            tasks_path.write_text(json.dumps(tasks, indent=2), encoding='utf8')
            print(key, task.id, flush=True)
    print('Exportaciones registradas. Consultar status; descargar CSV de Drive a salidas/clima/.')


def analyze(c, out):
    import numpy as np
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if not c['calendar_selection_confirmed']:
        raise ValueError('Confirma calendario antes de interpretar resultados.')
    windows = pd.read_csv(out/'windows_candidate.csv')
    cache_dir = Path(c.get('climate_cache', out/'clima'))
    files = []
    for pid in windows.pixel_id.unique():
        sub = windows[windows.pixel_id == pid]
        first, last = date.fromisoformat(sub.start.min()).year, date.fromisoformat(sub.end.max()).year
        for year in range(first, last+1):
            files.extend(cache_dir.glob(f'era5_UTC_{int(pid)}_{year}_*.csv'))
            legacy = cache_dir/f'era5_UTC_{int(pid)}_{year}.csv'
            if legacy.exists(): files.append(legacy)
    files = sorted(files)
    if not files:
        raise ValueError('No hay clima guardado: ejecuta run o download.')
    df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    df['date'] = pd.to_datetime(df['date'])
    keys = ['pixel_id', 'x', 'y', 'date']
    if df.duplicated(keys).any():
        raise ValueError('Hay fechas/celdas duplicadas; revisar archivos de clima.')
    annual, events = [], []
    for w in windows.to_dict('records'):
        start, end = pd.Timestamp(w['start']), pd.Timestamp(w['end'])
        full_dates = pd.date_range(start, end)
        pixel = df[df.pixel_id == w['pixel_id']]
        for (x, y), sub in pixel.groupby(['x', 'y']):
            series = sub.set_index('date')[c['variable']].reindex(full_dates)
            found = runs([t.date() for t in full_dates], series.tolist(), c['threshold'], c['operator'], c['min_days'])
            complete = bool(series.notna().all())
            base = dict(crop=c['crop'], pixel_id=w['pixel_id'], x=int(x), y=int(y),
                        season_year=w['season_year'], phase=c['phase'], source=c['source'])
            annual.append(base | dict(start=w['start'], end=w['end'], valid_days=int(series.notna().sum()),
                total_days=len(series), quality='OK' if complete else 'INCOMPLETE',
                event_count=len(found) if complete else None,
                qualifying_days=sum(map(len, found)) if complete else None,
                longest_run=max(map(len, found), default=0) if complete else None,
                latitude=float(sub.latitude.iloc[0])))
            for e in found:
                events.append(base | dict(start=e[0][0].isoformat(), end=e[-1][0].isoformat(),
                                         days=len(e), peak=max(v for _, v in e), quality='OK' if complete else 'INCOMPLETE'))
    if not annual:
        raise ValueError('No hay celdas climáticas coincidentes.')
    result = pd.DataFrame(annual)
    result.to_csv(out/'frecuencia_por_celda_fase.csv', index=False)
    save_csv(out/'eventos.csv', events, fields=['crop','pixel_id','x','y','season_year','phase','source','start','end','days','peak','quality'])
    # Frequency across available complete seasons; zero events remain in denominator.
    ok = result[result.quality == 'OK'].copy()
    if ok.empty:
        raise ValueError('No hay ventanas completas; revisar cobertura climática.')
    freq = ok.groupby(['pixel_id', 'x', 'y', 'phase']).agg(
        seasons=('event_count', 'size'), total_events=('event_count', 'sum'),
        events_per_season=('event_count', 'mean'),
        seasons_with_events=('event_count', lambda s: (s > 0).sum())).reset_index()
    freq['fraction_seasons_with_events'] = freq.seasons_with_events / freq.seasons
    freq.to_csv(out/'frecuencia_historica.csv', index=False)
    ok['weight'] = np.cos(np.deg2rad(ok.latitude))
    ok['weighted_events'] = ok.event_count * ok.weight
    ok['weighted_exposed'] = (ok.event_count > 0) * ok.weight
    agg = ok.groupby(['pixel_id', 'season_year', 'phase']).agg(
        weight=('weight', 'sum'), weighted_events=('weighted_events', 'sum'),
        weighted_exposed=('weighted_exposed', 'sum'), native_cells=('x', 'size')).reset_index()
    agg['mean_events_per_native_cell'] = agg.weighted_events / agg.weight
    agg['evaluated_area_fraction_with_event'] = agg.weighted_exposed / agg.weight
    agg.to_csv(out/'resumen_GDHY.csv', index=False)
    fig, ax = plt.subplots(figsize=(9, 4))
    for pid, sub in agg.groupby('pixel_id'):
        ax.plot(sub.season_year, sub.mean_events_per_native_cell, marker='o', label=str(pid))
    ax.set(xlabel='Año base del calendario', ylabel='Eventos medios por celda climática',
           title=f"{c['crop']} — {c['phase']}: {c['variable']} {c['operator']} {c['threshold']} °C, ≥{c['min_days']} días")
    ax.legend(title='Píxel GDHY'); fig.tight_layout(); fig.savefig(out/'frecuencia_anual.png', dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8, 4))
    max_events = int(ok.event_count.max())
    ax.hist(ok.event_count, bins=np.arange(-.5, max_events+1.5, 1), edgecolor='white')
    ax.set(xlabel='Eventos por celda climática y temporada', ylabel='Número de observaciones celda–temporada',
           title=f"Distribución de frecuencias — {c['crop']} {c['phase']}")
    fig.tight_layout(); fig.savefig(out/'distribucion_frecuencias.png', dpi=160); plt.close(fig)
    provenance = dict(config=c, dataset=DATASET, files={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in files},
        note='Area evaluated, not crop-area weighted. Incomplete seasons excluded; no yield association until year alignment validated.')
    (out/'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf8')
    print('Resultados y gráfico guardados en', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('command', choices=['run', 'prepare', 'download', 'export', 'status', 'analyze', 'authenticate'])
    ap.add_argument('--config', default=str(Path(__file__).with_name('config.json')))
    ap.add_argument('--project', help='ID del proyecto GEE; sustituye config solo durante esta ejecución')
    args = ap.parse_args()
    config_path = Path(args.config).resolve()
    c = json.loads(config_path.read_text(encoding='utf8'))
    if args.project: c['project'] = args.project
    out = config_path.parent / c['output']; out.mkdir(parents=True, exist_ok=True)
    (out/'clima').mkdir(exist_ok=True)
    if args.command == 'run':
        import ee
        project = args.project or os.environ.get('EE_PROJECT') or os.environ.get('GOOGLE_CLOUD_PROJECT') or c['project']
        if not project or project.startswith('PONER_'):
            project = input('ID de tu proyecto habilitado en GEE: ').strip()
            if not project:
                raise ValueError('El ID de proyecto es obligatorio.')
        c['project'] = project
        status_path = out/'run_status.json'
        status_path.write_text(json.dumps({'status':'RUNNING','config':c},indent=2),encoding='utf8')
        try:
            authenticate_gee()
            prepare(c, out)
            download(c, out)
            analyze(c, out)
        except Exception as exc:
            status_path.write_text(json.dumps({'status':'FAILED','error':str(exc),'config':c},indent=2),encoding='utf8')
            raise
        status_path.write_text(json.dumps({'status':'COMPLETED','config':c},indent=2),encoding='utf8')
    elif args.command == 'prepare': prepare(c, out)
    elif args.command == 'download': download(c, out)
    elif args.command == 'export': export(c, out)
    elif args.command == 'analyze': analyze(c, out)
    elif args.command == 'authenticate':
        authenticate_gee(force=True)
    else:
        ee = initialize(c)
        tasks = json.loads((out/'tasks.json').read_text())
        for key, task in tasks.items():
            print(key, ee.data.getTaskStatus(task['id'])[0])
    if c.get('repository_results'):
        import shutil
        destination = Path(c['repository_results'])
        destination.mkdir(parents=True, exist_ok=True)
        # Climate cache stays in thesis; version derived outputs and provenance.
        for item in out.iterdir():
            if item.is_file(): shutil.copy2(item, destination/item.name)


if __name__ == '__main__': main()
