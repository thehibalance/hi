# Instruments

**What this file is for.** HI Grade scores 1,139 companies on five dimensions (HUMAN) built
from eighteen sub-signals. A great deal has been measured about how well it does that, and
almost none of those measurements live in this repository — they are in a separate project
archive of findings. What *does* live here is the instruments that produced them, and this
file is the map.

**Read this before measuring anything.** The most expensive mistake available here is
re-deriving a figure that an instrument already computes, because you cannot tell whether
your answer is new.

**This file quotes almost no numbers on purpose.** RUBRIC's coverage figures went stale
because they were pasted in by hand and nothing re-ran them; snapshotting them here would
reproduce that defect in the document written to explain it. Instead, each section names the
instrument that measures the thing. Run it.

---

## 1. The one thing to understand first

The engine decides, per company, which sub-signals count as **evidence** rather than as a
filled-in blank. That test lives at `scoring_engine.py:1906`:

```python
real_count = sum(1 for k, v in all_details.items()
                 if v != 50 and k not in INDUSTRY_DERIVED
                 and k not in ABSENCE_DERIVED)
```

Three consequences, and all of them bite:

**A neutral 50 is a null, not a score.** A sub-signal with no data is set to exactly 50 and
excluded. So means, correlations and coverage must all state which arm they were computed
over. `mean ALL` and `mean != 50` are different numbers for the same sub-signal and have been
confused in this project at least twice, once reversing a prediction.

**`real_count` and its provenance are both published.** Every scored row carries
`signal_coverage` — `"14/18 sub-signals with real data"` — plus **`industry_derived`** and
**`absence_derived`**, the two sorted lists of sub-signal codes that count excluded.

Before 2026-10-28 only the count shipped and the sets were cleared on the next call, so
nothing outside the engine could tell *which* fourteen. `measure_rubric_figures.py` still
carries the `v != 50` fallback it needed then and prints which arm it used — if it says
**NON-NEUTRAL PROXY**, the rows you are reading predate the change.

**So fourteen of the eighteen sub-signals are exactly recomputable from
`data/scores/all_scores.json`, and four are not.** For the fourteen, `v != 50` *is* the whole
test, so a count of non-neutral values is the engine's own count — not an approximation of it.
The four exceptions are industry lookup tables whose constants sit off 50:

| sub-signal | why a `v != 50` count gets it wrong |
|---|---|
| H.2 | added unconditionally — the entire sub-signal is the `craft_defaults` table |
| U.4 | `u4_industry` constant for most of the index, discarded when real data arrives |
| A.1 | discarded when real data arrives, but CDP scores collide with the fallback set {30,40,45,50,55,60,65}, so the split is not determinable from published data |
| A.4 | `hw_defaults` industry constant |

**No line numbers here, on purpose.** The first version of this file quoted eight of them
from a two-week-old grep and every one was already wrong — the engine had grown underneath
them. Hand-copied figures in the document whose §4 says not to hand-copy figures. Get the
current ones from the source:

```
grep -n 'INDUSTRY_DERIVED\|ABSENCE_DERIVED' scoring_engine.py
```

Count those four from the scores file and you get 748 / 730 / 478 / 951 against RUBRIC's
0 / 38 / ~32 / 101. RUBRIC's figures for them come from the collector stores instead, so they
**cannot be checked from here at all** — and a reader who tries will conclude the document is
wrong when it is merely unverifiable.

They are not all right either, which is a different problem and an open one. The engine
credits **324** sub-signal-instances across those four; RUBRIC documents **171**
(U.4 38 + A.1 32 + A.4 101). The missing **153** is most likely A.1, whose own RUBRIC entry
says the split *"cannot be determined from published data because one measured path writes
`cdp_score` directly and CDP scores collide with the fallback values"*. Resolving it needs
`scoring_engine.py`, not the scores file — see §7.

`H.1`, `H.3` and `M.3` are `ABSENCE_DERIVED` and are set to **exactly 50** when withheld,
so `v != 50` already excludes them and they stay exactly recomputable. That was an assumption
until it was measured.

