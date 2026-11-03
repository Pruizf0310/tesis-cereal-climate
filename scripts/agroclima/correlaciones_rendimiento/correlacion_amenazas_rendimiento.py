"""Correlación por píxel entre las seis amenazas de maíz (conteos por fase) y el rendimiento
GDHY detrendido, con control estadístico: n, r crítico, p (t y permutación), FDR
Benjamini–Hochberg y significancia de campo por permutación conjunta de años.

Procesa por bloques de píxeles en float32, guarda un checkpoint por bloque y retoma si se cae.
Solo lee los datos de entrada; no los modifica.

Piloto (pocos píxeles, carpeta aparte):
    python -X utf8 correlacion_amenazas_rendimiento.py --piloto 200
Corrida completa:
    python -X utf8 correlacion_amenazas_rendimiento.py
Retomar una corrida caída: repetir el mismo comando con --run-id <id que aparece en el log>.
"""
import argparse
import hashlib
import json
import logging
import shutil
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd
from scipy import stats

PHASES = ['EST', 'VEG', 'REP', 'FLO', 'FIL', 'MAT']
YEARS = np.arange(1981, 2017)
ROOT = Path('C:/Users/paola/Tesis')
REPO = Path(__file__).resolve().parents[3]
SOURCE = ROOT / '03_Resultados/Agroclima/vigente/ejecuciones/maize_seis_fases_GEE_1981_2016/resumen_GDHY_anual.csv'
SOURCE_SHA = '0ebff649cc5d30a48bef486822b40110bdae0101f71e52cbda42463e2b4c5986'  # auditado el 8 oct
COORDS = ROOT / '02_Procesados/Pixeles_correlacion_vigentes/pixeles_maize.csv'
YIELD = ROOT / '02_Procesados/GDHY_detrend/maize_yield_1981_2016_DETREND_clean.nc'
AUDIT = REPO / 'outputs/agroclima_vigente/auditoria_rendimiento/maize/auditoria_por_pixel.csv'
OUT_BASE = ROOT / '03_Resultados/Agroclima/vigente/correlaciones_rendimiento/maize'
REPO_OUT = REPO / 'outputs/agroclima_vigente/correlaciones_rendimiento/maize'
SEED = 20261023
log = logging.getLogger('corr')


def peak_mb():
    try:
        import psutil
        info = psutil.Process().memory_info()
        return round(getattr(info, 'peak_wset', info.rss) / 2**20, 1)
    except Exception:
        return None


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for part in iter(lambda: f.read(1 << 20), b''):
            h.update(part)
    return h.hexdigest()


