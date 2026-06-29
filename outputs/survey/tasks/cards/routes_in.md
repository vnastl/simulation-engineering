# Task theme — Routes into engineering

**Split axis:** university type — **pre-1992 university** (students at a pre-1992, traditional research-intensive university (mostly post-A-level entrants)) vs **post-1992 university** (students at a post-1992, former-polytechnic university with a more vocational intake (more mature and part-time students)).  
_The report's headline finding is the 'significant difference between students studying at a pre- and post-1992 university'; the two intakes follow different routes into engineering. The report cross-tabulates placement and job-factors by university but NEVER the Q1 influence battery — so the by-university routes-in cut is the gap (§1.1). Empirically the richest split for this outcome (9/15 items differ)._

**Outcome (held out):** Influences on the decision to study engineering

**Paper grounding.** Split: university type (pre- vs post-1992). The ESRC report (RES-000-23-0426, p.27, p.20) makes the pre/post-1992 divide its HEADLINE finding — 'a significant difference between students studying at a pre- and post-1992 university', the post-1992 intake being more mature/part-time with 'different priorities and experiences'. Two intakes follow different ROUTES into engineering: the traditional pre-1992 cohort (mostly young post-A-level) vs the vocational post-1992 cohort. The report cross-tabulates placement and job-factors by university but NEVER the Q1 influence battery, so the by-university breakdown of *why students chose engineering* is the gap (§1.1). Powell et al. (2009, pp. 415–421) supply the conceptual frame (entry is shaped by socialisation, hobbies and encouragement); empirically university is the richest cut here (9/15 influences differ — pre-1992 students far more drawn by maths/science, challenge and 'a good degree', post-1992 more likely that 'nobody encouraged' them).

**Conditioning (shown in micro persona).** Background, the decision context (whether they attended an engineering insight course, whether/who discouraged them), and where they intend to go next (further study, preferred role, Chartership, specialism). Who the student is and how engaged they are with the engineering decision predict what drew them in; the specific Q1 influences are held out. The decision-context items are distinct columns from the Q1 battery — a correlated predictor, not the outcome (§1.3).

Conditioning vars: `gender`, `age`, `ethnic`, `religion`, `school`, `year`, `dept`, `uni`, `insight`, `encourag`, `discoura`, `whodisc`, `carpath`, `furstudy`, `studarea`, `workrole`, `charship`

Held-out vars: `highsal`, `interest`, `challeng`, `special`, `mathsci`, `knowledg`, `family`, `hobbies`, `gooddeg`, `varied`, `mother`, `father`, `careers`, `teacher`, `nobody`

## Rubric dimensions (verbatim statements)

- `highsal` — "I was attracted to engineering/design & technology because of the high salary"  
  salient (pos): *agrees that the high salary attracted them to engineering*
- `interest` — "Engineering/Design & Technology provided an opportunity to do interesting work"  
  salient (pos): *agrees that the chance to do interesting work attracted them*
- `challeng` — "I wanted the challenge of solving problems"  
  salient (pos): *agrees that wanting the challenge of solving problems attracted them*
- `special` — "I wanted to use my science and maths background without specialising in either"  
  salient (pos): *agrees that using science and maths without specialising attracted them*
- `mathsci` — "I was good at maths and science at school"  
  salient (pos): *agrees that being good at maths and science at school attracted them*
- `knowledg` — "I chose to study engineering/design & technology with little knowledge of what engineers actually do"  
  salient (pos): *agrees that they chose engineering with little knowledge of the job*
- `family` — "I knew about engineering/design & technology because a member of my family is involved in the industry"  
  salient (pos): *agrees that a family member in the industry informed the choice*
- `hobbies` — "My hobbies and interests are of a technical nature"  
  salient (pos): *agrees that their hobbies and interests are of a technical nature*
- `gooddeg` — "Engineering/Design & Technology will be a good degree to have even if I decide not to enter the profession"  
  salient (pos): *agrees that engineering is a good degree to hold regardless*
- `varied` — "Engineering/Design & Technology appealed to me because it is so varied"  
  salient (pos): *agrees that engineering's varied nature attracted them*
- `mother` — "My mother encouraged me to study engineering/design & technology"  
  salient (pos): *agrees that their mother encouraged them to study engineering*