**Seven sub-signals are tracked in total** — four industry, three absence — one more than the
six recorded on 2026-10-14. H.1 joined when v1.14.0 gave it a declared domain of [0.25, 4]
and began withholding ratios outside it. Expect this number to move again; the grep above is
the only trustworthy count.

> **Re-measure all of this:** `python3 measure_rubric_figures.py` — it reads every
> `Coverage` line in `RUBRIC.md` and prints claim against measurement with a verdict, and
> cross-checks its own per-row count against the published `signal_coverage`. That
> cross-check must stay **≤ 0 on every row**; a positive value means a new sub-signal has
> joined a derived set with a non-50 value and every per-sub-signal figure needs re-deriving.

---

## 2. The inventory

<!-- INSTRUMENTS:BEGIN generated by `python3 instruments.py --write-md` -->

**32 instruments, 74 production modules** in `pipeline/`, classified by `instruments.py`.

| instrument | signal | what it answers |
|---|---|---|
| `audit_all_tables.py` | PREFIX | Every hand-written table, which sub-signal reads it, and how much it carries. |
| `audit_constants.py` | PREFIX | Tier 1: how much of each 'constant' sub-signal is actually constant. Read-only. |
| `audit_redundancy.py` | PREFIX | Which sub-signals are the same measurement? Read-only. From pipeline/: |
| `audit_rubric_vs_engine.py` | PREFIX | The master audit: what the RUBRIC claims vs what the engine does. Read-only. |
| `audit_surface_area.py` | PREFIX | The denominator: everything that exists, and whether anything has audited it. |
| `check_continuity.py` | PREFIX | Fail the build when a published surface disagrees with the engine. |
| `check_errors.py` | PREFIX | Summarize pipeline collection errors. Fails the job on systematic failures. |
| `check_staleness.py` | PREFIX | A gate: fail the nightly when a collector goes quiet. Read-only. From pipeline/: |
| `collection_coverage.py` | DOCSTRING | How fast does a change actually reach production? Read-only. From pipeline/: |
| `count_sources.py` | PREFIX | The honest source count, and the dead source paths. Read-only. From pipeline/: |
| `instruments.py` | DOCSTRING | Which .py files are instruments rather than production code, in one place. |
| `measure_authored_sources.py` | PREFIX | What changes if GLASSDOOR_DATA and JOB_DATA stop counting as evidence? Read-only. |
| `measure_ceiling.py` | PREFIX | Why do measured sub-signals score above the middle? Read-only. From pipeline/: |
| `measure_h1_provenance.py` | PREFIX | Every company's H.1, by which branch produced it. Read-only. From pipeline/: |
| `measure_identity_collisions.py` | PREFIX | Two silent failure modes in the company matcher, measured. Read-only. From pipeline/: |
| `measure_rpe_medians.py` | PREFIX | The denominator of the largest real sub-signal. Read-only. From pipeline/: |
| `measure_rubric_figures.py` | PREFIX | Every coverage and correlation figure RUBRIC.md publishes, re-measured against today's |
| `patch_rubric_measured.py` | PREFIX | RUBRIC.md's coverage and correlation figures, re-measured 2026-10-21. From pipeline/: |
| `patch_rubric_note.py` | PREFIX | One block into RUBRIC.md: how the Coverage figures below it were measured. From pipeline/: |
| `patch_v130_h3.py` | PREFIX | v1.3.0 addendum — H.3 must not use a baseline H.1 refused. |
| `probe_a3_epa.py` | PREFIX | What patch two would do to A.3, measured before it ships. Read-only. From pipeline/: |
| `probe_dn.py` | PREFIX | Is a fifth of the composite carrying any information? Read-only. From pipeline/: |
| `probe_dn2.py` | PREFIX | What is the composite responding to? Read-only. From pipeline/: |
| `probe_h3_form.py` | PREFIX | H.3's ceiling: the measurement v1.3.0 ran for H.1, aimed at H.3. Read-only. |
| `probe_n2.py` | PREFIX | Where does N.2 = 70 come from, and does this project call it evidence? |
| `sim_h1.py` | PREFIX | Simulate H.1's scale against H.3's. Read-only. From pipeline/: |
| `sim_h3.py` | PREFIX | Simulate four separable H.3 changes. Read-only. From pipeline/: |
| `simulate_renorm.py` | PREFIX | HI Grade — Renormalization Simulation. Read-only. Changes nothing. |
| `source_audit.py` | NAME | HI. — Source Audit |
| `ticker_audit.py` | NAME | HI Grade — Ticker Universe Audit v2. Read-only. |
| `universe_audit.py` | NAME | Is every ticker in the universe still a company? |
| `verify_nightly.py` | PREFIX | Morning check — v1.14.0 (spec 1.13.0). Read-only. From pipeline/: |

