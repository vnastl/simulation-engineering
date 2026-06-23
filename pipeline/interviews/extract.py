"""Extract transcripts -> text preserving speaker turns (INTERVIEW playbook §3).

RTF -> text, splitting on the `Speaker:\\t` turn markers. The Interviewer/Subject
structure is signal (who is asked vs who answers) and must survive, because the
coder may only take evidence quotes from *Subject* turns (§3, §5.1). Individual
interviews (int01-72) parse to a clean two-speaker turn list; focus groups
(fg01-02) have many named speakers and are tagged as group sessions
(supporting-only / excluded from per-unit coding, §3).

Wording is kept verbatim (light normalisation only) so quotes round-trip through
the deterministic quote-presence check later (§5.1).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from striprtf.striprtf import rtf_to_text

ROOT = Path(__file__).resolve().parent.parent.parent
RTF_DIR = ROOT / "data/UKDA-5723-spss/rtf"
OUT = ROOT / "outputs/interviews"

TURN_RE = re.compile(r"^([A-Za-z][A-Za-z0-9 _'/-]{0,30}?):\t\s*(.*)$")
SUBJ_RE = re.compile(r"^(Subject|Respondent|Participant)\s*:\t", re.I)
INTV_RE = re.compile(r"^Interviewer", re.I)


def _normalise(s: str) -> str:
    # join hard-wrapped lines within a turn; collapse runs of whitespace; keep glyphs.
    s = s.replace("\r", "\n")
    return s


def detect_format(text: str) -> str:
    """One of: 'tagged' (Speaker:\\t for every turn, incl. focus groups),
    'alternating' (tagged Interviewer turns, untagged Subject replies between),
    'notes' (interviewer's prose notes, no speaker turns at all)."""
    lines = text.split("\n")
    has_subject = any(SUBJ_RE.match(l) for l in lines)
    has_named = sum(1 for l in lines if TURN_RE.match(l)) > 3
    has_interviewer = any(INTV_RE.match(l) for l in lines)
    if has_subject or (has_named and not has_interviewer):
        return "tagged"
    if has_interviewer:
        return "alternating"
    return "notes"


def parse_turns(text: str, fmt: str):
    """Split transcript text into [{speaker, text}] preserving order."""
    turns = []

    def push(speaker, lines):
        t = re.sub(r"\s+", " ", " ".join(l.strip() for l in lines if l.strip())).strip()
        if t:
            turns.append({"speaker": speaker, "text": t})

    if fmt == "notes":
        push("Notes", text.split("\n"))
        return turns

    cur_speaker, cur_lines = None, []
    for line in text.split("\n"):
        m = TURN_RE.match(line)
        if m:
            push(cur_speaker, cur_lines)
            cur_speaker, cur_lines = m.group(1).strip(), [m.group(2)]
        elif fmt == "alternating" and line.strip() and cur_speaker is not None \
                and not INTV_RE.match(cur_speaker or ""):
            # untagged line while in a non-interviewer turn -> continuation
            cur_lines.append(line)
        elif fmt == "alternating" and line.strip() and cur_speaker is not None \
                and INTV_RE.match(cur_speaker):
            # untagged non-blank line right after an Interviewer turn = Subject reply
            push(cur_speaker, cur_lines)
            cur_speaker, cur_lines = "Subject", [line]
        else:
            if cur_speaker is not None:
                cur_lines.append(line)
    push(cur_speaker, cur_lines)
    return turns


def canonical_speaker(sp: str, is_group: bool) -> str:
    low = sp.lower()
    if low.startswith("interviewer") or low in ("int", "i", "moderator", "facilitator"):
        return "Interviewer"
    if not is_group and low in ("subject", "respondent", "participant", "r", "s"):
        return "Subject"
    return sp  # named focus-group participant kept as-is


def extract_one(path: Path):
    is_group = path.stem.lower().replace("sn5723", "").startswith("fg")
    with open(path, errors="replace") as fh:
        text = rtf_to_text(_normalise(fh.read()))
    fmt = "tagged" if is_group else detect_format(text)
    turns = parse_turns(text, fmt)
    for t in turns:
        t["role"] = canonical_speaker(t["speaker"], is_group)
    speakers = sorted({t["speaker"] for t in turns})
    subj_turns = [t for t in turns if t["role"] == "Subject"]
    if is_group:
        kind = "focus_group"
    elif fmt == "notes":
        kind = "interview_notes"          # interviewer prose, NOT verbatim (§5.1 caveat)
    else:
        kind = "interview"
    return {
        "file": path.name,
        "unit_id": path.stem.replace("SN5723", ""),     # e.g. int01, fg01
        "kind": kind,
        "format": fmt,
        "is_group": is_group,
        "verbatim": kind in ("interview", "focus_group"),
        "n_turns": len(turns),
        "n_subject_turns": len(subj_turns),
        "speakers": speakers,
        "full_text": text,
        "turns": turns,
    }


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    tdir = OUT / "transcripts"
    tdir.mkdir(exist_ok=True)
    index = []
    for path in sorted(RTF_DIR.glob("SN5723*.rtf")):
        rec = extract_one(path)
        (tdir / f"{rec['unit_id']}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1))
        index.append({k: rec[k] for k in
                      ("file", "unit_id", "kind", "format", "is_group", "verbatim",
                       "n_turns", "n_subject_turns", "speakers")})
    (OUT / "transcript_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
    from collections import Counter
    kinds = Counter(r["kind"] for r in index)
    print(f"[extract] {len(index)} transcripts -> {tdir}")
    print(f"[extract] kinds: {dict(kinds)}")
    bad = [r["unit_id"] for r in index
           if r["kind"] == "interview" and r["n_subject_turns"] == 0]
    notes = [r["unit_id"] for r in index if r["kind"] == "interview_notes"]
    print(f"[extract] verbatim interviews with 0 Subject turns: {bad if bad else 'none'}")
    print(f"[extract] notes-based (non-verbatim) interviews: {notes}")
    return index


if __name__ == "__main__":
    build()
