# Archive Vision — Implementation Plan

**Branch:** `dev` · **Date:** 2026-09-02 · **Design:** [DESIGN.md](DESIGN.md)

Read [../CLAUDE.md](../CLAUDE.md) first. It carries the known traps with line
numbers and the hard constraints.

---

## How to use this plan

Tasks are `T*` (from the CEO review) and `E*` (from the eng review). Each has a
priority, a dual effort estimate, the finding that produced it, and a verification
step. Check them off as you ship.

- **P1** blocks progress. **P2** should land in the same branch. **P3** is follow-up.
- Effort is given as `human ~X / CC ~Y`. The second number assumes Claude Code.
- Do not invent tasks that are not here. If you find new work, add it to
  [../TODOS.md](../TODOS.md) with context.

### Do these two first, today

| | Task | Why now |
|---|---|---|
| 1 | **E3** — tokenizer check | 10 minutes, and it can invalidate all of Phase 3 |
| 2 | **E1** — start data acquisition | Longest lead time, external dependency, blocks Phases 2-3 |

### Already done (2026-09-02)

| Task | What landed |
|---|---|
| ~~E2~~ | Duplicate uploads purged. `backend/data/uploads/` and `backend/data/transcripts/` are empty. |
| ~~T31~~ | `CLAUDE.md`, `docs/DESIGN.md`, `docs/PLAN.md`, `TODOS.md` written. |
| ~~E20~~ (part) | `.DS_Store` files removed repo-wide, `__pycache__` cleared, `pres.py` and `temp_00000015.jpg` gone. **Remaining:** `.git` is 790MB and `.gitignore:210` excludes `.jpg` — both tied to the E1 storage decision. |
| ~~T14b~~ (part) | `Alphabet.docx` and `F203.docx` deleted from the repo. **Remaining:** the ~120 lines of parsing code in `ocr_service.py:402-525` still reference them. |

---

## Phase gate map

```
  PHASE 0  ── eval harness + correctness batch ──┐
   (wks 1-2)  E1 E3 E4 E5 E9 E10 E11             │  no data needed for
              T5 T6 T8 T17 T26 T35               │  the bug batch
                          │                       │
  PHASE 1  ── benchmark ──┤                       │
   (wk 2-3)   E12 T33     │                       │
                          ▼                       │
              ◆ GATE: build vs adopt ◄────────────┘
                 pre-committed CER threshold
                          │
  PHASE 2  ── layout ─────┤   needs: ~20 sourced pages
   (wks 3-5)  E6 E7 E8 T2 T3 E15 E17 T1
                          │
  PHASE 3  ── recognition ┤   needs: Digital Peter + verified tokenizer
   (later)    T36 T37 E13 E14 T12 fine-tune, then D-19 (CTC)
                          │
  PHASE 4  ── flywheel ───┘   deferred until there are users
              T10 T11 T15_DEFER T7_DEFER
```

---

## Phase 0 — Measure and stop the bleeding

**Goal:** a number you trust, and the code no longer lying about what it does.
**Blocked by:** nothing. The bug batch needs no data at all.

### Data

