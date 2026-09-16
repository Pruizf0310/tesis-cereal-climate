import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const rows=JSON.parse(fs.readFileSync(path.join(root,'web-v2/public/data/hazard_impact_harmonized_v3.json'),'utf8')).rows;
const daily='ECMWF/ERA5_LAND/DAILY_AGGR', hourly='ECMWF/ERA5_LAND/HOURLY';
const blocked={
 MAIZE_EMERGENCE_COLD6:'Resolve soil chilling versus 2 m air temperature in the reviewed evidence before selecting an ERA5 band.',
 MAIZE_EARLYVEG_DROUGHT_SWP051_4D:'Soil water potential requires a soil retention curve; volumetric water content is not an interchangeable measurement.',
 MAIZE_TASSEL_HEAT38_30_15D:'Paired experimental day/night temperatures require an explicit local day/night exposure definition.',
 MAIZE_HEAT_DAY37_9:'Daytime metric and consecutive exposure duration are not specified.',
 MAIZE_HEAT_NIGHT27_3:'Approximate nighttime threshold has no approved inequality, night definition or consecutive duration.',
 MAIZE_HNT_FILL28_18D:'Define local night hours and within-night exposure before counting 18 consecutive nights.',
 MAIZE_R6_WIND15:'Exposure duration and wind measurement (gust or sustained speed, height) are unresolved.',
 RICE_SUBMERGENCE_SENSITIVE7D:'Requires consecutive daily crop submergence observations. Monthly surface water does not measure duration or crop submergence.',
 RICE_DROUGHT_FLOWERING_SWP30:'Soil water potential cannot be obtained directly from ERA5 volumetric moisture; duration is also unresolved.',
 RICE_HEAT_DAY37_2:'Daytime metric and consecutive exposure duration are not specified.',
 RICE_HEAT_NIGHT31_2:'Nighttime metric and the tentative duration interpretation require review; daily minimum is not nighttime temperature.',
 RICE_DROUGHT_SM75:'The denominator of 75% soil moisture must be identified. ERA5 volumetric moisture is not relative soil moisture.',
 RICE_RIPENING_HEAT_MEAN28:'The transferred threshold lacks an approved consecutive exposure duration.',
 SOY_FLOOD_DURATION3:'Requires daily flooding observations; the strict >3-day condition must not be silently changed to >=3 days.',
 SOY_FLOOD_DURATION6_GRAIN:'Requires daily flooding observations; the strict >6-day condition must not be silently changed to >=6 days.',
 SOY_SEASONAL_HEAT30:'Seasonal association does not establish that the daily air metric means daily maximum, daily mean or hourly exposure.',
 SOY_WATERLOG_R1_3CM_16D:'Requires daily water depth >=3 cm above the soil for 16 days; rainfall and monthly surface water cannot supply this.',
 SOY_HNT_FILL28_R5_R7:'Experimental 12-hour night regime requires a reviewed mapping to natural local nights.',
 WHEAT_SEEDLING_HEAT42:'42 C is an experimental treatment value; an exceedance inequality has not been established.',
 WHEAT_STEM_DROUGHT_VSMC45_14D:'A reduction relative to an experimental control is not absolute moisture or a climatological anomaly.',
 WHEAT_FROST_POSTHEADING_CANOPY_MINUS3_5:'Canopy temperature cannot be replaced by ERA5 2 m air temperature without a validated transfer; duration is unspecified.',
 WHEAT_HEAT_DAY27_3:'Daytime metric and consecutive exposure duration are not specified.',
 WHEAT_HEAT_NIGHT19_6:'Nighttime metric and tentative consecutive exposure interpretation require review.',
 WHEAT_WATERLOG_Z65_3D:'Requires daily waterlogging observations. The three-day experimental treatment is not a validated damage threshold.',
 WHEAT_BOOT_HEAT35_30_24H:'Paired experimental day/night regime requires a reviewed mapping to local hourly exposures.',
 WHEAT_HNT_POSTANTHESIS_DELTA3_8:'Temperature difference is relative to a paired experimental control, not an ERA5 climatological anomaly.'
};
function spec(resolution,band,operator,threshold,samples,unit,interpretation,mode='run') {
 return {dataset:resolution==='day'?daily:hourly,resolution,band,operator,threshold,min_samples:samples,unit,mode,interpretation,conversion:band.startsWith('temperature')?'kelvin_to_celsius':'metres_to_mm'};
}
const ready={
 MAIZE_HEAT_FILL39_4_41_5:spec('day','temperature_2m_max','>=',39.4,6,'C','Operational six-day mean of daily maxima, aligned with the reported treatment mean; not six separate daily exceedances or a calibrated damage model.','rolling_mean'),
 RICE_GERMINATION_HEAT38_24H:spec('hour','temperature_2m','>=',38,24,'C','Frequency of 24 consecutive hourly 2 m air temperature samples meeting the reviewed experimental exposure.'),
 RICE_HEAT_MEAN_33:spec('day','temperature_2m','>=',33,1,'C','One UTC daily mean meeting the regional threshold.'),
 RICE_COLD_ANTHESIS17_5D:spec('day','temperature_2m','<=',17,5,'C','Operational five consecutive UTC daily means meeting the experimental cold condition; not a calibrated field damage probability.'),
 RICE_COLD_MEAN20:spec('day','temperature_2m','<=',20,1,'C','One UTC daily mean meeting the regional threshold.'),
 RICE_RAIN25:spec('day','total_precipitation_sum','>=',25,1,'mm/day','One UTC daily precipitation total meeting the regional threshold.'),
 RICE_COLD_MEAN17:spec('day','temperature_2m','<=',17,1,'C','One UTC daily mean meeting the regional threshold.'),
 WHEAT_BOOT_COLD_MINUS2_24H:spec('hour','temperature_2m','<=',-2,24,'C','Frequency of 24 consecutive hourly air temperature samples meeting an experimental exposure; spatial mean at 2 m is a field-scale approximation.'),
 WHEAT_RIPENING_RAIN5_8H:spec('hour','total_precipitation_hourly','>=',5,8,'mm/hour','Operational eight consecutive hourly increments meeting the reviewed rainfall treatment. Experimental exposure frequency, not validated sprouting probability.')
};
const ids=[...new Set(rows.map(r=>r.details.rule_id))];
if(ids.length!==35 || ids.some(id=>!!ready[id]===!!blocked[id])) throw Error('Every reviewed rule must have exactly one explicit decision');
const rules=ids.map(id=>{const assignments=rows.filter(r=>r.details.rule_id===id), r=assignments[0];return {
 rule_id:id,crop:r.crop,hazard:r.hazard,phases:[...new Set(assignments.map(r=>r.phase_code))],threshold:r.exact_threshold,exposure:r.consecutive_exposure,
 status:ready[id]?'operational':'unavailable',reason:ready[id]?.interpretation??blocked[id],spec:ready[id]??null,
 evidence_category:r.category,source:r.details.source,doi:r.details.link,limitations:r.details.limitations,
 assignments:assignments.map(r=>({id:r.id,phase:r.phase_code,source_assignments:r.details.source_assignments}))};});