`signal` is how `instruments.py` classified it: **PREFIX** a known filename prefix, **NAME** "audit" in the stem, **DOCSTRING** a `read-only.` claim in the module docstring. DOCSTRING is the one that does not rot, because it describes behaviour rather than naming.

**1 documented exception** — matched a signal, held as production code:

- `cleanup_audit.py` — WRITES. 'HI. Data Cleanup - fix domain collisions, dupes, and bad mappings.' Caught by NAME because 'audit' is in the stem. Treating it as an instrument would exclude it from the audit, so its own tables would stop being scanned.

<!-- INSTRUMENTS:END -->

Add an instrument, then run `python3 instruments.py --write-md` and the table above is true
again. Nothing needs remembering.

`instruments.py` is also the single definition of what counts as an instrument, in the same
form as `source_rules.py` (the source-publication rule) and `scored_rows.py` (what a scored
row is). Both audits import it rather than carrying their own list — they each used to, and
both rotted. See `FINDING-the-audit-denominator-was-machine-dependent.md`.

---

## 3. Where to start, by question

| you want to know | run |
|---|---|
| is the nightly's output sane this morning | `verify_nightly.py` |
| does a published surface disagree with the engine | `check_continuity.py` |
| has a collector gone quiet | `check_staleness.py`, `check_errors.py` |
| how many sources really feed the scores | `count_sources.py` |
| which hand-written tables exist and who reads them | `audit_all_tables.py` |
| what exists at all, and whether anything has audited it | `audit_surface_area.py` |
| which sub-signals are the same measurement twice | `audit_redundancy.py` |
| does RUBRIC still match the engine | `audit_rubric_vs_engine.py`, `measure_rubric_figures.py` |
| why measured sub-signals score above the middle | `measure_ceiling.py` |
| which branch produced a company's H.1 | `measure_h1_provenance.py` |
| does the company matcher silently merge two firms | `measure_identity_collisions.py` |
| what an authored table contributes as evidence | `measure_authored_sources.py` |
| how fast a change reaches production | `collection_coverage.py` |
| what a proposed scale change would do before it ships | `sim_h1.py`, `sim_h3.py`, `simulate_renorm.py` |

Everything above is read-only. `patch_*.py` files are one-shot appliers and are gitignored by
design; they are not instruments and they are not kept.

---

## 4. How measurement is done here

These are not style preferences. Each one is a mistake that was made, found, and cost a
retraction.

**Write the rule beside the number.** A correct figure was retracted because a second script
using a different rule produced a different number; the first was right, and nobody could
tell because neither rule was written down. Two instruments can disagree legitimately — a
disagreement is not evidence against either until both rules are stated.

**When a mechanism's output is observable, look at the output.** Do not infer what it must
have done. Four retractions in one thread came from reasoning about code whose printed output
was one command away.

**A claim quantified by "sampled" or "observed" cannot be used as a premise.** A finding was
built on "every *sampled* value is a multiple of 0.05". The hedge was dropped in restatement
and the finding was false.

**State predictions before running the check.** Two hypotheses were refuted this way in one
week and both refutations were worth more than the hypotheses would have been.

