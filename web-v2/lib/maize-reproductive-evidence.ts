// Literature evidence only. This record is not an operational climate threshold.
export const maizeReproductiveEvidence = {
  crop: "maize" as const,
  phase_code: "R1",
  derived_stage: "REP — Initial kernel set (late R1)",
  hazard: "Heat during initial kernel set",
  threshold: "Damage-onset threshold not established. Observed mean Tmax: 38.8 °C (2019) and 40.8 °C (2021), with daytime heating for 6 days (08:00–18:00).",
  qualitative_impact: "Heat during the lag stage reduced kernel number, consistent with kernel abortion and impaired initial kernel set.",
  quantitative_impact: "Kernel number per ear: −12.6% (2019), −7.8% (2021). Grain yield: −14.9% and −8.7%, respectively.",
  category: "Damaging experimental treatment",
  details: {
    phase_order: 4,
    rule_id: "MAIZE_REP_LAG_HEAT_ZHANG2023",
    evidence_type: "Phase-specific damage evidence; quantitative threshold unresolved",
    spatial_scope: "Hengshui, China; heat-sensitive hybrid Xianyu335; three field replicates",
    source: "Zhang et al. (2023), Agronomy 13, 2126. Section 2.2 (p. 2), sections 3.1–3.2 (p. 5), Table 1 (p. 6), section 4.1.",
    link: "10.3390/agronomy13082126",
    limitations: "Treatment: 5–10 days after silking. REP is a project crosswalk for initial kernel set, not the authors’ stage label; the authors call it lag stage within grain filling. The window can overlap the transition to R2. Temperatures are treatment means, not a calibrated damage-onset threshold. Do not use them as an exceedance rule or infer a regional calendar window."
  }
};
