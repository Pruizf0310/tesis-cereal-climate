import assert from 'node:assert/strict';
import fs from 'node:fs';
import ts from 'typescript';

const code = fs.readFileSync(new URL('../lib/macro-phases.ts', import.meta.url), 'utf8');
const compiled = ts.transpileModule(code, { compilerOptions: { module: ts.ModuleKind.ESNext } }).outputText;
const { MACRO_PHASES, groupCalendarForDisplay } = await import(`data:text/javascript;base64,${Buffer.from(compiled).toString('base64')}`);
const load = (path) => JSON.parse(fs.readFileSync(new URL(path, import.meta.url), 'utf8'));
const calendar = load('../public/data/phenology_technical_v2.json');
const before = JSON.stringify(calendar);
let bands = 0;
for (const crop of calendar.crops) {
  for (const band of crop.bands) {
    const grouped = groupCalendarForDisplay(crop.id, band.phases);
    assert.deepEqual(grouped.map(p => p.code), MACRO_PHASES.map(p => p.code));
    const sum = (rows, get) => rows.reduce((total, row) => total + get(row), 0);
    assert.ok(Math.abs(sum(grouped, p => p.average_duration_days) - sum(band.phases, p => p.average_duration_days)) < 1e-8);
    for (let m = 0; m < 12; m++) assert.ok(Math.abs(sum(grouped, p => p.average_days_by_month[m]) - sum(band.phases, p => p.average_days_by_month[m])) < 1e-8);
    if (crop.id === 'maize') {
      const rep = grouped.find(p => p.code === 'REP');
      assert.equal(rep.has_counted_window, false);
      assert.ok(rep.shared_notes.some(note => note.includes('FLO + REP')));
    }
    bands++;
  }
}
assert.equal(JSON.stringify(calendar), before, 'Display grouping must not mutate source calendars');
const hazards = load('../public/data/hazard_impact_harmonized_v3.json');
const audit = load('../../docs/phenology_harmonization_audit.json');
const ids = new Set(hazards.rows.map(row => row.id));
assert.equal(ids.size, hazards.rows.length, 'One row per crop/phase/rule');
assert.equal(audit.rows.length, 63);
for (const row of hazards.rows) {
  assert.ok(MACRO_PHASES.some(p => p.code === row.phase_code));
  assert.ok(row.details.link && row.variable && row.exact_threshold);
  for (const assignment of row.details.source_assignments) {
    const original = audit.rows.find(item => item.row === assignment.review_row);
    assert.equal(original.decision, 'grouped');
    assert.equal(original.orange, false);
    assert.ok(original.output_ids.includes(row.id));
  }
}
for (const original of audit.rows) {
  for (const id of original.output_ids) assert.ok(ids.has(id));
  if (original.decision === 'reviewed_not_published') {
    assert.ok(original.reason && original.coverage);
    const actual = hazards.rows.filter(row => row.crop === original.crop && row.details.rule_id === original.rule_id).map(row => row.id);
    assert.deepEqual(original.retained_same_evidence, actual);
  }
}
assert.deepEqual(audit.rows.filter(row => row.decision === 'reviewed_not_published' && row.retained_same_evidence.length === 0).map(row => row.row), [10, 11, 34]);
assert.ok(!hazards.rows.some(row => row.crop === 'maize' && row.phase_code === 'REP'));
console.log(`Passed: ${bands} unchanged calendar bands, six display phases, ${hazards.rows.length} unique evidence groups, all 63 input rows reconciled.`);