# ---------------------------------------------------------------- insumos
def load_inputs(run, coords, alignment):
    """Conteos (P,36,6) y rendimiento alineado (P,36) en float32; se cachean (compartido entre
    piloto y corrida completa, ligado al hash auditado del CSV)."""
    (OUT_BASE / '_cache').mkdir(parents=True, exist_ok=True)
    cache = OUT_BASE / '_cache' / f'insumos_{alignment}_{SOURCE_SHA[:12]}.npz'
    if cache.exists():
        z = np.load(cache)
        log.info('Insumos leídos del checkpoint %s', cache.name)
        return z['counts'], z['yield_'], z['yield_year']
    log.info('Verificando hash del CSV de amenazas (357 MB)...')
    if sha256(SOURCE) != SOURCE_SHA:
        raise ValueError('El CSV de amenazas no coincide con la versión auditada; no se calcula.')
    pmap = dict(zip(coords.pixel_id, range(len(coords))))
    P = len(coords)
    counts = np.full((P, 36, 6), np.nan, np.float32)
    seen = np.zeros((P, 36, 6), bool)
    mat_end = np.full((P, 36), -1, np.int32)
    cols = ['pixel_id', 'season_year', 'phase', 'quality', 'mean_count_per_native_cell', 'end']
    for k, d in enumerate(pd.read_csv(SOURCE, usecols=cols, chunksize=200_000)):
        d = d[d.pixel_id.isin(pmap) & d.season_year.between(1981, 2016)]
        if d.empty:
            continue
        i = d.pixel_id.map(pmap).to_numpy()
        j = d.season_year.to_numpy() - 1981
        f = d.phase.map({p: n for n, p in enumerate(PHASES)}).to_numpy()
        if seen[i, j, f].any():
            raise ValueError('Registros píxel-año-fase duplicados')
        seen[i, j, f] = True
        v = d.mean_count_per_native_cell.to_numpy(float)
        ok = d.quality.eq('OK').to_numpy() & np.isfinite(v)
        counts[i, j, f] = np.where(ok, v, np.nan)   # dato incompleto no es cero
        m = f == 5
        mat_end[i[m], j[m]] = pd.to_datetime(d.end.to_numpy()[m]).year  # 'end' es inclusivo
        if k % 3 == 0:
            log.info('Lectura CSV: bloque %d (%s filas útiles acumuladas)', k, f'{int(seen.sum()):,}')
    if not seen.all():
        raise ValueError('Faltan combinaciones píxel-año-fase en el CSV; no se publica resultado')

    with h5py.File(YIELD, 'r') as h:
        v = h['var']
        if v.shape != (360, 720, 36):
            raise ValueError(f'Dimensiones inesperadas del detrendido: {v.shape}')
        lat = h['lat'][:]
        lon = (h['lon'][:] + 180) % 360 - 180
        li, lj = coords.lat_idx.to_numpy(), coords.lon_idx.to_numpy()
        if not (np.allclose(lat[li], coords.latitude) and np.allclose(lon[lj], coords.longitude)):
            raise ValueError('Coordenadas del CSV de píxeles y del NetCDF no coinciden')
        ylab = (np.datetime64('1981-01-01') + h['time'][:].astype('timedelta64[D]')).astype('datetime64[Y]').astype(int) + 1970
        y_by_label = v[:][li, lj, :].astype(np.float32)
    if not np.array_equal(ylab, YEARS):
        raise ValueError('Años del rendimiento distintos de 1981–2016')

    if alignment == 'same-label':
        yield_year = np.tile(YEARS, (P, 1))
    else:  # maturity-year: año en que termina MAT ≈ año de cosecha
        yield_year = mat_end
    idx = yield_year - 1981
    inside = (idx >= 0) & (idx < 36)
    yld = np.full((P, 36), np.nan, np.float32)
    rows = np.repeat(np.arange(P)[:, None], 36, 1)
    yld[inside] = y_by_label[rows[inside], idx[inside]]
    np.savez(cache, counts=counts, yield_=yld, yield_year=yield_year)
    log.info('Insumos guardados en %s', cache.name)
    return counts, yld, yield_year


# ---------------------------------------------------------------- estadística
def pearson_masked(x, y, valid):
    """r de Pearson por fila usando solo pares válidos. x, y: (..., 36)."""
    n = valid.sum(-1)
    xv = np.where(valid, x, 0.0)
    yv = np.where(valid, y, 0.0)
    with np.errstate(invalid='ignore', divide='ignore'):
        mx = xv.sum(-1) / n
        my = yv.sum(-1) / n
        dx = np.where(valid, x - mx[..., None], 0.0)
        dy = np.where(valid, y - my[..., None], 0.0)
        r = (dx * dy).sum(-1) / np.sqrt((dx * dx).sum(-1) * (dy * dy).sum(-1))
    return r, n, dx, dy


def ranks_masked(a, valid):
    """Rangos promedio (empates) dentro de los pares válidos de cada fila."""
    out = np.full(a.shape, np.nan)
    flat_a = a.reshape(-1, a.shape[-1])
    flat_v = valid.reshape(-1, a.shape[-1])
    flat_o = out.reshape(-1, a.shape[-1])
    for k in range(flat_a.shape[0]):
        m = flat_v[k]
        if m.sum() >= 3:
            flat_o[k, m] = stats.rankdata(flat_a[k, m])
    return out


