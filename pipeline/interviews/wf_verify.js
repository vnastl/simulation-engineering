export const meta = {
  name: 'verify-interviews-5723',
  description: 'Adversarial re-read + blind second pass over quote-checked interview codings',
  phases: [
    { title: 'Adversarial', detail: 'fresh agent re-reads transcript, checks each quote supports the ASSIGNED code' },
    { title: 'Blind', detail: 'independent re-code of low-confidence fields, not shown the original code' },
  ],
}

const PRIMARY = "int01,int02,int03,int04,int05,int06,int07,int08,int10,int11,int12,int13,int14,int15,int16,int17,int18,int19,int20,int21,int22,int23,int24,int25,int26,int27,int29,int30,int34,int35,int36,int37,int38,int39,int40,int41,int42,int43,int44,int45,int46,int47,int48,int49,int50,int51,int52,int53,int54,int55,int56,int57,int58,int59,int60,int61,int62,int63,int64,int65,int66,int67,int68,int69,int70,int71,int72".split(',')
const NOTES = ['int09', 'int28', 'int31', 'int32', 'int33']
const UNITS = [...PRIMARY, ...NOTES]

const BASE = '/Users/vnastl/Seafile/My Library/mpi social simulation/experiments2/outputs/interviews'

const ADV_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['unit_id', 'wrote_file', 'n_checked', 'n_supported', 'n_corrected', 'n_rejected'],
  properties: {
    unit_id: { type: 'string' }, wrote_file: { type: 'boolean' },
    n_checked: { type: 'integer' }, n_supported: { type: 'integer' },
    n_corrected: { type: 'integer' }, n_rejected: { type: 'integer' },
    notes: { type: 'string' },
  },
}
const BLIND_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['unit_id', 'wrote_file', 'n_recoded'],
  properties: {
    unit_id: { type: 'string' }, wrote_file: { type: 'boolean' },
    n_recoded: { type: 'integer' }, notes: { type: 'string' },
  },
}

function advPrompt(u) {
  return `You are an ADVERSARIAL verifier. Default to skepticism. Re-read ONE interview and check each already-assigned code.

READ:
1. Transcript: ${BASE}/transcripts/${u}.json (turns with roles)
2. The codes to verify: ${BASE}/coding/checked/${u}.json — the "codes" array (each has var, code, label, confidence, evidence_quote, reasoning). The "allowed_values" per variable are in ${BASE}/coding_brief.md.

For EACH code, decide whether the evidence quote — read in context — genuinely supports the ASSIGNED code (not a neighbouring code, not a weaker/stronger point on the scale). Be strict:
- "supported": the quote clearly supports this exact code.
- "wrong_code": the quote supports the variable but a DIFFERENT allowed code (give corrected_code + corrected_label).
- "unsupported": the quote does not support this variable at all, OR it is interviewer-planted (content only in the Interviewer turn) → reject.
Also downgrade confidence where support is thin (give corrected_confidence).

OUTPUT: Write JSON to EXACTLY ${BASE}/coding/verify/${u}.adv.json :
{"unit_id":"${u}","verdicts":[{"var":"family","verdict":"supported|wrong_code|unsupported","corrected_code":null,"corrected_label":null,"corrected_confidence":null,"note":"<one line>"}]}
Include one verdict object per code, in the same order. Then return the summary.`
}

function blindPrompt(u) {
  return `You are an INDEPENDENT coder doing a BLIND second pass. You will re-code ONLY the LOW-CONFIDENCE fields of one interview, WITHOUT being shown the original code.

READ:
1. Transcript: ${BASE}/transcripts/${u}.json
2. The list of variables to re-code: open ${BASE}/coding/checked/${u}.json and take every entry of "codes" whose "confidence" == "low" — use ONLY their "var" names (IGNORE their code/label/quote; do not be anchored). If there are none, write an empty list and return n_recoded=0.
3. Allowed values per variable: ${BASE}/coding_brief.md

For each such variable, independently decide the best allowed code from the transcript, with your own verbatim Subject-turn quote, or null if you cannot support it. Do not look at or infer the original assignment.

OUTPUT: Write JSON to EXACTLY ${BASE}/coding/verify/${u}.blind.json :
{"unit_id":"${u}","recodes":[{"var":"carpath","code":2,"label":"design work","confidence":"medium","evidence_quote":"<verbatim>","reasoning":"<one line>"}]}
(code=null if unsupportable). Then return the summary.`
}

// --- Phase 1: adversarial re-read (every unit) ---
phase('Adversarial')
const adv = await parallel(UNITS.map(u => () =>
  agent(advPrompt(u), { label: `adv:${u}`, phase: 'Adversarial',
    agentType: 'general-purpose', schema: ADV_SCHEMA })))

// --- Phase 2: blind second pass (every unit; agent self-selects low-conf vars) ---
phase('Blind')
const blind = await parallel(UNITS.map(u => () =>
  agent(blindPrompt(u), { label: `blind:${u}`, phase: 'Blind',
    agentType: 'general-purpose', schema: BLIND_SCHEMA })))

const advOk = adv.filter(Boolean)
const blindOk = blind.filter(Boolean)
log(`adversarial: ${advOk.length}/${UNITS.length}; blind: ${blindOk.length}/${UNITS.length}`)

return {
  adversarial_done: advOk.length,
  blind_done: blindOk.length,
  total_rejected: advOk.reduce((a, r) => a + (r.n_rejected || 0), 0),
  total_corrected: advOk.reduce((a, r) => a + (r.n_corrected || 0), 0),
  total_recoded: blindOk.reduce((a, r) => a + (r.n_recoded || 0), 0),
  adv_failures: UNITS.filter(u => !advOk.find(r => r && r.unit_id === u)),
  blind_failures: UNITS.filter(u => !blindOk.find(r => r && r.unit_id === u)),
}
