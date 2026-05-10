# ============================================================
# PROCESAMIENTO MASIVO: CORRELACIÓN PIXEL–SST PARA TODOS
# LOS PÍXELES BUENOS (CLUSTER ALTO) DE TODOS LOS CULTIVOS
# ============================================================

import os
import pandas as pd
import numpy as np
import xarray as xr
from scipy.stats import pearsonr
from multiprocessing import Pool
from functools import partial

# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

BASE = r"C:\Users\paola\Tesis"
SST_FILE = os.path.join(BASE, r"01_Data\SST\SST_monthly_detrended_1981_2025_fixed.nc")

CLUSTER_DIR = os.path.join(BASE, r"03_Resultados\Puntos\Kmeans_Calidad")
YIELD_DIR = os.path.join(BASE, r"02_Procesados\GDHY_detrend")

OUT_DIR = os.path.join(BASE, r"03_Resultados\Correlaciones\TodosBuenos")
os.makedirs(OUT_DIR, exist_ok=True)

CULTIVOS = ["maize", "rice", "wheat", "soybean"]

# Num procesos (14 cores – 2 libres)
NPROC = 12


# ============================================================
# FUNCIÓN PEARSON
# ============================================================

def pearson_full(x, y):
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 5:
        return np.nan, np.nan
    r, p = pearsonr(x[mask], y[mask])
    return r, p


# ============================================================
# PROCESAR UN SOLO PIXEL (USADO EN MULTIPROCESS)
# ============================================================

def procesar_pixel(lat_sel, lon_sel, cultivo, sst, da):
    """
    Procesa 1 pixel: calcula las correlaciones mensuales y guarda corr.nc + pval.nc
    """

    # Normalizar serie del pixel
    y_pix = da.sel(lat=lat_sel, lon=(lon_sel + 360) % 360, method="nearest")
    y_pix = (y_pix - y_pix.mean("time")) / y_pix.std("time")

    r_list = []
    p_list = []

    for m in range(1, 13):

        # SST mensual
        sst_m = sst.where(sst.month == m, drop=True).groupby("year").mean("time")

        # Años comunes
        years = np.intersect1d(sst_m.year.values, y_pix.time.dt.year.values)

        sst_c = sst_m.sel(year=years)
        y_c = y_pix.sel(time=pd.to_datetime(years, format="%Y"))

        r_map, p_map = xr.apply_ufunc(
            pearson_full,
            sst_c, y_c,
            input_core_dims=[["year"], ["time"]],
            output_core_dims=[[], []],
            vectorize=True,
            dask="parallelized",
            output_dtypes=[float, float]
        )

        r_list.append(r_map)
        p_list.append(p_map)

    # Convertir a DataArray
    corr = xr.concat(r_list, dim="month").assign_coords(month=np.arange(1, 13))
    pval = xr.concat(p_list, dim="month").assign_coords(month=np.arange(1, 13))

    # Guardado del pixel
    out_pixel = os.path.join(OUT_DIR, cultivo, f"{lat_sel}_{lon_sel}")
    os.makedirs(out_pixel, exist_ok=True)

    corr.to_netcdf(os.path.join(out_pixel, "corr.nc"))
    pval.to_netcdf(os.path.join(out_pixel, "pval.nc"))

    print(f"✔ {cultivo}  ({lat_sel}, {lon_sel}) guardado.")
    return True


# ============================================================
# BUCLE PRINCIPAL
# ============================================================

def main():

    print("\n==============================================")
    print(" PROCESO MASIVO DE CORRELACIONES INICIADO")
    print("==============================================\n")

    # =================================================
    # 1. Cargar SST una sola vez
    # =================================================
    print("Cargando SST...")

    ds_sst = xr.open_dataset(SST_FILE)
    var_sst = [v for v in ds_sst.data_vars if "sst" in v.lower()][0]

    sst = ds_sst[var_sst].sel(time=slice("1981", "2016"))
    sst = sst.coarsen(lat=4, lon=4, boundary="trim").mean()
    sst = sst.assign_coords(year=sst.time.dt.year, month=sst.time.dt.month)

    # Crear pool
    print(f"Usando {NPROC} procesos paralelos...\n")
    pool = Pool(processes=NPROC)

    # =================================================
    # 2. PROCESAR CADA CULTIVO
    # =================================================

    for cultivo in CULTIVOS:

        print(f"\n\n======= CULTIVO: {cultivo.upper()} =======")

        # Leer CSV de clusters
        fcsv = os.path.join(CLUSTER_DIR, f"{cultivo}_kmeans_clusters.csv")
        df = pd.read_csv(fcsv)

        # Seleccionar el cluster "bueno"
        cmax = df["cluster"].max()
        df_buenos = df[df["cluster"] == cmax]

        print(f"Píxeles buenos: {len(df_buenos)}")

        # Cargar rendimiento
        yrfile = os.path.join(YIELD_DIR, f"{cultivo}_yield_1981_2016_DETREND_clean.nc")
        ds_y = xr.open_dataset(yrfile)
        var_y = list(ds_y.data_vars)[0]
        da = ds_y[var_y]

        # Asegurar formato datetime
        if not np.issubdtype(da.time.dtype, np.datetime64):
            da = da.assign_coords(time=pd.to_datetime(np.arange(1981, 1981 + da.sizes["time"]), format="%Y"))

        # Lista de tareas lat/lon
        tareas_latlon = [
            (float(row.lat), float(row.lon))
            for _, row in df_buenos.iterrows()
        ]

        # Partial con variables fijas
        worker = partial(procesar_pixel, cultivo=cultivo, sst=sst, da=da)

        # Ejecutar en paralelo
        pool.starmap(worker, tareas_latlon)

    pool.close()
    pool.join()

    print("\n==============================================")
    print("   PROCESO MASIVO COMPLETADO EXITOSAMENTE")
    print(f"   Resultados guardados en: {OUT_DIR}")
    print("==============================================\n")


# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    main()
