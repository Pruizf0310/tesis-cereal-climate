"""Build the auditable 1981-2016 rice hazard pilot for one H5 pixel."""
import argparse, csv, json, math, time, urllib.error, urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq

DEFAULT_MASTER=Path(r"C:\Users\paola\Tesis\03_Resultados\Fenologia\tabla_maestra_fenologia_amenazas_espacial_v2_csv.csv")
DEFAULT_OUT=Path(r"C:\Users\paola\Tesis\03_Resultados\Hazard")
DEFAULT_REPO=Path(r"C:\Users\paola\Documents\Codex\2026-08-16\eje\work\tesis-cereal-climate")
API="https://tesis-cereal-climate-egcl.vercel.app/api/calculate-phase-risk"
DATASET="ECMWF/ERA5_LAND/DAILY_AGGR"
BANDS={"tmax_c":"temperature_2m_max","tmean_c":"temperature_2m","tmin_c":"temperature_2m_min","precip_mm":"total_precipitation_sum","rootzone_sm":"volumetric_soil_water_layer_1/2/3"}
UNITS={"tmax_c":"degC","tmean_c":"degC","tmin_c":"degC","precip_mm":"mm/day","rootzone_sm":"m3/m3"}

def fnum(v):
    try:return float(v)
    except:return None
def in_year(doy, year): return date(year,1,1)+timedelta(days=int(doy)-1)
def critical(v,t,op):
    if v is None:return False
    return {">":v>t,">=":v>=t,"<":v<t,"<=":v<=t}[op]
def exceed(v,t,op): return (v-t) if op in (">",">=") else (t-v)

def api_post(payload, cache_path):
    if cache_path.exists(): return json.loads(cache_path.read_text(encoding="utf-8"))
    req=urllib.request.Request(API,data=json.dumps(payload).encode(),headers={"content-type":"application/json","user-agent":"rice-hazard-builder/1.0"},method="POST")
    err=None
    for wait in (0,2,5):
        if wait: time.sleep(wait)
        try:
            with urllib.request.urlopen(req,timeout=300) as r: body=json.loads(r.read().decode())
            cache_path.write_text(json.dumps(body,ensure_ascii=False,indent=2),encoding="utf-8")
            return body
        except Exception as e: err=e
    raise RuntimeError(f"API failed after retries: {err}")

