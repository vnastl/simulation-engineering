# Task theme — Experiences of the engineering degree

**Split axis:** industrial placement — **placement** (engineering students who have gone, or intend to go, on an industrial placement) vs **no placement** (engineering students who do not go on an industrial placement).  
_The industrial placement is the study's KEY transitional stage ('usually women's first major contact with the engineering sector'); the whole project compares placement vs non-placement students. Whether a student goes on placement plausibly reshapes how they view their degree. The report discusses placement heavily but NEVER breaks down the Q4 degree-experience items by placement status — verified clean by the disclosure check._

**Outcome (held out):** Experiences of the engineering degree (views of the course)

**Paper grounding.** Split: industrial placement (gone/intending vs not). The placement is the study's central transitional stage — the ESRC report (pp.15, 17) targets it as 'usually women's first major contact with the engineering sector and ... a key transitional stage', and the entire project contrasts placement with non-placement students (Objectives 1–2). Going on placement plausibly reshapes how a student views their degree — its difficulty, the relevance of modules, whether it builds interpersonal skills, whether they are pleased with the choice. The report discusses placement extensively (reasons for/against, transition to work) and discusses these Q4 degree-views (curriculum, relevance, assessment, theory) — but it attributes their *directions* to sex, discipline and university, NEVER to placement status. The by-placement breakdown of the degree experience is therefore the gap (§1.1), verified absent from both sources by an adversarial disclosure check.

**Conditioning (shown in micro persona).** Background (including whether they go on placement — the split), why they chose engineering (Q1 influences), how satisfied they are with the course (Q5), and where they intend to head. Who the student is, what drew them in and how they rate the teaching are the apt predictors of how they view the degree; the Q4 degree-view statements themselves are held out. The Q5 satisfaction items are a near-leak (correlated with course views, distinct columns) — allowed by §1.3.

Conditioning vars: `gender`, `age`, `ethnic`, `religion`, `school`, `year`, `dept`, `uni`, `placemen`, `highsal`, `interest`, `challeng`, `special`, `mathsci`, `knowledg`, `family`, `hobbies`, `gooddeg`, `varied`, `mother`, `father`, `careers`, `teacher`, `nobody`, `quality`, `supplect`, `supppers`, `groupwk`, `teachhrs`, `friends`, `coursewk`, `theory`, `practwk`, `designwk`, `variety`, `carpath`, `furstudy`, `studarea`, `workrole`, `charship`

Held-out vars: `practica`, `curricul`, `pleased`, `relevanc`, `deadline`, `assess`, `interper`

## Rubric dimensions (verbatim statements)

- `practica` — "The level of practical work on the course is just right"  
  salient (pos): *agrees that the level of practical work on the course is just right*
- `curricul` — "The engineering/design & technology curriculum is more difficult than I expected"  
  salient (pos): *agrees that the engineering curriculum was more difficult than expected*
- `pleased` — "I am pleased I chose to study engineering/design & technology"  
  salient (pos): *agrees that they are pleased they chose to study engineering*
- `relevanc` — "It is difficult to understand the relevance of some modules"  
  salient (pos): *agrees that it is difficult to understand the relevance of some modules*
- `deadline` — "We always have competing deadlines"  
  salient (pos): *agrees that they always have competing deadlines*
- `assess` — "The balance between coursework and exams in module assessments is just right"  
  salient (pos): *agrees that the coursework/exam balance in assessment is just right*
- `interper` — "The course develops interpersonal skills"  
  salient (pos): *agrees that the course develops interpersonal skills*

## Model-facing prompts

### micro (per respondent — persona prepended)

```
Below is a profile of one engineering / design & technology student, covering their background, why they chose engineering, how satisfied they are with the course, and their future intentions.

{persona}

Based only on this profile, predict how this student would rate each of the following statements about their degree, on a scale from strongly disagree to strongly agree:
  (a) The level of practical work on the course is just right.
  (b) The engineering curriculum is more difficult than I expected.
  (c) I am pleased I chose to study engineering.
  (d) It is difficult to understand the relevance of some modules.
  (e) We always have competing deadlines.
  (f) The balance between coursework and exams is just right.
  (g) The course develops interpersonal skills.

Write a short paragraph. For each statement, say whether you expect the student to agree or disagree, and why.
```

### macro — prose

```
Consider two populations of engineering / design & technology students:
  A: engineering students who have gone, or intend to go, on an industrial placement
  B: engineering students who do not go on an industrial placement

In a paragraph, compare how these two populations would rate the following statements about their degree, and say which population is more likely to agree with each:
  (a) The level of practical work on the course is just right.
  (b) The engineering curriculum is more difficult than I expected.
  (c) I am pleased I chose to study engineering.
  (d) It is difficult to understand the relevance of some modules.
  (e) We always have competing deadlines.
  (f) The balance between coursework and exams is just right.
  (g) The course develops interpersonal skills.
```

### macro — number

```
Consider two populations of engineering / design & technology students:
  A: engineering students who have gone, or intend to go, on an industrial placement
  B: engineering students who do not go on an industrial placement

For each statement below, estimate the percentage of EACH population who would agree (answer 'agree' or 'strongly agree' on a 5-point scale). Give two percentages per statement:
  (a) The level of practical work on the course is just right.
  (b) The engineering curriculum is more difficult than I expected.
  (c) I am pleased I chose to study engineering.
  (d) It is difficult to understand the relevance of some modules.
  (e) We always have competing deadlines.
  (f) The balance between coursework and exams is just right.
  (g) The course develops interpersonal skills.
```

## Answer key — SCORER ONLY (not shown to the model)

| item | placement % | no placement % | p | significant | keyed direction |
|---|---|---|---|---|---|
| `practica` | 45.2 | 40.0 | 0.2004 | no | about_equal |
| `curricul` | 41.6 | 50.7 | 0.0247 | yes | no_placement |
| `pleased` | 85.6 | 76.5 | 0.0030 | yes | placement |
| `relevanc` | 44.9 | 54.3 | 0.0212 | yes | no_placement |
| `deadline` | 60.4 | 74.2 | 0.0003 | yes | no_placement |
| `assess` | 48.1 | 48.2 | 1.0000 | no | about_equal |
| `interper` | 73.5 | 66.1 | 0.0433 | yes | placement |

Denominators (scorer-only): placement n=570, no placement n=223.
Endorsement cut: an item counts as endorsed ('pos') when the respondent answered 4 or 5 on its 5-point scale (agree/strongly agree, or important/very important).
