export const MACRO_PHASES = [
  { code: "EST", name: "Establishment" },
  { code: "VEG", name: "Vegetative growth" },
  { code: "FLO", name: "Flowering" },
  { code: "REP", name: "Reproductive development" },
  { code: "FIL", name: "Grain/seed filling" },
  { code: "MAT", name: "Maturation" }
] as const;

export type MacroPhaseCode = (typeof MACRO_PHASES)[number]["code"];

// Display correspondence only. Original calendar files and dates are unchanged.
const CALENDAR_CROSSWALK: Record<string, Record<string, MacroPhaseCode[]>> = {
  maize: { VE: ["EST"], V1_V6: ["VEG"], V7_VT: ["VEG"], R1: ["FLO", "REP"], R2: ["FIL"], R3: ["FIL"], R4_R5: ["FIL"], R6: ["MAT"] },
  rice: { BBCH_00_09: ["EST"], BBCH_10_19: ["VEG"], BBCH_20_29: ["VEG"], BBCH_30_39: ["VEG", "REP"], BBCH_40_59: ["REP"], BBCH_60_69: ["FLO"], BBCH_70_79: ["FIL"], BBCH_80_99: ["MAT"] },
  soybean: { VE_VC: ["EST"], V1_VN: ["VEG"], R1_R2: ["FLO"], R3: ["REP"], R4: ["REP"], R5: ["FIL"], R6_R7: ["FIL", "MAT"], R8: ["MAT"] },
  wheat: { Z00_09: ["EST"], Z10_29: ["VEG"], Z30_39: ["VEG"], Z40_49: ["REP"], Z50_59: ["REP"], Z60_69: ["FLO"], Z70_89: ["FIL"], Z90_99: ["MAT"] }
};

interface CalendarPhase {
  code: string;
  name: string;
  average_duration_days: number;
  average_days_by_month: number[];
}

export function groupCalendarForDisplay(crop: string, phases: CalendarPhase[]) {
  const grouped = MACRO_PHASES.map((phase, index) => ({ ...phase, order: index + 1,
    average_duration_days: 0, average_days_by_month: Array<number>(12).fill(0),
    source_stages: [] as string[], shared_notes: [] as string[], has_counted_window: false,
    includes_shared_window: false
  }));
  for (const phase of phases) {
    const mapped = CALENDAR_CROSSWALK[crop]?.[phase.code];
    if (!mapped) throw new Error(`Missing calendar correspondence: ${crop}/${phase.code}`);
    const owner = grouped.find((item) => item.code === mapped[0])!;
    owner.has_counted_window = true;
    owner.average_duration_days += phase.average_duration_days;
    phase.average_days_by_month.forEach((days, index) => { owner.average_days_by_month[index] += days; });
    owner.source_stages.push(`${phase.code} — ${phase.name}`);
    if (mapped.length > 1) {
      owner.includes_shared_window = true;
      const note = `${phase.code} spans ${mapped.join(" + ")}; its complete window is displayed once under ${owner.code}. Separate phase durations are unresolved.`;
      for (const code of mapped) grouped.find((item) => item.code === code)!.shared_notes.push(note);
    }
  }
  return grouped;
}
