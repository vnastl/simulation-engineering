# Task theme — What matters in a future job

**Split axis:** engineering discipline — **civil & building engineering** (students in the civil & building engineering department (construction-oriented engineering)) vs **design & technology** (students in the design & technology department (design- and product-oriented engineering)).  
_A clean two-discipline head-to-head: civil & building (site-based, location-dependent, company-car construction culture) vs design & technology (studio / product design). Both ~100 students at the same pre-1992 university, so the cut is discipline not institution. The report singles out both disciplines but NEVER splits the Q11 job-factors by discipline — so the cut is the gap (§1.1). Empirically civil students rate location, company-car benefits and training higher._

**Outcome (held out):** Importance of factors when choosing a job

**Paper grounding.** Split: engineering discipline — a clean two-department head-to-head, civil & building engineering vs design & technology (both ~100 students at the same pre-1992 university, so the cut is discipline not institution). The study's Objective 4 is explicitly about disciplinary sub-cultures — 'distinct aspects of different engineering workplaces and cultures' (report p.16) — and the report singles out BOTH of these disciplines (civil/building on practical-work satisfaction; design & technology as distinctive on several outcomes). What a student values in a job tracks the industry their field leads to: civil is the archetypal site-based, location-dependent, company-car construction culture, design & technology a studio/product-design culture. The ESRC report (p.27) cross-tabulates the Q11 job-factors by UNIVERSITY, but NEVER by discipline — so the by-discipline breakdown is the gap (§1.1, verified by the disclosure check). Empirically, civil students rate location, company-car benefits and training markedly higher than design & technology students. (Powell et al. 2009 supply the domestic-sphere / equal-opportunities frame for the battery.)

**Conditioning (shown in micro persona).** Background, future plans (further study, preferred role, Chartership, specialism), and the placement block (whether they went on placement and what they sought from / avoided about it). What a student wants from industrial placement and where they intend to head are the apt predictors of what they will value in a job; the Q11 job-acceptance factors themselves are held out. Placement motivations are distinct columns from the Q11 battery — correlated predictors, not the outcome (§1.3).

Conditioning vars: `gender`, `age`, `ethnic`, `religion`, `school`, `year`, `dept`, `uni`, `carpath`, `furstudy`, `studarea`, `workrole`, `charship`, `placemen`, `experien`, `money`, `educatio`, `jobprosp`, `jobdecid`, `industry`, `perdevel`, `unigrade`, `apptheor`, `finalyr`, `indchart`, `wkexp`, `placloca`, `breaked`, `finuni`, `nogain`, `noappeal`, `noaccept`

Held-out vars: `salary`, `location`, `workenv`, `people`, `travel`, `benefits`, `training`, `promot`, `equalopp`, `flexible`, `childcar`

## Rubric dimensions (verbatim statements)

- `salary` — "Salary will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates salary important*
- `location` — "Location will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates location important*
- `workenv` — "Work environment will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates the work environment important*
- `people` — "People I work with will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates the people they work with important*
- `travel` — "Opportunities to travel will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates opportunities to travel important*
- `benefits` — "Benefits like a company car will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates benefits such as a company car important*
- `training` — "Training opportunities will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates training opportunities important*
- `promot` — "Opportunities for promotion will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates opportunities for promotion important*
- `equalopp` — "Equal opportunites policies will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates equal-opportunities policies important*
- `flexible` — "Opportunities for flexible working will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates opportunities for flexible working important*
- `childcar` — "Child-care policies will be important to me in making a decision to accept a job or decide where to work"  
  salient (pos): *rates childcare policies important*

## Model-facing prompts

### micro (per respondent — persona prepended)

```
Below is a profile of one engineering / design & technology student, covering their background, their industrial-placement experience and motivations, and their future intentions.

{persona}

Based only on this profile, predict which factors this student would rate as important when choosing a job. For each factor, say whether you expect them to rate it important or not, and why: salary; location; work environment; the people they work with; opportunities to travel; benefits like a company car; training opportunities; opportunities for promotion; equal-opportunities policies; flexible working; childcare policies. Write a short paragraph.
```

### macro — prose

```
Consider two populations of engineering / design & technology students:
  A: students in the civil & building engineering department (construction-oriented engineering)
  B: students in the design & technology department (design- and product-oriented engineering)

In a paragraph, compare which job factors these two populations would rate as important when choosing a job, and for each factor say which population is more likely to rate it important: salary; location; work environment; the people they work with; opportunities to travel; benefits like a company car; training opportunities; opportunities for promotion; equal-opportunities policies; flexible working; childcare policies.
```

### macro — number

```
Consider two populations of engineering / design & technology students:
  A: students in the civil & building engineering department (construction-oriented engineering)
  B: students in the design & technology department (design- and product-oriented engineering)

For each job factor below, estimate the percentage of EACH population who would rate it important (answer 'important' or 'very important' on a 5-point scale). Give two percentages per factor: salary; location; work environment; the people they work with; opportunities to travel; benefits like a company car; training opportunities; opportunities for promotion; equal-opportunities policies; flexible working; childcare policies.
```

## Answer key — SCORER ONLY (not shown to the model)

| item | civil & building engineering % | design & technology % | p | significant | keyed direction |
|---|---|---|---|---|---|
| `salary` | 96.9 | 90.1 | 0.0825 | no | about_equal |
| `location` | 86.6 | 75.0 | 0.0472 | yes | civil |
| `workenv` | 91.8 | 96.0 | 0.2440 | no | about_equal |
| `people` | 84.5 | 84.2 | 1.0000 | no | about_equal |
| `travel` | 48.5 | 48.5 | 1.0000 | no | about_equal |
| `benefits` | 50.5 | 22.8 | 0.0001 | yes | civil |
| `training` | 87.6 | 75.2 | 0.0292 | yes | civil |
| `promot` | 94.8 | 88.1 | 0.1282 | no | about_equal |
| `equalopp` | 43.8 | 50.5 | 0.3924 | no | about_equal |
| `flexible` | 63.9 | 53.5 | 0.1506 | no | about_equal |
| `childcar` | 24.0 | 13.9 | 0.0997 | no | about_equal |

Denominators (scorer-only): civil & building engineering n=97, design & technology n=102.
Endorsement cut: an item counts as endorsed ('pos') when the respondent answered 4 or 5 on its 5-point scale (agree/strongly agree, or important/very important).
