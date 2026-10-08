"""Save lightweight exact H5 pixel selections, without reading correlation arrays."""
import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


def extract(h5_path,yield_path):
    import h5py
    import numpy as np
    with h5py.File(h5_path) as h:
        ii,jj=h['lat_idx'][...],h['lon_idx'][...]
    with h5py.File(yield_path) as h:
        lat,lon=h['lat'][...],h['lon'][...]
    if len(ii)!=len(jj) or len(set(zip(ii.tolist(),jj.tolist())))!=len(ii):
        raise ValueError('Selección con índices duplicados o tamaños incompatibles')
    if not (np.all(ii>=0) and np.all(ii<len(lat)) and np.all(jj>=0) and np.all(jj<len(lon))):
        raise ValueError('Índices fuera de la cuadrícula GDHY')
    return [dict(pixel_id=int(i)*len(lon)+int(j),h5_index=k,lat_idx=int(i),lon_idx=int(j),
                 latitude=float(lat[i]),longitude=float((lon[j]+180)%360-180))
            for k,(i,j) in enumerate(zip(ii,jj))]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tesis',default=r'C:\Users\paola\Tesis')
    parser.add_argument('--h5-dir',default='D:/')
    args=parser.parse_args()
    thesis=Path(args.tesis)
    out=thesis/'02_Procesados/Pixeles_correlacion_vigentes';out.mkdir(parents=True,exist_ok=True)
    repo=thesis/'Repositorio/tesis-cereal-climate/outputs/agroclima_vigente/diagnosticos/pixeles_correlacion'
    manifest={'purpose':'Exact original H5 selections; not new significance or yield-completeness filtering',
              'pixel_id_formula':'lat_idx * number_of_longitudes + lon_idx; longitude normalized to [-180,180)',
              'note':'h5_index preserves original H5 row order. No correlation dataset was loaded or copied.',
              'crops':{}}
    for crop in ['maize','soybean','rice','wheat']:
        h5=Path(args.h5_dir)/f'{crop}_correlacion_vectorizada.h5'
        nc=thesis/f'02_Procesados/GDHY_detrend/{crop}_yield_1981_2016_DETREND_clean.nc'
        rows=extract(h5,nc)
        path=out/f'pixeles_{crop}.csv';tmp=path.with_suffix('.tmp')
        with tmp.open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=['pixel_id','h5_index','lat_idx','lon_idx','latitude','longitude'])
            writer.writeheader();writer.writerows(rows)
        tmp.replace(path)
        manifest['crops'][crop]=dict(pixels=len(rows),source_h5=str(h5),source_yield=str(nc),
                                   source_h5_bytes=h5.stat().st_size,
                                   csv=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        print(f'{crop}: {len(rows)} píxeles guardados en {path}',flush=True)
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    if repo.parent.exists():
        repo.mkdir(parents=True,exist_ok=True)
        for f in out.glob('*'):
            if f.is_file():shutil.copy2(f,repo/f.name)


if __name__=='__main__':main()