**Name the arm.** Every mean, every correlation, every coverage count needs its denominator
stated in the same sentence. `n` moving is usually more informative than the statistic moving.

**Verify that what must not change did not.** Patch scripts here check every anchor before
writing anything, and assert afterwards — including absences. That has caught a patch
destroying its own edits, an anchor matching twice, and a reverted change staying reverted.

---

## 5. The recurring defect class

Most defects found in this system are one shape:

> **A failure recorded as a favourable fact.**

Instances, all confirmed: FDA 404s stored as clean records; CFPB "zero complaints" scored as
good; `"No EPA-regulated facilities found"` treated as a conclusion; EPA's 26 error rows
counted as an active source; a litigation value of zero read as a clean record; `else: 85` as
a fallback; 90 points for filing a mandatory report; 70 for being arithmetically average.

Three variants worth knowing separately, because they are harder to see:

**A drift recorded as agreement.** A continuity gate held a four-member copy of a
seven-member rule and reported a stale published figure as correct. The rule now lives in one
place (`source_rules.py`) and the gate imports it.

**Two values from one measurement, counted as two.** H.1 and H.3 are both functions of
`industry_median / rpe` and correlate at Spearman 0.944. For about a third of the index they
are the *only* two sub-signals with real data, so "2 of 18" describes one measurement reported
twice. See `FINDING-for-a-third-of-the-index-the-evidence-is-one-datum-counted-twice.md`.

**A classifier that rots in the flattering direction.** A list maintained by enumeration
decays asymmetrically. Two audits identified instruments by filename prefix; a missed
instrument inflated apparent unaudited code *and* deflated the audit count, so the measurer
looked more thorough about a bigger problem, and nothing ever reported an error.

---

## 6. Conventions

**Read-only scripts say so, with a period.** `"Read-only. From pipeline/:"` or
`"Read-only. Changes nothing."` That sentence is how `instruments.py` classifies a file it
does not recognise by name, so it is load-bearing, not decoration. `api_server.py` says
`- Read-only: no write endpoints exposed` — true of the API's endpoints, not of the file —
which is why the test requires the terminating period.

**`.gitignore` has swallowed instruments twice.** A blanket `check_*.py` hid
`check_continuity.py` from CI and was narrowed in v1.8.2; a blanket `probe_*.py` kept nine
measurement scripts out of the repository until 2026-10-22. Both are now narrowed to
`*_tmp*` / `*_scratch*`. Before adding a prefix rule, consider that instruments get named
after what they do.

**Patch scripts verify, then write, then assert.** They are gitignored, single-use, and
disposable — but the pattern is not: anchor-exact, all-or-nothing, with post-write checks
including the things that must *not* have moved.

**Release numbering is offset from the spec.** Release vN.M stamps spec N.(M−1). v1.14.0
stamps `spec_version: "1.13.0"`. The engine's stamp and the formula it describes must change
in the same commit.

---

## 7. The largest piece of specified, unstarted work

**Eighteen per-sub-signal coverage replays.** RUBRIC publishes a coverage figure for each of
the eighteen sub-signals. Fourteen are checkable from the scores file today. Nothing
reproduces them from the inputs — which is what would make all eighteen checkable, including
the four industry-derived ones that currently cannot be verified at all.

`measure_h1_provenance.py` is the template and does exactly this for H.1: it imports the
engine's own `index_by_company` and `find_match` rather than reimplementing matching, replays
every branch, classifies each company, and reconstructs the published value so that a
mismatch is a writer nobody has found.

Seventeen more of those, one per sub-signal, each about 150 lines, each independently
checkable, none requiring a judgment call about what the engine ought to do. That retires one
unverifiable published figure per instrument.

**The cheaper alternative, if it is ever acceptable to change the engine:** emit
`industry_derived` and `absence_derived` on every row. The sets exist in memory at
`scoring_engine.py:217`/`222` and are cleared at `1804`. Publishing them turns all eighteen
replays into one `json.load` and ends the inference category permanently.