const inputs=['web-v2/public/data/hazard_impact_harmonized_v3.json','metadata/reviewed_sources/REVISION_HUMANA_fases_macro_completada_SOLO_3_COLUMNAS.xlsx'].map(p=>({path:p,sha256:createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex')}));
const audit={version:'2026-09-16',meaning:'Historical frequency of an operational meteorological exposure, not crop damage probability.',calendar:'pixel-calendars/manifest.json',inputs,datasets:[daily,hourly],rules};
fs.writeFileSync(path.join(root,'web-v2/public/data/gee_rule_audit.json'),JSON.stringify(audit,null,2)+'\n');
fs.writeFileSync(path.join(root,'docs/gee_rule_audit.md'),'# Rule-by-rule GEE feasibility audit\n\nGenerated by `scripts/build_gee_rule_audit.mjs` from the reviewed hazard assignments. Operational mappings are project interpretations, not additional claims attributed to papers. Source row IDs and paper references are preserved in `web-v2/public/data/gee_rule_audit.json`.\n\n35 distinct rules: '+Object.keys(ready).length+' operational exposures; '+Object.keys(blocked).length+' unavailable. Maize REP pending assignment is additional context, not a rule.\n\n| Rule | Phases | Decision | Reason / operational definition |\n|---|---|---|---|\n'+rules.map(r=>`| ${r.rule_id} | ${r.phases.join(', ')} | ${r.status} | ${r.reason} |`).join('\n')+'\n');
console.log(`${rules.length} rules; ${Object.keys(ready).length} operational; ${Object.keys(blocked).length} unavailable`);