def p_from_r(r, n):
    with np.errstate(invalid='ignore', divide='ignore'):
        t = r * np.sqrt((n - 2) / (1 - r * r))
    return 2 * stats.t.sf(np.abs(t), n - 2)


def r_critical(n, alpha=0.05):
    tc = stats.t.isf(alpha / 2, n - 2)
    return tc / np.sqrt(n - 2 + tc * tc)


def permutation_p(dx, dy, valid, r_obs, n_perm, batch, rng):
    """p de permutación (dos colas) por fila: baraja el rendimiento solo entre pares válidos."""
    R, T = dx.shape
    order = np.argsort(~valid, axis=1, kind='stable')          # válidos primero
    xc = np.take_along_axis(dx, order, 1).astype(np.float32)
    yc = np.take_along_axis(dy, order, 1).astype(np.float32)
    vc = np.take_along_axis(valid, order, 1)
    denom = np.sqrt((xc * xc).sum(1) * (yc * yc).sum(1)).astype(np.float32)
    exceed = np.zeros(R, np.int32)
    absr = np.abs(r_obs).astype(np.float32) - 1e-6
    done = 0
    while done < n_perm:
        b = min(batch, n_perm - done)
        keys = rng.random((b, R, T), dtype=np.float32)
        keys[:, ~vc] = np.inf                                   # inválidos al final
        perm = np.argsort(keys, axis=2)
        yp = np.take_along_axis(np.broadcast_to(yc, (b, R, T)), perm, 2)
        rp = (xc[None] * yp).sum(2) / denom[None]
        exceed += (np.abs(rp) >= absr[None]).sum(0, dtype=np.int32)
        done += b
    return (exceed + 1) / (n_perm + 1)


def bh(p, q=0.05):
    """Benjamini–Hochberg sobre los p finitos. Devuelve q-valores ajustados y bandera."""
    p = np.asarray(p, float)
    qv = np.full(p.shape, np.nan)
    ok = np.isfinite(p)
    m = ok.sum()
    if m:
        ps = p[ok]
        o = np.argsort(ps)
        adj = ps[o] * m / np.arange(1, m + 1)
        adj = np.minimum.accumulate(adj[::-1])[::-1].clip(max=1)
        tmp = np.empty(m)
        tmp[o] = adj
        qv[ok] = tmp
    return qv, qv <= q


# ---------------------------------------------------------------- bloques
def run_block(b, sl, counts, yld, args, run, coords):
    path = run / 'bloques' / f'bloque_{b:04d}.npz'
    if path.exists():
        return
    t0 = time.perf_counter()
    x = counts[sl].transpose(0, 2, 1).astype(np.float64)          # (B,6,36)
    y = np.broadcast_to(yld[sl][:, None, :], x.shape).astype(np.float64)
    valid = np.isfinite(x) & np.isfinite(y)
    r, n, dx, dy = pearson_masked(x, y, valid)
    n_event = ((x > 0) & valid).sum(-1)
    constant = np.nanstd(np.where(valid, x, np.nan), axis=-1) < 1e-9
    rx, ry = ranks_masked(x, valid), ranks_masked(y, valid)
    rho, _, _, _ = pearson_masked(rx, ry, valid)
    status = np.where(n < args.min_years, 1, np.where(constant, 2, np.where(n_event < args.min_event_years, 3, 0)))
    testable = status == 0
    p_t = np.where(testable, p_from_r(r, n), np.nan)
    p_rho = np.where(testable, p_from_r(rho, n), np.nan)
    p_perm = np.full(r.shape, np.nan)
    if args.n_perm and testable.any():
        rng = np.random.default_rng([SEED, b])
        flat = testable.ravel()
        p_perm.ravel()[flat] = permutation_p(dx.reshape(-1, 36)[flat], dy.reshape(-1, 36)[flat],
                                             valid.reshape(-1, 36)[flat], r.ravel()[flat],
                                             args.n_perm, args.perm_batch, rng)
    tmp = path.with_suffix('.tmp.npz')
    np.savez(tmp, r=r.astype(np.float32), rho=rho.astype(np.float32), n=n.astype(np.int16),
             n_event=n_event.astype(np.int16), mean_count=np.nanmean(np.where(valid, x, np.nan), -1).astype(np.float32),
             p_t=p_t, p_rho=p_rho, p_perm=p_perm, status=status.astype(np.int8))
    tmp.replace(path)                                             # escritura atómica
    log.info('Bloque %d listo (%d píxeles) en %.1f s', b, sl.stop - sl.start, time.perf_counter() - t0)


