"""Compare every published calendar endpoint with the original GGCMI NetCDF grid."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import h5py

ROOT = Path(__file__).resolve().parents[1]
PREFIX = {'maize': 'mai', 'rice_1': 'ri1', 'rice_2': 'ri2',
          'soybean': 'soy', 'spring_wheat': 'swh', 'winter_wheat': 'wwh'}
MD5 = {
    'mai_ir': 'b51586de1f1017ab06439300386b1abb', 'mai_rf': '30886422bdfb9d3655e8396c4f7cff41',
    'ri1_ir': 'ece9aede389db223ff2919470c61bc4c', 'ri1_rf': '087961d0c2b5cb16971804318908337d',
    'ri2_ir': '491aa2312f06494962bad863d881e8b6', 'ri2_rf': 'ffdb642ddee073e253f65b4185430baa',
    'soy_ir': 'e5a62341a09c684e9af6cf64a2d36bc5', 'soy_rf': 'ff26e022c463fccbf96ceb72ce05b7a3',
    'swh_ir': 'bfba2387651c337a42879431036bc964', 'swh_rf': '68a597731d26b1ea5f3348131413c22c',
    'wwh_ir': '7f2fa18beb3bacca7e03c437476a0d4e', 'wwh_rf': 'b561771b343efd3978326611fa058442',
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    public = ROOT / 'web-v2/public'
    manifest = json.loads((public / 'data/pixel-calendars/manifest.json').read_text())
    result = {'source': 'https://zenodo.org/records/5062513',
              'calendar_version': manifest['version'], 'seasons': []}
    for crop in manifest['crops'].values():
        for season, entry in crop['seasons'].items():
            name, water = season.split('__')
            code = PREFIX[name] + '_' + water
            source = args.source / (code + '_ggcmi_crop_calendar_phase3_v1.01.nc4')
            checksum = hashlib.md5(source.read_bytes()).hexdigest()
            data = json.loads((public / entry['url'].lstrip('/')).read_text())
            stats = {'season': season, 'cells': len(data['pixels']), 'md5': checksum,
                     'matches_published_md5': checksum == MD5[code],
                     'endpoint_mismatches': 0, 'invalid_source_cells': 0,
                     'source_length_difference_counts': Counter(), 'examples': []}
            with h5py.File(source) as nc:
                lat_index = {float(v): i for i, v in enumerate(nc['lat'][:])}
                lon_index = {float(v): i for i, v in enumerate(nc['lon'][:])}
                planting, maturity, length = [nc[k][:] for k in
                                              ('planting_day', 'maturity_day', 'growing_season_length')]
                for cell, values in data['pixels'].items():
                    lat, lon = map(float, cell.split(','))
                    y, x = lat_index[lat], lon_index[lon]
                    p, m = float(planting[y, x]), float(maturity[y, x])
                    if not (1 <= p <= 365 and 1 <= m <= 365):
                        stats['invalid_source_cells'] += 1
                        continue
                    end = (values[0] - 1 + values[1] - 1) % 365 + 1
                    if values[0] != p or end != m:
                        stats['endpoint_mismatches'] += 1
                        if len(stats['examples']) < 5:
                            stats['examples'].append({'cell': cell, 'web': [values[0], end], 'source': [p, m]})
                    stats['source_length_difference_counts'][str(values[1] - float(length[y, x]))] += 1
            stats['hemisphere_examples'] = []
            for latitude, longitude in [(40, -95), (-35, -60)]:
                cell = min(data['pixels'], key=lambda c: sum((a-b)**2 for a,b in
                           zip(map(float, c.split(',')), [latitude, longitude])))
                values = data['pixels'][cell]
                stats['hemisphere_examples'].append({'cell': cell, 'planting_doy': values[0],
                    'maturity_doy': (values[0] + values[1] - 2) % 365 + 1, 'inclusive_days': values[1]})
            result['seasons'].append(stats)
    result['total_cells'] = sum(s['cells'] for s in result['seasons'])
    result['endpoint_mismatches'] = sum(s['endpoint_mismatches'] for s in result['seasons'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    if result['endpoint_mismatches'] or any(not s['matches_published_md5'] or s['invalid_source_cells'] for s in result['seasons']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
