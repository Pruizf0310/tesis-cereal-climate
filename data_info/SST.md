# SST

- Descripción: temperatura superficial del mar usada como campo climático principal para correlaciones con rendimiento agrícola.
- Fuente oficial: pendiente de confirmar en documentación final; probablemente NOAA/OISST según nombres `sst.day.mean.*.nc`.
- Resolución espacial/temporal: archivos diarios; derivado mensual detrended a 0,5 grados identificado.
- Periodo: archivos anuales detectados entre 1980s y 2020s; derivado `1981_2025`.
- Formato: NetCDF `.nc`; derivados TIFF excluidos.
- Ruta original: `C:\Users\paola\Tesis\01_Data\SST`; `C:\Users\paola\Tesis\02_Procesados\SST_monthly_detrended_1981_2025_0p5deg35.nc`.
- Scripts relacionados: `notebooks/importantes/SST.ipynb`, `notebooks/importantes/TendRemove.ipynb`, `notebooks/importantes/Tend_Remove_All Cereals.ipynb`, `scripts/correlacion_masiva.py`.
- Outputs derivados: correlaciones SST-rendimiento, TIFF detrended locales, outputs web resumidos.
- Notas metodológicas: no versionar NetCDF/TIFF. Registrar versión, fuente, periodo, resolución y procesamiento de detrending.