def events(flags, dates, values, threshold, op, min_days):
    out=[]; start=None
    for i,flag in enumerate(flags+[False]):
        if flag and start is None:start=i
        if not flag and start is not None:
            idx=list(range(start,i)); dur=len(idx); vals=[values[j] for j in idx]
            out.append((idx,dur,dates[start],dates[i-1],max(vals),sum(vals)/dur,max(exceed(v,threshold,op) for v in vals),dur>=min_days))
            start=None
    return out

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--pixel-id",default="rice_0"); ap.add_argument("--start-year",type=int,default=1981); ap.add_argument("--end-year",type=int,default=2016); ap.add_argument("--master-table-path",type=Path,default=DEFAULT_MASTER); ap.add_argument("--output-dir",type=Path,default=DEFAULT_OUT); ap.add_argument("--repo-path",type=Path,default=DEFAULT_REPO); a=ap.parse_args()
    out=a.output_dir; pilot=out/"pilot"/a.pixel_id; cache=pilot/"cache"; val=out/"validation"; cache.mkdir(parents=True,exist_ok=True); val.mkdir(parents=True,exist_ok=True)
    cross=list(csv.DictReader((out/"rice_pixel_crosswalk.csv").open(encoding="utf-8-sig"))); px=next(x for x in cross if x["pixel_id"]==a.pixel_id)
    source=[]
    with a.master_table_path.open(encoding="utf-8-sig",newline="") as f:
        for r in csv.DictReader(f):
            if r["coordinate_id"]==a.pixel_id and r["crop"]=="rice": source.append(r)
    th=json.loads((a.repo_path/"web-v2/public/data/calculator_thresholds_v2.json").read_text(encoding="utf-8"))["crops"]["rice"]
    rules={(phase,r["rule_id"]):r for phase,rs in th.items() for r in rs}
    master=[]; daily=[]; event_rows=[]; warnings=[]; query_count=0
    for src in source:
        phase=src["phase_code"]; rid=src["threat_rule_id"]; rule=rules.get((phase,rid)); season_id=f'{src["season"]}__{src["water_system"]}'
        calculable=bool(rule and rule.get("calculation_status")=="provisional" and rule.get("variable"))
        annual_by_year={}; start_offset=int(src["start_year_offset"])
        if calculable:
            query_start=a.start_year+start_offset; query_end=min(a.end_year+start_offset,2016)
            if query_start<=query_end:
                payload={"lat":float(px["gee_query_lat"]),"lon":float(px["gee_query_lon"]),"crop":"rice","phase":phase,"season_id":season_id,"rule_id":rid,"variable":rule["variable"],"threshold":rule["threshold"],"operator":rule["operator"],"aggregation":rule["aggregation"],"window_days":rule["window_days"],"min_days_event":rule["min_days_event"],"start_year":query_start,"end_year":query_end}
                cache_name=(f"{season_id}__{phase}__{rid}__{query_start}_{query_end}.json" if start_offset==0 else f"offset{start_offset}__{season_id}__{phase}__{rid}__{query_start}_{query_end}.json")
                body=api_post(payload,cache/cache_name); query_count+=1
                if not body.get("ok"):
                    warnings.append(f"{season_id}/{phase}/{rid}: {body.get('message')}")
                else: annual_by_year={int(x["year"])-start_offset:x for x in body["result"]["annual"]}
        for year in range(a.start_year,a.end_year+1):
            start_year=year+int(src["start_year_offset"]); end_year=year+int(src["end_year_offset"])
            pstart=in_year(src["phase_start_doy"],start_year); pend=in_year(src["phase_end_doy"],end_year); phase_days=(pend-pstart).days+1
            base={"pixel_id":a.pixel_id,"rice_h5_pixel_index":int(px["rice_h5_pixel_index"]),"lat":float(px["h5_lat"]),"lon":float(px["h5_lon"]),"season_year":year,"season_id":season_id,"phase":phase,"hazard":src["hazard"],"hazard_code":rid,"climate_variable":rule.get("variable") if rule else src["variable"],"threshold_value":fnum(src["threshold"]),"threshold_operator":src["operator"],"phase_start_date":pstart.isoformat(),"phase_end_date":pend.isoformat(),"phase_days_total":phase_days,"threshold_source":src["source"],"master_record_id":src["record_id"]}
            ann=annual_by_year.get(year)
            if not ann:
                master.append(base|{"hazard_occurred":None,"critical_days":None,"critical_day_fraction":None,"event_count":None,"longest_event_days":None,"severity":None,"severity_unit":None,"first_critical_date":None,"last_critical_date":None,"valid_days":0,"missing_days":phase_days,"coverage_fraction":0.0,"quality_flag":"NO_GEE_DATA"}); continue
            ds=ann["daily_values"]; dates=[x["date"] for x in ds]; vals=[x.get("value") for x in ds]; threshold=float(rule["threshold"]); op=rule["operator"]; flags=[critical(v,threshold,op) for v in vals]
            ev=events(flags,dates,vals,threshold,op,int(rule["min_days_event"])); qualifying=[e for e in ev if e[7]]; crit=sum(flags); valid=sum(v is not None for v in vals); missing=max(phase_days-valid,0); coverage=valid/phase_days if phase_days else 0
            critical_vals=[v for v,flag in zip(vals,flags) if flag]; severity=(sum(exceed(v,threshold,op) for v in critical_vals)/len(critical_vals)) if critical_vals else 0.0
            for i,(d,v,flag) in enumerate(zip(dates,vals,flags)):
                eid=None
                for n,e in enumerate(ev,1):
                    if i in e[0]:eid=f"{a.pixel_id}_{season_id}_{year}_{phase}_{rid}_E{n:02d}"
                daily.append(base|{"date":d,"observed_value":v,"observed_unit":UNITS.get(rule["variable"]),"is_critical_day":flag,"event_id":eid,"gee_dataset":DATASET,"gee_band":BANDS.get(rule["variable"]),"quality_flag":"OK" if v is not None else "NO_GEE_DATA"})
            for n,e in enumerate(ev,1):
                event_rows.append(base|{"event_id":f"{a.pixel_id}_{season_id}_{year}_{phase}_{rid}_E{n:02d}","event_start_date":e[2],"event_end_date":e[3],"event_duration_days":e[1],"event_peak_value":e[4],"event_mean_value":e[5],"event_max_exceedance":e[6],"qualifies_as_hazard":e[7]})
            q="OK" if coverage>=0.8 else "INSUFFICIENT_CLIMATE_DATA"
            master.append(base|{"hazard_occurred":bool(qualifying),"critical_days":crit,"critical_day_fraction":crit/phase_days,"event_count":len(qualifying),"longest_event_days":max((e[1] for e in qualifying),default=0),"severity":severity,"severity_unit":UNITS.get(rule["variable"]),"first_critical_date":next((d for d,f in zip(dates,flags) if f),None),"last_critical_date":next((d for d,f in reversed(list(zip(dates,flags))) if f),None),"valid_days":valid,"missing_days":missing,"coverage_fraction":coverage,"quality_flag":q})
    def write(name,rows):
        csvp=pilot/f"{name}.csv"; pqp=pilot/f"{name}.parquet"
        if rows:
            with csvp.open("w",encoding="utf-8-sig",newline="") as f: w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
            pq.write_table(pa.Table.from_pylist(rows),pqp,compression="zstd")
        return str(csvp),str(pqp)
    paths={"master":write("rice_hazard_history_master_pilot",master),"daily":write("rice_hazard_daily_pilot",daily),"events":write("rice_hazard_events_pilot",event_rows)}
    # Strict invariants and a compact sample spanning the full period.
    errs=[]
    for r in master:
        if r["quality_flag"]=="OK":
            if not (r["phase_days_total"]>0 and r["critical_days"]<=r["phase_days_total"] and r["longest_event_days"]<=r["critical_days"] and 0<=r["coverage_fraction"]<=1): errs.append(r)
    daily_groups={}
    for r in daily:
        k=(r["season_id"],r["season_year"],r["phase"],r["hazard_code"]); daily_groups.setdefault(k,[]).append(r)
    outside_dates=sum(not (r["phase_start_date"]<=r["date"]<=r["phase_end_date"]) for r in daily)
    reconciliation_errors=0
    for r in master:
        if r["quality_flag"]=="OK":
            q=daily_groups.get((r["season_id"],r["season_year"],r["phase"],r["hazard_code"]),[])
            if sum(bool(x["is_critical_day"]) for x in q)!=r["critical_days"] or len(q)!=r["valid_days"]: reconciliation_errors+=1
    sample=[r for r in master if r["hazard_code"]=="RICE_HEAT_DAY37_2" and r["season_id"]=="rice_1__ir" and r["season_year"] in (1981,1985,1990,1995,2000,2005,2010,2016)]
    write("rice_hazard_history_sample",sample)
    report={"status":"PASS" if not errs and not outside_dates and not reconciliation_errors and daily else "FAIL","pixel_id":a.pixel_id,"period":[a.start_year,a.end_year],"source_master_rows":len(source),"rows_master":len(master),"rows_daily":len(daily),"rows_events":len(event_rows),"api_queries":query_count,"quality_counts":{},"invariant_errors":len(errs),"dates_outside_master_phase":outside_dates,"daily_master_reconciliation_errors":reconciliation_errors,"duplicate_master_keys":len(master)-len({(r['season_id'],r['season_year'],r['phase'],r['hazard_code']) for r in master}),"duplicate_daily_keys":len(daily)-len({(r['season_id'],r['season_year'],r['phase'],r['hazard_code'],r['date']) for r in daily}),"warnings":warnings,"outputs":paths,"severity_definition":"Mean physical threshold exceedance over critical days; 0 when valid data contain no critical days; null when climate data are unavailable.","period_note":"For phases with start_year_offset=1, season_year 2016 requires 2017 climate data. The deployed API restricts requests to 2016, so these rows remain NO_GEE_DATA rather than being shifted."}
    for r in master: report["quality_counts"][r["quality_flag"]]=report["quality_counts"].get(r["quality_flag"],0)+1
    (val/"pilot_rice_0_validation_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"rice_hazard_checkpoint.json").write_text(json.dumps({"updated_at":datetime.now(timezone.utc).isoformat(),"completed_pilots":[a.pixel_id],"period":[a.start_year,a.end_year]},indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__": main()
