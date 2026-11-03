"""Auditoría del rendimiento GDHY por píxel: unidades, plausibilidad frente a FAOSTAT,
convención de año y reproducción del detrend. Solo lee; no modifica datos crudos.

Uso (desde la raíz del repo):
    python -X utf8 scripts/agroclima/auditoria_rendimiento/auditar_rendimiento_gdhy.py --crop maize
"""
import argparse
import json
import struct
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from matplotlib.path import Path as MplPath

REPO = Path(__file__).resolve().parents[3]
ROOT = Path('C:/Users/paola/Tesis')
NE = Path('C:/Users/paola/.local/share/cartopy/shapefiles/natural_earth/cultural/ne_50m_admin_0_countries')
YEARS = np.arange(1981, 2017)
# Umbral absoluto de plausibilidad (t/ha, grano, promedio de celda de 0,5°). Por encima del récord
# nacional FAOSTAT 1981-2016 de cualquier país productor relevante; se documenta en docs/.
ABS_MAX = {'maize': 15.0, 'rice': 12.0, 'soybean': 5.5, 'wheat': 10.0}
RATIO_MAX = 3.0  # bandera blanda: celda > 3 × rendimiento nacional FAOSTAT del mismo año (solo informativa)


def read_dbf(path, fields):
    with open(path, 'rb') as f:
        head = f.read(32)
        n, header_len, rec_len = struct.unpack('<IHH', head[4:12])
        spec = []
        while True:
            d = f.read(32)
            if d[0] == 0x0D:
                break
            spec.append((d[:11].split(b'\0')[0].decode(), d[16]))
        f.seek(header_len)
        rows = []
        for _ in range(n):
            rec = f.read(rec_len)[1:]
            pos, row = 0, {}
            for name, size in spec:
                if name in fields:
                    row[name] = rec[pos:pos + size].decode('latin-1').strip()
                pos += size
            rows.append(row)
    return rows


def read_polygons(path):
    """Lector mínimo de .shp tipo polígono (5): devuelve lista de listas de anillos."""
    out = []
    with open(path, 'rb') as f:
        f.seek(100)
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            length = struct.unpack('>i', head[4:])[0] * 2
            rec = f.read(length)
            if struct.unpack('<i', rec[:4])[0] != 5:
                out.append([])
                continue
            nparts, npts = struct.unpack('<ii', rec[36:44])
            parts = list(struct.unpack(f'<{nparts}i', rec[44:44 + 4 * nparts])) + [npts]
            pts = np.frombuffer(rec[44 + 4 * nparts:44 + 4 * nparts + 16 * npts], '<f8').reshape(-1, 2)
            out.append([pts[parts[k]:parts[k + 1]] for k in range(nparts)])
    return out


def assign_country(lat, lon):
    """ISO3 por punto central; si cae en costa/agua prueba desplazamientos de ±0,25°."""
    attrs = read_dbf(str(NE) + '.dbf', {'ISO_A3', 'ADM0_A3', 'NAME'})
    polys = read_polygons(str(NE) + '.shp')
    iso = np.array([''] * len(lat), dtype=object)
    offsets = [(0, 0), (.25, 0), (-.25, 0), (0, .25), (0, -.25), (.25, .25), (-.25, -.25), (.25, -.25), (-.25, .25)]
    for dy, dx in offsets:
        todo = np.flatnonzero(iso == '')
        if not len(todo):
            break
        pts = np.column_stack([lon[todo] + dx, lat[todo] + dy])
        for a, rings in zip(attrs, polys):
            code = a['ISO_A3'] if a['ISO_A3'] not in ('-99', '') else a['ADM0_A3']
            for ring in rings:
                hit = MplPath(ring).contains_points(pts)
                if hit.any():
                    sel = todo[hit]
                    iso[sel] = np.where(iso[sel] == '', code, iso[sel])
    return iso


def nanstat(fn, a):
    ok = np.isfinite(a).any(1)
    out = np.full(len(a), np.nan)
    out[ok] = fn(a[ok], 1)
    return out.round(3)