- [ ] **E1 (P1, human: ~1w / CC: ~1h + archive access)** — data — **BLOCKING: acquire a corpus**
  - Surfaced by: verified — all 27 uploads share md5 `02146e7b36dc9d28b7dccc9ccc17f3e2`; usable corpus is one page
  - Do: pull [Digital Peter](https://arxiv.org/pdf/2103.09354) (9,694 annotated lines) for recognition. Source ~20 real Fund 203 pages from cgamos.ru for layout measurement and CER ground truth. Spend 20 minutes verifying the [Russian Empire Period Manuscripts](https://openreview.net/pdf/8fc2738629b918329dae9d7765f7d31e9cdb2dc7.pdf) dataset, which may be a closer orthographic match. Check redistribution licensing. Decide image storage: LFS, a DVC-style manifest with hashes, or an out-of-band bundle.
  - Note: `.gitignore:210` excludes `.jpg` and `.git` is already 790MB, so "just commit them" is not available
  - Files: `backend/data/`, `.gitignore`, `.gitattributes`
  - Verify: `ls` shows N distinct md5s where N is the real page count; the other contributor can obtain the identical set

### The 10-minute check that gates Phase 3

- [ ] **E3 (P1, human: ~10m / CC: ~5m)** — recognize — Verify the TrOCR tokenizer contains ѣ ѳ і ѵ
  - Surfaced by: outside voice — if they map to `<unk>`, no fine-tuning can make the model emit them and the recognition track is capped before it starts
  - Do: load `kazars24/trocr-base-handwritten-ru`'s processor, encode a string containing all four characters, assert none round-trip to `<unk>`
  - Verify: a test asserting round-trip fidelity for the full pre-reform charset
  - **If this fails, stop and re-plan Phase 3 before doing anything else.**

### Eval harness

- [ ] **E4 (P1, human: ~3d / CC: ~40m)** — eval — Two-metric harness
  - Surfaced by: Section 3 + outside voice — one page-level CER conflates layout and recognition errors
  - Do: `scripts/eval_layout.py` (detection IoU, reading-order correctness, **page-split pass/fail**) and `scripts/eval_recognition.py` (CER/WER via `jiwer`, measured on **manually cropped** line images so it survives preprocessing changes)
  - Files: `scripts/eval_layout.py`, `scripts/eval_recognition.py`
  - Verify: both metrics produce a number on a known fixture with a hand-computed expected value

- [ ] **E5 (P1, human: ~half day / CC: ~20m)** — docs — Transcription convention document, **before ground-truth page 1**
  - Surfaced by: outside voice — two annotators without a written convention produce incomparable ground truths and an uninterpretable CER
  - Do: decide and write down: abbreviations, superscripts, crossed-out text, ditto marks, whether ѣ is normalized, and the exact `jiwer` settings (lowercasing, punctuation stripping)
  - Files: `docs/transcription-convention.md`
  - Verify: a second person can transcribe the same line and match character-for-character

- [ ] **E11 (P1, human: ~1d / CC: ~20m)** — eval — `make eval` writing a committed results file
  - Surfaced by: Issue 5 decision A + outside voice — beam search is not bit-reproducible across machines
  - Do: pin seeds, round metrics to 3 decimals, record torch/CUDA/device in the output file so a diff is attributable
  - Files: `Makefile`, `eval/results.md`
  - Verify: two consecutive runs on the same machine produce an identical file

### Correctness batch (no data required, fully parallel)

- [ ] **T5 (P1, human: ~30m / CC: ~5m)** — recognize — Fix duplicate `_token_re`; the winning definition omits pre-reform characters
  - `ocr_service.py:40` vs `:100`, plus a third inline regex at `:518`. Three disagreeing Cyrillic charsets in one file.
  - Verify: a test asserting ѣ і ѳ ѵ tokenize as word characters

- [ ] **T6 (P1, human: ~30m / CC: ~5m)** — recognize — Fix confidence using `min(model_scores)` instead of the chosen hypothesis
  - `ocr_service.py:269`. Every reported confidence value is currently wrong.
  - Verify: a test where the best hypothesis is not the lowest-scoring one

- [ ] **T8 (P1, human: ~1h / CC: ~10m)** — jobs — Stop inserting NULL `transcript_path` on OCR failure
  - `documents.py:63-64` passes `(None, -1)` into a `nullable=False` column (`models/file.py:25`). `IntegrityError` inside a background task, silently.
  - Verify: an integration test that forces an OCR failure and asserts a clean failed state in the DB

- [ ] **T17 (P1, human: ~5m / CC: ~2m)** — api — Remove the duplicate `corrections.router` registration
  - `api.py:8-9` registers it twice.
  - Verify: route count in the OpenAPI schema drops by the duplicated set

- [ ] **T35 (P1, human: ~1h / CC: ~5m)** — preprocess — **REGRESSION FIX**: deskew must run before the page split
  - `ocr_service.py:302-305` currently splits then dewarps.
  - **Mandatory regression test** (no question, per the review's regression rule): a deliberately rotated two-page spread must split at the true gutter, not at `w // 2` of the un-rotated image.

- [ ] **T26 (P2, human: ~2h / CC: ~10m)** — cleanup — Delete dead code
  - `process_document_mock` (empty `pass`), `DEWARPNET_*` (read once, never used), the `inspect.getargspec` monkey-patch (only for mmcv, not installed), duplicate `import re`, duplicate `FileCreate` import, duplicate `scikit-image`/`tqdm` in requirements

- [ ] **T14b (P1, human: ~4h / CC: ~15m)** — postprocess — Delete **all** `.docx` parsing; define `PRE_REFORM_CHARSET` as a constant
  - `load_alphabet_from_docx`, `load_fund_glossary`, `_parse_pairs_from_text`, `AlphabetRules` — roughly 120 lines
  - Surfaced by: the parser extracts garbage mappings (`ъ→П`, `Я→К`, `а→т`); enabling it corrupts transcripts
  - **Do not "fix" this code. Delete it.**

- [ ] **E9 (P1, human: ~2h / CC: ~10m)** — deps — Pin exact versions for all 19 backend deps and every new one
  - 0 of 19 currently pinned. `front/requirements.txt` already pins 3, so the convention exists.
  - Verify: `grep -c "==" backend/requirements.txt` equals the dependency count

- [ ] **E10 (P1, human: ~1w / CC: ~1h)** — tests — pytest scaffold targeting the 31 coverage gaps
  - Verify: `pytest` runs green; coverage report exists

- [ ] **E18 (P2, human: ~2h / CC: ~10m)** — quality — Add `ruff` and `pre-commit` config
  - No `pyproject.toml`, `setup.cfg`, `.pre-commit-config.yaml`, `ruff.toml` or `.flake8` exists anywhere

- [ ] **E20 (P3, human: ~1h / CC: ~15m)** — repo — Remaining hygiene: `.git` is 790MB, and `.gitignore:210` excludes `.jpg` which blocks committing eval fixtures
  - Both are tied to the E1 image-storage decision (LFS, DVC manifest, or out-of-band bundle). Resolve them together.

---

## Phase 1 — Benchmark, then decide

**Goal:** replace the build-vs-adopt argument with a number.
**Blocked by:** E1, E4, E5.

- [ ] **E12 / T33 (P1, human: ~3d / CC: ~45m)** — benchmark — Benchmark with a **pre-committed numeric threshold**
  - Surfaced by: outside voice — "benchmark then decide" without a written number reliably becomes "we already started building"
  - Candidates: Kraken/eScriptorium, **Transkribus**, PaddleOCR, Surya, TrOCR-large, current TrOCR baseline
  - **Write the threshold before running anything.** Example shape: *"if any off-the-shelf engine reaches CER < X on the ground-truth set with fewer than Y hours of fine-tuning, we adopt and stop building recognition."*
  - Files: `scripts/benchmark_baselines.py`, `eval/results.md`
  - Verify: every candidate has a CER on the same ground-truth set, recorded in the committed results file

### ◆ GATE — build vs adopt

Do not start Phase 2 recognition work until this gate is answered against the
threshold written above. Record the outcome in `DESIGN.md` as a new decision row.

---

## Phase 2 — Layout

**Goal:** stop merging table columns into one crop.
**Blocked by:** E1 (~20 sourced pages), E8 (schema).

- [ ] **E8 (P1, human: ~4h / CC: ~20m)** — schema — Add `region_type`, `row`, `col`, `parent_region_id` as Optional on `TranscriptData`, via Alembic
  - `schemas/document.py:22-27` is flat and discards the structure layout recovers
  - **Must land before E6/E7 can store anything useful**
  - Verify: an old transcript JSON still parses; a new one carries `(row, col)`

- [ ] **T10 (P1, human: ~2d / CC: ~30m)** — db — Introduce Alembic; add `transcript_id` FK + bbox to `FileCorrection`
  - `Base.metadata.create_all` (`db/init_db.py:7`) creates missing tables but never alters existing ones
  - Verify: upgrade → downgrade → upgrade round-trips on a populated database

- [ ] **E6 (P1, human: ~2d / CC: ~20m)** — layout — Port `cv_detect` / `find_cells` into `pipeline/layout.py`; delete the other two duplicate copies
  - `cv_detect` from `dataset_preparation.ipynb` is canonical (`max_w=4000`, `max_h=2000`, has the merged-cell heuristic). The `layout_detection.ipynb` copy uses `max_w=2000`, `max_h=1000` and no merged-cell handling — a 2x parameter drift.
  - Verify: layout metric produces IoU and reading-order numbers on the sourced pages

- [ ] **E7 (P1, human: ~2d / CC: ~30m)** — contract — Emit PAGE XML from the layout stage
  - Reverses the earlier bespoke-contract decision. Kraken, eScriptorium and Transkribus already consume it.
  - Verify: a coordinate-space round-trip test (pixels → PAGE XML → pixels) is lossless

- [ ] **T2 (P1, human: ~1d / CC: ~20m)** — preprocess — Port deskew/find_spine/CLAHE into **one shared** `pipeline/preprocess.py`
  - The two notebook copies are verbatim duplicates. Shared-by-training-and-serving is the train/serve skew guard, not a style preference.

- [ ] **T3 (P1, human: ~2h / CC: ~10m)** — preprocess — Replace `split_double_page`'s `w // 2` with `find_spine`

- [ ] **T1 (P1, human: ~1d / CC: ~20m)** — pipeline — Split `ocr_service.py` into `pipeline/{preprocess,layout,recognize,postprocess}.py`
  - Add ASCII pipeline diagrams to each module's docstring per project convention

- [ ] **E15 (P2, human: ~1d / CC: ~20m)** — perf — Batch inference must land **with** cell detection, not after
  - `ocr_service.py:343` is per-unit with 5-beam search. Cell detection raises ~40 units/page to ~100, so Phase 2 would otherwise ship measurably slower than today.

- [ ] **E17 (P2, human: ~4h / CC: ~20m)** — perf — Stream pages instead of accumulating `all_page_lines`; index `file_transcripts.file_id` and `file_corrections.file_id`
  - `ocr_service.py:301-311` holds ~2.6GB resident for a 50-page PDF, worse under cell detection. Postgres does not index FKs.

- [ ] **E19 (P2, human: ~15m / CC: ~5m)** — jobs — Declare the ordering dependency: the DB progress column is a migration, so **T7b cannot precede T10**

- [ ] **T7b (P1, human: ~2h / CC: ~10m)** — jobs — Fresh `SessionLocal()` inside the background task; progress in a DB column
  - Replaces the Celery migration. `documents.py:70,79` hands a request-scoped session to a task that outlives the request; `progress_status` is a module dict that breaks with >1 worker.

- [ ] **T9 (P1, human: ~1d / CC: ~20m)** — errors — Replace catch-all handlers with named exceptions and structured context
  - `except Exception: pass` twice nested at `ocr_service.py:130-136`; one catch-all wraps all of `process_document` at `:379`

- [ ] **T19 (P1, human: ~1d / CC: ~20m)** — observability — Structured logging with `job_id` and `file_id`; replace `print()`

- [ ] **T20b (P2, human: ~2h / CC: ~10m)** — observability — Log experiment runs to a CSV + git tag; stamp `model_version` and `pipeline_version` into transcript output

---

## Phase 3 — Recognition

**Goal:** better characters, on data that actually exists.
**Blocked by:** E3 (tokenizer must pass), Phase 1 gate, Digital Peter acquired.

- [ ] **T36 (P1, human: ~4h / CC: ~20m)** — training — Verify at least one handwriting font renders ѣ ѳ і ѵ rather than `.notdef`
  - **Can fail on day one with no fallback identified.** Run early.
  - Verify: a test asserting non-`.notdef` glyph coverage for the full charset in every configured font

- [ ] **E13 (P1, human: ~2h / CC: ~10m)** — charset — Charset must include uppercase, digits, abbreviation and ditto marks
  - Surfaced by: outside voice — "~37 chars" was lowercase-only; parish registers are wall-to-wall proper nouns and place names

- [ ] **T37 (P2, human: ~3d / CC: ~30m)** — corpus — Source a domain corpus: Moscow-guberniya toponyms + Orthodox name-day gazetteer
  - A general pre-reform literary corpus buys much less; these documents are names, patronymics, villages and dates
  - ⚠️ If the decoding lexicon and the synthetic training text come from the same templates, eval looks great and generalization is zero. Keep them separate.

- [ ] **E14 / T12 (P2, human: ~1d / CC: ~30m)** — synth — Configure `trdg` or SynthTIGER; pre-render a fixed seeded set
  - Gitignored output directory; commit only seed, config hash, counts and ~12 sample images
  - Start at ~50k lines and **measure before scaling**
  - Do **not** hand-write a generator

- [ ] **T13 (P1, human: ~1w / CC: ~2h)** — recognize — Fine-tune, then the CTC head swap ⚠️
  - **Recorded dissent (D-19):** two reviewers recommended gating this behind a measured trigger. Swapping TrOCR's decoder discards the pretrained decoder. Fine-tune the existing decoder first and measure; only then swap.
  - Verify: CER improves against the Phase 0 baseline in the committed results file

- [ ] **E16 (P2, human: ~1d / CC: ~20m)** — perf — SymSpell or BK-tree index before the real corpus lands
  - `_autocorrect_token` (`ocr_service.py:508-512`) linear-scans the vocabulary computing a DP edit distance per token. Invisible at 179 words, dominant at 50,000.

---

## Phase 4 — Flywheel (deferred until there are users)

- [ ] **T11 (P1 when unblocked, human: ~2d / CC: ~30m)** — training — `export_pairs.py`: corrections → labeled line crops via stored coordinates
  - ⚠️ **Do not run before T10.** Exporting against unstable `fragment_id` poisons the training set undetectably.

- [ ] **T15_DEFER (P3, human: ~1d / CC: ~20m)** — security — Corrections auth + `reviewed` flag + outlier filter
  - **Required before T11 goes live.** Unauthenticated corrections becoming training data is a model-poisoning path.

- [ ] **T16 (P1, human: ~2h / CC: ~10m)** — security — Upload size cap + magic-byte validation
  - `documents.py:43` uses unbounded `shutil.copyfileobj`; `:31` validates by extension only

- [ ] **T18 (P1, human: ~2h / CC: ~10m)** — jobs — Idempotency guard on `POST /process`
  - Double-click spawns duplicate jobs and duplicate transcript rows; `get_transcript_by_file_id` uses `.first()` and picks arbitrarily

- [ ] **T7_DEFER (P3)** — jobs — Full Celery/RQ + Redis, when concurrent users exist
- [ ] **T30 (P3)** — reports — Replace or remove the mocked `/reports/generate` (`reports.py:24-27` returns hardcoded fake people)

---

## Test coverage targets

Current coverage: **0%**. No `tests/`, no `pytest.ini`, no CI.

```
CODE PATHS                                       USER FLOWS
[+] pipeline/preprocess.py                       [+] Upload → process → view
  ├── deskew()                                     ├── [GAP][→E2E] happy path
  │   ├── [GAP] Hough finds no lines → 0.0         ├── [GAP][→E2E] double-click /process
  │   ├── [GAP] angle beyond max_angle             ├── [GAP] navigate away mid-job
  │   └── [GAP] non-square aspect distortion       └── [GAP] server restart mid-job
  ├── find_spine()
  │   ├── [GAP] no dark strip → w//2 fallback    [+] Correction → training pair
  │   ├── [GAP] strip narrower than min_width      ├── [GAP] correction on stale transcript
  │   └── [GAP] spine at x=0 → empty left page     ├── [GAP] empty corrected_text
  └── clahe()                                      └── [GAP][→E2E] export after re-process
      └── [GAP] already-normalized input
                                                 [+] Error states
[+] pipeline/layout.py                             ├── [GAP] corrupt image upload
  ├── cv_detect()                                  ├── [GAP] CUDA OOM
  │   ├── [GAP] zero detections on blank page      ├── [GAP] disk full on write
  │   ├── [GAP] faded / broken rule lines          └── [GAP] job failed → what user sees
  │   └── [GAP] reading-order assignment
  └── to_page_xml()
      └── [GAP] coord-space round trip

[+] pipeline/recognize.py                        [+] alembic
  ├── predict_batch()                              └── [GAP] up→down→up on populated DB
  │   ├── [GAP] empty batch
  │   ├── [GAP] zero-area crop (x1<=x0)          [+] eval
  │   └── [GAP] CTC collapses to ""  ←silent       ├── [GAP] IoU + reading order
  └── adapters (TrOCR | Kraken)                    └── [GAP] CER/WER on known pairs
      └── [GAP] engine-swap parity

[+] pipeline/postprocess.py                      [+] training
  └── constrained_decode()                         ├── [GAP][→E2E] stale fragment_id
      ├── [GAP] char outside charset               │        must be REFUSED  ←CRITICAL
      └── [GAP] empty vocabulary                   └── [GAP] font missing ѣѳіѵ ←CRITICAL

COVERAGE: 0/31 (0%)  |  GAPS: 31 (5 E2E)
```

### The three tests that carry the plan

1. **`export_pairs` refuses a stale correction** `[→E2E]` — submit a correction,
   re-process the file, assert the export refuses or re-anchors rather than emitting
   a mislabeled pair. This should fail against today's code.
2. **Font glyph coverage** — assert every `PRE_REFORM_CHARSET` character renders to a
   non-`.notdef` glyph in every configured font. Turns a day-one surprise into a
   one-line failure.
3. **Engine-swap parity** — the same PAGE XML into both adapters returns the same
   shape. This is what makes the Phase 1 benchmark trustworthy.

---

## Failure modes

```
 CODEPATH              | FAILURE MODE                  |TEST?|HANDLED?|USER SEES
 ----------------------|-------------------------------|-----|--------|-------------
 tokenizer             | ѣ ѳ і ѵ map to <unk>          | E3  | N/A    | caps CER silently ←CRIT
 find_spine            | no dark strip → w//2 fallback | E4  | Y      | wrong page split
 page split            | text crosses the cut          | E4  | N      | truncated lines ←CRIT
 cv_detect             | faded / broken rule lines     | E4  | N      | missing cells ←CRIT
 PAGE XML emit         | coord-space round-trip drift  | E10 | N      | boxes off by scale
 recognize (batched)   | zero-area crop                | E10 | N      | crash or empty
 recognize (CTC)       | collapse to ""                | E10 | N      | fewer lines ←CRIT
 postprocess           | char outside charset          | E10 | N      | dropped chars
 export_pairs          | stale fragment_id             | E10 | Y(T10) | poisoned labels ←CRIT
 synth_gen             | font renders .notdef          | T36 | N      | trains on boxes ←CRIT
 eval                  | non-reproducible across hosts | E11 | Y(E11) | phantom regressions
 background job        | NOT NULL on failure           | E10 | Y(T8)  | silent job death
 ----------------------|-------------------------------|-----|--------|-------------
 6 CRITICAL GAPS — all have owning tasks
```

---

## Parallel execution (git worktrees)

| Lane | Tasks | Modules | Depends on |
|---|---|---|---|
| **A** | E1 | `backend/data/`, `.gitignore` | — (external, blocks F, G) |
| **B** | T5, T6, T8, T17, T26, T14b, E9, E18, E20 | `backend/services/`, config | — |
| **C** | E3 | `pipeline/recognize.py` | — (10 min, run first) |
| **D** | E5 | `docs/` | — |
| **E** | E8, T10 | `models/`, `schemas/`, `alembic/` | — (must precede F) |
| **F** | E6, E7, T2, T3, T1, T35 | `pipeline/` | E, A |
| **G** | E4, E11 | `scripts/`, `Makefile` | A, D |

**Launch A, B, C, D, E in parallel** — five worktrees, no shared modules. Then **F**
after E and A. Then **G** after A and D.

**Conflict flags:**
- Lanes **B and F both touch `backend/services/`**. B edits `ocr_service.py`, F creates
  `pipeline/` and deletes from it. Sequence B before F, or accept a merge on the
  deleted-code boundary.
- Lanes **E and F** both touch schema-adjacent code. E must land first.
- **Lane C is ten minutes and can invalidate Lane F's downstream work.** Run it first.

---

## Definition of done for this plan

- [ ] `make eval` produces a CER and a layout score on a real ground-truth set
- [ ] The committed results file shows a measured improvement over the Phase 0 baseline
- [ ] `pytest` green, with all 6 critical failure modes covered
- [ ] No `except Exception` without a named cause in the pipeline
- [ ] Every dependency pinned
- [ ] `ocr_service.py` no longer exists as a monolith
- [ ] A new contributor can read `CLAUDE.md` + `DESIGN.md` and ship a small change
      without asking anything