def field_significance(counts, yld, args, run, alpha=0.05):
    """Permuta los años del rendimiento con la MISMA permutación en todos los píxeles (conserva la
    correlación espacial) y cuenta la fracción de pruebas con p<alpha. Checkpoint por lotes."""
    x = counts.transpose(0, 2, 1).astype(np.float32)               # (P,6,36)
    y = yld.astype(np.float32)
    valid0 = np.isfinite(x) & np.isfinite(y)[:, None, :]
    n0 = valid0.sum(-1)
    n_event = ((x > 0) & valid0).sum(-1)
    const = np.nanstd(np.where(valid0, x, np.nan), -1) < 1e-9
    testable = (n0 >= args.min_years) & ~const & (n_event >= args.min_event_years)

    def frac_sig(yy):
        valid = np.isfinite(x) & np.isfinite(yy)[:, None, :]
        r, n, _, _ = pearson_masked(x, np.broadcast_to(yy[:, None, :], x.shape), valid)
        ok = testable & (n >= args.min_years)
        rc = r_critical(np.maximum(n, 3), alpha)
        sig = ok & (np.abs(r) >= rc)
        neg = ok & (r <= -rc)
        tot = ok.sum(0).clip(min=1)
        return np.r_[sig.sum(0) / tot, sig.sum() / ok.sum(), neg.sum(0) / tot, neg.sum() / ok.sum()]

    obs = frac_sig(y)
    fdir = run / 'campo'
    fdir.mkdir(exist_ok=True)
    rng = np.random.default_rng([SEED, 999])
    perms = [rng.permutation(36) for _ in range(args.n_field)]
    nb = int(np.ceil(args.n_field / 100))
    for k in range(nb):
        path = fdir / f'campo_{k:03d}.npy'
        if path.exists():
            continue
        t0 = time.perf_counter()
        res = np.stack([frac_sig(y[:, pm]) for pm in perms[k * 100:(k + 1) * 100]])
        np.save(path, res)
        log.info('Campo: lote %d/%d (%.1f s)', k + 1, nb, time.perf_counter() - t0)
    null = np.concatenate([np.load(fdir / f'campo_{k:03d}.npy') for k in range(nb)])
    labels = [f'sig_{p}' for p in PHASES] + ['sig_TODAS'] + [f'neg_{p}' for p in PHASES] + ['neg_TODAS']
    p_field = (1 + (null >= obs[None] - 1e-12).sum(0)) / (1 + len(null))
    return pd.DataFrame({'estadistico': labels, 'fraccion_observada': obs,
                         'nulo_media': null.mean(0), 'nulo_p95': np.quantile(null, .95, 0),
                         'p_campo': p_field, 'n_permutaciones': len(null)})


