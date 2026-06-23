export const meta = {
  name: 'code-interviews-5723',
  description: 'Code 72 interview transcripts into the 5723 survey schema (one coder per unit)',
  phases: [{ title: 'Code', detail: 'one coder agent per interview, Subject-turn verbatim evidence' }],
}

// Unit lists (from registry.json). 67 verbatim interviews + 5 notes-based.
const PRIMARY = "int01,int02,int03,int04,int05,int06,int07,int08,int10,int11,int12,int13,int14,int15,int16,int17,int18,int19,int20,int21,int22,int23,int24,int25,int26,int27,int29,int30,int34,int35,int36,int37,int38,int39,int40,int41,int42,int43,int44,int45,int46,int47,int48,int49,int50,int51,int52,int53,int54,int55,int56,int57,int58,int59,int60,int61,int62,int63,int64,int65,int66,int67,int68,int69,int70,int71,int72".split(',')
const NOTES = ['int09', 'int28', 'int31', 'int32', 'int33']

const BASE = '/Users/vnastl/Seafile/My Library/mpi social simulation/experiments2/outputs/interviews'

const SUMMARY_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['unit_id', 'wrote_file', 'n_codes', 'n_skips', 'placement_status', 'n_theme_quotes'],
  properties: {
    unit_id: { type: 'string' },
    wrote_file: { type: 'boolean', description: 'true if the coding JSON was written to the exact path' },
    n_codes: { type: 'integer' },
    n_skips: { type: 'integer' },
    placement_status: { type: 'string' },
    n_theme_quotes: { type: 'integer' },
    notes: { type: 'string', description: 'any problems encountered, else empty' },
  },
}

function prompt(unit, verbatim) {
  const evidenceRule = verbatim
    ? `Every code MUST carry a VERBATIM evidence quote copied EXACTLY (character for character) from a turn whose "role" is "Subject". Do NOT take evidence from Interviewer turns: an affirmation like "yeah" whose content lives only in the interviewer's question is interviewer-planted — null it or downgrade it. You may join non-contiguous verbatim fragments with " … " but each fragment must be an exact substring of a Subject turn. Set evidence_role to "Subject".`
    : `This transcript is the interviewer's PROSE NOTES (kind=interview_notes), not a verbatim exchange — there are no Subject turns. Evidence quotes come from the single "Notes" turn and are the interviewer's paraphrase, NOT the subject's words. Set evidence_role to "Notes", cap every confidence at "medium", and never claim a quote is the subject's verbatim speech.`

  return `You are a careful qualitative coder. Code ONE interview into a survey schema, backing every code with evidence.

READ these files first (use the Read tool):
1. Transcript: ${BASE}/transcripts/${unit}.json  — a JSON object with "turns": [{"role":"Interviewer"|"Subject"|"Notes","text":...}]. Code from this.
2. Coding brief: ${BASE}/coding_brief.md  — the TARGET variables, grouped by section, each with its question and the EXACT allowed values (code=label). You may emit ONLY codes listed there.
3. Themes: ${BASE}/addressability.json  — the "themes" map (recurring-question themes -> variable subsets).

CODING RULES (INTERVIEW_TO_TEXT playbook):
- Reuse the survey's value-labels. For a variable, emit ONLY one of its listed integer codes. Never invent a code or label.
- For agreement / satisfaction / importance batteries: code a variable ONLY when the subject clearly expresses that stance about THAT specific item; map it to the nearest allowed point (e.g. clearly positive about course friends -> satisfied/very satisfied). Do not code a whole battery from one general remark.
- For yes/no and categorical variables (placement, who-discouraged, career area, etc.): pick the allowed code the subject's words support.
- ${evidenceRule}
- NULL OVER GUESS. A code is a claim you must back with words on the page. If a variable is not clearly supported, put it in "skips" with reason "not discussed" OR "covered by <var>" (their view is captured on a neighbouring variable).
- confidence: "high" = explicit & direct; "medium" = clear but indirect/inferred; "low" = weak/ambiguous (keep, flag).
- placement_status: classify the subject as one of intend_yes | on_placement | not_going | network75 | unclear (from the content). Use it to set the "placemen" code (yes for intend_yes/on_placement/network75; no for not_going) when supported.
- themes: for EACH of the 4 themes, give 2–6 VERBATIM Subject quotes (Notes quotes for notes-based) that capture the fullest answer to that recurring question AFTER probing — including rich material that no single code captures. Exact substrings only.

OUTPUT: Write a JSON file to EXACTLY this path (use the Write tool):
${BASE}/coding/raw/${unit}.json
with this shape:
{
  "unit_id": "${unit}",
  "verbatim": ${verbatim},
  "placement_status": "<one of the above>",
  "codes": [
    {"var":"family","code":4,"label":"agree","confidence":"high","evidence_role":"Subject","evidence_quote":"<exact substring>","theme":"route_into_engineering","reasoning":"<one line>"}
  ],
  "skips": [{"var":"insight","reason":"not discussed"}],
  "themes": [{"theme":"route_into_engineering","answer_quotes":["<verbatim>","<verbatim>"]}]
}

Be thorough but disciplined: code every variable the transcript genuinely supports (a rich interview supports 25–50), skip the rest with a reason. After writing the file, return the summary object.`
}

phase('Code')

const ALL = [...PRIMARY.map(u => ({ u, verbatim: true })),
             ...NOTES.map(u => ({ u, verbatim: false }))]

const results = await parallel(ALL.map(({ u, verbatim }) => () =>
  agent(prompt(u, verbatim), {
    label: `code:${u}`,
    phase: 'Code',
    agentType: 'general-purpose',
    schema: SUMMARY_SCHEMA,
  })))

const ok = results.filter(Boolean)
const wrote = ok.filter(r => r.wrote_file)
const totalCodes = ok.reduce((a, r) => a + (r.n_codes || 0), 0)
log(`coded ${ok.length}/${ALL.length} units; ${wrote.length} files written; ${totalCodes} total codes`)

return {
  attempted: ALL.length,
  returned: ok.length,
  files_written: wrote.length,
  total_codes: totalCodes,
  failures: ALL.map(x => x.u).filter(u => !ok.find(r => r && r.unit_id === u)),
  not_written: ok.filter(r => !r.wrote_file).map(r => r.unit_id),
}
