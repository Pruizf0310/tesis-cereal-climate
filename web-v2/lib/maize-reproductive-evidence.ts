// Literature evidence only. This record is not an operational climate threshold.
export const maizeReproductiveEvidence = {
  crop: "maize" as const,
  phase_code: "REP",
  derived_stage: "Reproductive development",
  hazard: "Pending hazard assignment",
  threshold: "Not assigned — reserved for the reviewed maize REP threat row.",
  qualitative_impact: "Heat during the lag stage reduced kernel number, consistent with kernel abortion and impaired initial kernel set.",
  quantitative_impact: "Kernel number per ear: −12.6% (2019), −7.8% (2021). Grain yield: −14.9% and −8.7%, respectively.",
  category: "Pending assignment",
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