# ---------------------------------------------------------------- figuras
def maps(df, out, alignment):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(3, 2, figsize=(16, 13), constrained_layout=True)
    for ax, ph in zip(axes.ravel(), PHASES):
        d = df[df.phase == ph]
        t = d[d.estado == 'OK']
        ax.scatter(d.longitude, d.latitude, s=1, c='#dddddd', lw=0)
        sc = ax.scatter(t.longitude, t.latitude, s=2, c=t.r_pearson, cmap='RdBu', vmin=-.7, vmax=.7, lw=0)
        s = t[t.sig_bh_global]
        ax.scatter(s.longitude, s.latitude, s=9, facecolors='none', edgecolors='k', lw=.4)
        ax.set_title(f'{ph}: {len(t):,} pruebas · {int(t.sig_bh_global.sum()):,} significativas BH (q≤0,05)')
        ax.set_xlim(-180, 180); ax.set_ylim(-60, 75); ax.set_aspect('equal'); ax.grid(alpha=.2)
    fig.colorbar(sc, ax=axes, shrink=.6, label='r de Pearson (conteo de la fase vs rendimiento detrendido)')
    fig.suptitle(f'Maíz secano 1981–2016 · amenazas por fase vs rendimiento GDHY detrendido · año: {alignment}\n'
                 'Gris: sin prueba (n<20, fase constante o <3 años con evento). Círculo negro: FDR BH global. '
                 'Asociación, no pérdida causal.', fontsize=12)
    for ext in ('png', 'pdf'):
        fig.savefig(out / f'mapas_r_seis_fases.{ext}', dpi=170, facecolor='white')
    plt.close(fig)