def linear_detrend_by_year(s):
    """Detrend lineal contra el AÑO real (respeta huecos), para comparar con el archivo."""
    m = np.isfinite(s)
    out = np.full_like(s, np.nan)
    if m.sum() >= 5:
        b, a = np.polyfit(YEARS[m], s[m], 1)
        out[m] = s[m] - (a + b * YEARS[m])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--crop', choices=list(ABS_MAX), default='maize')
    args = ap.parse_args()
    crop = args.crop
    t0 = time.perf_counter()
    out = REPO / 'outputs/agroclima_vigente/auditoria_rendimiento' / crop
    out.mkdir(parents=True, exist_ok=True)

    px = pd.read_csv(ROOT / f'02_Procesados/Pixeles_correlacion_vigentes/pixeles_{crop}.csv', encoding='utf-8-sig')
    li, lj = px.lat_idx.to_numpy(), px.lon_idx.to_numpy()

    # Crudo GDHY v1.2+v1.3 apilado (time, lat, lon); fill -9.99e8. Unidades oficiales: t/ha.
    with h5py.File(ROOT / f'02_Procesados/GDHY_timeseries/{crop}_yield_1981_2016_RAW.nc', 'r') as f:
        v = f['var']
        assert v.shape == (36, 360, 720), v.shape
        raw = v[:][:, li, lj]
        lat, lon = f['lat'][:], f['lon'][:]
    raw = raw.astype('f8').T
    raw[raw < -1e8] = np.nan
    assert np.allclose(lat[li], px.latitude) and np.allclose((lon[lj] + 180) % 360 - 180, px.longitude)

    # Detrendido usado en el cruce (lat, lon, time), sin atributo de unidades.
    with h5py.File(ROOT / f'02_Procesados/GDHY_detrend/{crop}_yield_1981_2016_DETREND_clean.nc', 'r') as f:
        v = f['var']
        assert v.shape == (360, 720, 36), v.shape
        det = v[:][li, lj, :].astype('f8')
        det_units = v.attrs.get('units', b'SIN_UNIDADES')

    # 1. País y FAOSTAT
    iso = assign_country(px.latitude.to_numpy(), px.longitude.to_numpy())
    fao = pd.read_csv(REPO / f'metadata/reference/faostat_owid_{crop}_yield_t_ha.csv')
    fao.columns = ['entity', 'code', 'year', 'yield_t_ha']
    fao = fao[fao.year.between(1981, 2016) & fao.code.notna()]
    table = fao.pivot_table(index='code', columns='year', values='yield_t_ha')
    nat = np.full(raw.shape, np.nan)
    for k, code in enumerate(iso):
        if code in table.index:
            nat[k] = table.loc[code].reindex(YEARS).to_numpy()
    ratio = raw / nat

    # 2. Banderas de plausibilidad por píxel-año
    flag_abs = raw > ABS_MAX[crop]      # inverosímil: se enmascara en el cálculo por lotes
    flag_ratio = ratio > RATIO_MAX      # dudoso: se informa, no se excluye
    flag = flag_abs | flag_ratio

    # 3. Detrend: ¿reproduce scipy.signal.detrend (índice, no año) o detrend por año?
    gaps = np.isfinite(raw).sum(1) < 36
    d_year = np.array([linear_detrend_by_year(s) for s in raw])
    diff_year = np.nanmax(np.abs(d_year - det), axis=1)

    # 4. Convención de año: faltantes de 1981 y 2016 por hemisferio (GDHY sin satélite antes de jul-1981)
    south = px.latitude.to_numpy() < 0
    year_conv = pd.DataFrame({
        'hemisferio': ['norte', 'sur'],
        'pixeles': [int((~south).sum()), int(south.sum())],
        'faltante_1981_pct': [100 * np.isnan(raw[~south, 0]).mean(), 100 * np.isnan(raw[south, 0]).mean()],
        'faltante_2016_pct': [100 * np.isnan(raw[~south, -1]).mean(), 100 * np.isnan(raw[south, -1]).mean()],
    })

    pix = pd.DataFrame({
        'pixel_id': px.pixel_id, 'latitude': px.latitude, 'longitude': px.longitude, 'iso3': iso,
        'anios_validos': np.isfinite(raw).sum(1),
        'raw_media_t_ha': np.nanmean(raw, 1).round(3), 'raw_max_t_ha': np.nanmax(raw, 1).round(3),
        'fao_media_t_ha': nanstat(np.nanmean, nat), 'ratio_mediano': nanstat(np.nanmedian, ratio),
        'anios_sobre_umbral_abs': flag_abs.sum(1), 'anios_ratio_fao_mayor_3': flag_ratio.sum(1),
        'anios_marcados': flag.sum(1),
        'tiene_huecos': gaps, 'detrend_archivo_vs_por_anio_maxdiff': diff_year.round(4),
    })
    validos_tras_mascara = (np.isfinite(raw) & ~flag_abs).sum(1)
    pix['anios_validos_tras_mascara'] = validos_tras_mascara
    pix['clase'] = np.select(
        [validos_tras_mascara < 20, pix.anios_sobre_umbral_abs > 0, pix.anios_ratio_fao_mayor_3 > 0],
        ['EXCLUIDO_MENOS_20_ANIOS_TRAS_MASCARA', 'ANIOS_INVEROSIMILES_ENMASCARADOS', 'DUDOSO_RATIO_FAO'], 'OK')
    pix.to_csv(out / 'auditoria_por_pixel.csv', index=False)

    k, j = np.nonzero(flag)
    pd.DataFrame({'pixel_id': px.pixel_id.to_numpy()[k], 'iso3': iso[k], 'year': YEARS[j],
                  'raw_t_ha': raw[k, j].round(3), 'fao_nacional_t_ha': nat[k, j].round(3),
                  'ratio': ratio[k, j].round(3), 'detrendido': det[k, j].round(3)}
                 ).to_csv(out / 'pixel_anios_marcados.csv', index=False)

    by_country = pix.groupby('iso3').agg(pixeles=('pixel_id', 'size'), raw_media=('raw_media_t_ha', 'median'),
                                         fao_media=('fao_media_t_ha', 'median'), ratio_mediano=('ratio_mediano', 'median'),
                                         pixeles_marcados=('anios_marcados', lambda s: int((s > 0).sum()))
                                         ).sort_values('pixeles', ascending=False)
    by_country.round(3).to_csv(out / 'resumen_por_pais.csv')
    year_conv.round(2).to_csv(out / 'convencion_anio_faltantes.csv', index=False)

    summary = {
        'cultivo': crop, 'pixeles': int(len(px)),
        'unidades_gdhy': 't/ha (documentación DIAS GDHY v1.2+v1.3; el NetCDF crudo no trae atributo units)',
        'unidades_detrendido': det_units.decode() if isinstance(det_units, bytes) else str(det_units),
        'raw_percentiles_t_ha': dict(zip(['p50', 'p95', 'p99', 'p99_9', 'max'],
                                         np.nanpercentile(raw, [50, 95, 99, 99.9, 100]).round(2).tolist())),
        'umbral_absoluto_t_ha': ABS_MAX[crop], 'umbral_ratio_fao': RATIO_MAX,
        'pixel_anios_sobre_umbral_abs': int(flag_abs.sum()), 'pixel_anios_ratio_fao_mayor_3': int(flag_ratio.sum()),
        'pixel_anios_marcados': int(flag.sum()), 'pixeles_con_algun_anio_marcado': int((pix.anios_marcados > 0).sum()),
        'clases_pixel': pix.clase.value_counts().to_dict(),
        'pixeles_sin_pais': int((iso == '').sum()), 'pixeles_sin_fao': int(np.isnan(nat).all(1).sum()),
        'detrend_pixeles_con_huecos': int(gaps.sum()),
        'detrend_maxdiff_sin_huecos': float(np.nanmax(diff_year[~gaps])) if (~gaps).any() else None,
        'detrend_maxdiff_con_huecos': float(np.nanmax(diff_year[gaps])) if gaps.any() else None,
        'segundos': round(time.perf_counter() - t0, 1),
    }
    (out / 'resumen_auditoria.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(year_conv.round(1).to_string(index=False))
    print(by_country.head(15).round(2).to_string())


if __name__ == '__main__':
    main()