- `father` — "My father encouraged me to study engineering/design & technology"  
  salient (pos): *agrees that their father encouraged them to study engineering*
- `careers` — "My careers advisor encouraged me to study engineering/design & technology"  
  salient (pos): *agrees that a careers advisor encouraged them*
- `teacher` — "My school teacher encouraged me to study engineering/design & technology"  
  salient (pos): *agrees that a school teacher encouraged them*
- `nobody` — "Nobody encouraged me to study engineering/design & technology"  
  salient (pos): *agrees that nobody encouraged the choice*

## Model-facing prompts

### micro (per respondent — persona prepended)

```
Below is a profile of one engineering / design & technology student, covering their background, the context of their decision to study engineering, and their future intentions.

{persona}

Based only on this profile, predict what influenced this student's decision to study engineering. For each of these possible influences, say whether you expect it applied to them (they would agree) or not, and why: high salary; interesting work; the challenge of problem-solving; using science & maths without specialising; being good at maths/science at school; choosing with little knowledge of the job; a family member in industry; technical hobbies; it being a good degree to hold; its varied nature; encouragement from mother, from father, from a careers advisor, from a teacher; or nobody encouraging them. Write a short paragraph.
```

### macro — prose

```
Consider two populations of engineering / design & technology students:
  A: students at a pre-1992, traditional research-intensive university (mostly post-A-level entrants)
  B: students at a post-1992, former-polytechnic university with a more vocational intake (more mature and part-time students)

In a paragraph, compare what influenced these two populations' decision to study engineering, and for each influence say which population is more likely to agree it applied to them: high salary; interesting work; the challenge of problem-solving; using science & maths without specialising; being good at maths/science at school; choosing with little knowledge of the job; a family member in industry; technical hobbies; it being a good degree to hold; its varied nature; encouragement from mother, from father, from a careers advisor, from a teacher; nobody encouraging them.
```

### macro — number

```
Consider two populations of engineering / design & technology students:
  A: students at a pre-1992, traditional research-intensive university (mostly post-A-level entrants)
  B: students at a post-1992, former-polytechnic university with a more vocational intake (more mature and part-time students)

For each influence below, estimate the percentage of EACH population who would agree it applied to their decision to study engineering (answer 'agree' or 'strongly agree' on a 5-point scale). Give two percentages per influence: high salary; interesting work; the challenge of problem-solving; using science & maths without specialising; being good at maths/science at school; choosing with little knowledge of the job; a family member in industry; technical hobbies; a good degree to hold; varied nature; encouragement from mother, from father, from a careers advisor, from a teacher; nobody encouraging them.
```

## Answer key — SCORER ONLY (not shown to the model)

| item | pre-1992 university % | post-1992 university % | p | significant | keyed direction |
|---|---|---|---|---|---|
| `highsal` | 44.2 | 47.6 | 0.4639 | no | about_equal |
| `interest` | 96.8 | 92.6 | 0.0322 | yes | pre1992 |
| `challeng` | 92.4 | 81.1 | 0.0001 | yes | pre1992 |
| `special` | 64.3 | 42.6 | 0.0000 | yes | pre1992 |
| `mathsci` | 77.5 | 50.0 | 0.0000 | yes | pre1992 |
| `knowledg` | 25.2 | 26.0 | 0.8338 | no | about_equal |
| `family` | 31.7 | 38.8 | 0.1202 | no | about_equal |
| `hobbies` | 56.6 | 53.4 | 0.5213 | no | about_equal |
| `gooddeg` | 89.0 | 68.5 | 0.0000 | yes | pre1992 |
| `varied` | 79.0 | 66.2 | 0.0012 | yes | pre1992 |
| `mother` | 20.2 | 12.9 | 0.0469 | yes | pre1992 |
| `father` | 31.6 | 29.9 | 0.7679 | no | about_equal |
| `careers` | 21.1 | 19.6 | 0.7376 | no | about_equal |
| `teacher` | 36.1 | 19.2 | 0.0001 | yes | pre1992 |
| `nobody` | 32.0 | 46.2 | 0.0014 | yes | post1992 |

Denominators (scorer-only): pre-1992 university n=656, post-1992 university n=148.
Endorsement cut: an item counts as endorsed ('pos') when the respondent answered 4 or 5 on its 5-point scale (agree/strongly agree, or important/very important).