# ---------------------------------------------------------------- principal
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--alineacion', choices=['maturity-year', 'same-label'], default='maturity-year')
    ap.add_argument('--piloto', type=int, default=0, help='N píxeles (muestra aleatoria fija) en carpeta aparte')
    ap.add_argument('--bloque', type=int, default=500, help='píxeles por bloque/checkpoint')
    ap.add_argument('--n-perm', type=int, default=2000, help='permutaciones por prueba (0 = omitir)')
    ap.add_argument('--perm-batch', type=int, default=100, help='permutaciones simultáneas (memoria)')
    ap.add_argument('--n-field', type=int, default=1000, help='permutaciones conjuntas para significancia de campo')
    ap.add_argument('--min-years', type=int, default=20)
    ap.add_argument('--min-event-years', type=int, default=3)
    ap.add_argument('--q', type=float, default=0.05)
    ap.add_argument('--run-id', help='retomar una corrida existente')
    ap.add_argument('--etiqueta', default='', help='prefijo del run_id (p. ej. tiempo)')
    ap.add_argument('--no-copiar', action='store_true', help='no copiar resultados al repo')
    args = ap.parse_args()

    tag = (f'{args.etiqueta}_' if args.etiqueta else '') + (f'piloto{args.piloto}_' if args.piloto else '')
    run_id = args.run_id or f'{tag}{args.alineacion}_{time.strftime("%Y%m%d_%H%M%S")}'
    run = OUT_BASE / run_id
    (run / 'bloques').mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S',
                        handlers=[logging.FileHandler(run / 'progreso.log', encoding='utf-8'),
                                  logging.StreamHandler(sys.stdout)])
    params = vars(args) | {'run_id': run_id, 'seed': SEED}
    pfile = run / 'parametros.json'
    if pfile.exists() and args.run_id:
        old = json.loads(pfile.read_text(encoding='utf-8'))
        diff = {k: (old.get(k), v) for k, v in params.items() if k != 'run_id' and old.get(k) != v}
        if diff:
            raise SystemExit(f'Parámetros distintos a los de la corrida que se quiere retomar: {diff}')
    pfile.write_text(json.dumps(params, indent=2), encoding='utf-8')
    log.info('Corrida %s | carpeta %s', run_id, run)
    t0 = time.perf_counter()

    coords = pd.read_csv(COORDS, encoding='utf-8-sig').sort_values('h5_index').reset_index(drop=True)
    counts, yld, yield_year = load_inputs(run, coords, args.alineacion)
    if args.piloto:
        pick = np.sort(np.random.default_rng(SEED).choice(len(coords), args.piloto, replace=False))
        coords, counts, yld, yield_year = coords.iloc[pick].reset_index(drop=True), counts[pick], yld[pick], yield_year[pick]
    P = len(coords)
    blocks = [slice(s, min(s + args.bloque, P)) for s in range(0, P, args.bloque)]
    log.info('%s píxeles · %d bloques de hasta %d · %d permutaciones por prueba', f'{P:,}', len(blocks), args.bloque, args.n_perm)
    t_bloques = time.perf_counter()
    for b, sl in enumerate(blocks):
        run_block(b, sl, counts, yld, args, run, coords)
        eta = (time.perf_counter() - t0) / (b + 1) * (len(blocks) - b - 1)
        log.info('Avance %d/%d bloques · restante estimado %.1f min', b + 1, len(blocks), eta / 60)

    t_bloques = time.perf_counter() - t_bloques
    parts = [np.load(run / 'bloques' / f'bloque_{b:04d}.npz') for b in range(len(blocks))]
    cat = {k: np.concatenate([p[k] for p in parts]) for k in parts[0].files}
    names = {0: 'OK', 1: 'MENOS_DE_MIN_ANIOS', 2: 'FASE_CONSTANTE', 3: 'POCOS_ANIOS_CON_EVENTO'}
    df = pd.DataFrame({
        'pixel_id': np.repeat(coords.pixel_id.to_numpy(), 6),
        'latitude': np.repeat(coords.latitude.to_numpy(), 6),
        'longitude': np.repeat(coords.longitude.to_numpy(), 6),
        'phase': np.tile(PHASES, P),
        'n': cat['n'].ravel(), 'anios_con_evento': cat['n_event'].ravel(),
        'conteo_medio': cat['mean_count'].ravel().round(4),
        'r_pearson': cat['r'].ravel().round(4), 'p_t': cat['p_t'].ravel(), 'p_perm': cat['p_perm'].ravel(),
        'rho_spearman': cat['rho'].ravel().round(4), 'p_spearman': cat['p_rho'].ravel(),
        'estado': pd.Series(cat['status'].ravel()).map(names).to_numpy(),
    })
    df['r_critico_05'] = np.where(df.n >= 3, r_critical(df.n.clip(lower=3)), np.nan).round(4)
    df['q_bh_global'], df['sig_bh_global'] = bh(df.p_t, args.q)
    df['q_bh_fase'] = np.nan
    df['sig_bh_fase'] = False
    for ph in PHASES:
        m = df.phase == ph
        qv, sg = bh(df.loc[m, 'p_t'], args.q)
        df.loc[m, 'q_bh_fase'] = qv
        df.loc[m, 'sig_bh_fase'] = sg
    # Wilks (2016): FDR con alpha_FDR = 2·alpha_global controla significancia de campo con correlación espacial
    df['q_bh_wilks'], df['sig_campo_wilks'] = bh(df.p_t, 2 * args.q)
    # Spearman: alternativa robusta para conteos con muchos ceros (mismas pruebas, mismo q)
    df['q_bh_spearman'], df['sig_bh_spearman'] = bh(df.p_spearman, args.q)
    if AUDIT.exists():
        aud = pd.read_csv(AUDIT, usecols=['pixel_id', 'clase', 'raw_max_t_ha'])
        df = df.merge(aud.rename(columns={'clase': 'clase_auditoria_rendimiento'}), on='pixel_id', how='left')

    out = run / 'resultados'
    out.mkdir(exist_ok=True)
    df.to_csv(out / 'correlaciones_pixel_fase.csv.gz', index=False, float_format='%.6g')

    t = df[df.estado == 'OK']
    resumen = t.groupby('phase', sort=False).agg(
        pruebas=('r_pearson', 'size'), r_mediana=('r_pearson', 'median'),
        pct_r_negativo=('r_pearson', lambda s: 100 * (s < 0).mean()),
        pct_p_menor_05=('p_t', lambda s: 100 * (s < .05).mean()),
        pct_p_perm_menor_05=('p_perm', lambda s: 100 * (s < .05).mean()),
        sig_bh_global=('sig_bh_global', 'sum'), sig_bh_fase=('sig_bh_fase', 'sum'),
        sig_bh_spearman=('sig_bh_spearman', 'sum'), rho_mediana=('rho_spearman', 'median'),
        sig_bh_global_negativas=('r_pearson', lambda s: int(((s < 0) & t.loc[s.index, 'sig_bh_global']).sum())),
        n_mediano=('n', 'median'), r_critico_n_mediano=('r_critico_05', 'median')).reindex(PHASES)
    estado = df.pivot_table(index='phase', columns='estado', values='pixel_id', aggfunc='size', fill_value=0).reindex(PHASES)
    resumen = resumen.join(estado)
    t_campo = time.perf_counter()
    if args.n_field:
        log.info('Significancia de campo: %d permutaciones conjuntas...', args.n_field)
        campo = field_significance(counts, yld, args, run)
    else:
        campo = pd.DataFrame(columns=['estadistico', 'fraccion_observada', 'nulo_media', 'nulo_p95', 'p_campo', 'n_permutaciones'])
    t_campo = time.perf_counter() - t_campo
    resumen.round(4).to_csv(out / 'resumen_por_fase.csv')
    campo.round(5).to_csv(out / 'significancia_campo.csv', index=False)
    ns = np.arange(20, 37)
    pd.DataFrame({'n': ns, 'r_critico_05': r_critical(ns).round(4), 'r_critico_01': r_critical(ns, .01).round(4)}
                 ).to_csv(out / 'umbral_r_por_n.csv', index=False)
    # autocorrelación lag-1 del rendimiento detrendido (supuesto de independencia anual)
    a, b2 = yld[:, :-1], yld[:, 1:]
    ok = np.isfinite(a) & np.isfinite(b2)
    ac, _, _, _ = pearson_masked(a.astype(float), b2.astype(float), ok)
    maps(df, out, args.alineacion)

    manifest = {
        'run_id': run_id, 'alineacion': args.alineacion, 'pixeles': int(P), 'parametros': params,
        'fuentes': {'amenazas_csv': str(SOURCE), 'amenazas_sha256': SOURCE_SHA,
                    'rendimiento_nc': str(YIELD), 'rendimiento_sha256': sha256(YIELD),
                    'pixeles_csv': str(COORDS), 'codigo_sha256': sha256(Path(__file__))},
        'unidades': 'Rendimiento: t/ha detrendido (anomalía respecto a tendencia lineal 1981–2016 por píxel). '
                    'EST–FIL: episodios de Tmax ≥ umbral con racha ≥2 días (media de celdas nativas). MAT: días con P>10 mm.',
        'autocorrelacion_lag1_rendimiento_mediana': float(np.nanmedian(ac)),
        'pruebas_validas': int(len(t)), 'sig_bh_global_total': int(t.sig_bh_global.sum()),
        'sig_campo_wilks_total': int(t.sig_campo_wilks.sum()),
        'segundos': round(time.perf_counter() - t0, 1),
        'segundos_bloques': round(t_bloques, 1), 'segundos_campo': round(t_campo, 1),
        'memoria_pico_mb': peak_mb(),
        'equipo': 'Intel Core Ultra 7 155U, 15,3 GB RAM, sin GPU (portátil)',
        'limitaciones': [
            'Correlación marginal por fase: las fases comparten calor y no se separan aquí (ver OLS previo).',
            'Detrend lineal con los 36 años: no afecta la correlación (no hay predicción fuera de muestra).',
            'GDHY sin enmascarar: hay píxel-año >15 t/ha; ver clase_auditoria_rendimiento para sensibilidad.',
            'Año de madurez aproxima el año de cosecha; GDHY no documenta explícitamente su convención.',
            'p_t asume rendimiento ~normal e independencia entre años; p_perm no asume normalidad.'],
    }
    (out / 'manifiesto.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    (run / 'COMPLETADO').write_text(time.strftime('%Y-%m-%d %H:%M:%S'), encoding='utf-8')
    if not args.piloto and not args.no_copiar:
        dest = REPO_OUT / run_id
        shutil.copytree(out, dest, dirs_exist_ok=True)
        log.info('Resultados copiados al repo: %s', dest)
    log.info('TERMINADO en %.1f min. Resumen:\n%s\n%s', (time.perf_counter() - t0) / 60,
             resumen.round(3).to_string(), campo.round(4).to_string(index=False))


if __name__ == '__main__':
    main()
