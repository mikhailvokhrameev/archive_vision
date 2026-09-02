# CLAUDE.md — Archive Vision

Project instructions for Claude Code. Read this before touching anything.

---

## What this project is

A web service that transcribes scanned Russian archival documents, specifically
**pre-1918 handwritten church records from Moscow archive Fund 203** (Московская
духовная консистория): parish birth, marriage and death registers, and confession
books, 1680-1929.

These documents are **ruled multi-column tables** written in pre-reform Russian
cursive. That single fact drives most architecture decisions here. See
[docs/DESIGN.md](docs/DESIGN.md).

Stack: FastAPI + SQLAlchemy + Postgres backend, Streamlit frontend, TrOCR for
recognition, OpenCV for preprocessing and layout.

The README frames this as a learning and portfolio project. Treat "we can explain
and defend every part of this" as a real goal alongside "it works."

---

## ⛔ Read this before planning any ML work

**The training corpus does not exist.** `backend/data/uploads/` contains 27 JPEG
files that are all byte-identical: one image uploaded 27 times through the API,
each receiving a fresh UUID filename.

```
27 files → md5 02146e7b36dc9d28b7dccc9ccc17f3e2 (all)
27 files → 4,188,309 bytes (all)
27 files → 5282 × 4458 px (all)
```

Any task that assumes training or evaluation data is **blocked** until `E1` in
[docs/PLAN.md](docs/PLAN.md) completes. Do not write code that silently assumes a
corpus. Do not generate a "sample dataset" to work around this.

Related: `.gitignore:210` excludes `.jpg`, so no image is tracked anywhere, and
`.git` is already 790MB. Image storage is an open decision, not a detail.

---

## Non-negotiable constraints

1. **Do not touch the frontend.** `front/` is out of scope by explicit user
   instruction. Do not edit, refactor, or "improve" it.
2. **Do not restore or apply the git stashes.** Three stashes hold ~107MB of model
   weights and six parallel OCR implementations. The user decided to leave them.
   Do not `git stash pop`, `apply`, or `drop`.
3. **The `.docx` files are gone by decision.** `Alphabet.docx` and `F203.docx` are
   not to be used. Do not re-add the parsing code. See "Known traps" below.
4. **Never `git add -A`.** Stage intentional files only. `.DS_Store` files are
   already tracked by mistake; do not add more.

---

## Known traps (verified, with line numbers)

These are real bugs in `backend/services/ocr_service.py` and friends. Several look
like dead code but are actively harmful.

| Location | Trap |
|---|---|
| `ocr_service.py:40` and `:100` | `_token_re` is defined **twice** with different alphabets. The second wins and omits pre-reform characters (ѣ і ѳ ѵ). A third, different Cyrillic regex is inline at `:518`. |
| `ocr_service.py:236` | The projection-profile fallback emits boxes spanning `x=0` to `image.width`. On a multi-column table every "line" crop contains **all columns merged**. This is the layout bottleneck. |
| `ocr_service.py:269` | `confidence` uses `min(model_scores)` instead of the score of the chosen hypothesis. Every confidence value reported to users is wrong. |
| `ocr_service.py:302-305` | `split_double_page()` runs **before** `dewarp_image()`. Deskew must come first. |
| `ocr_service.py:130-136` | `except Exception: pass`, nested twice. Silently degrades DBNet to a projection guess. |
| `ocr_service.py:379` | One catch-all wraps the entire `process_document` body. |
| `ocr_service.py:366-368` | `wer=0.0` and `extracted_attributes={}` are hardcoded constants presented as results. |
| `documents.py:63-64` + `models/file.py:25` | On OCR failure `process_document` returns `(None, -1)`, which is then inserted into a `nullable=False` column. `IntegrityError` inside a background task, silently. |
| `documents.py:70,79` | A request-scoped DB session from `Depends(get_db)` is handed to a `BackgroundTask` that outlives the request. |
| `api.py:8-9` | `corrections.router` is registered **twice**. |
| `reports.py:24-27` | `/reports/generate` returns two hardcoded fake people regardless of input. |
| **`.docx` parsing** (`ocr_service.py:402-525`) | Looks dormant (env vars unset) but is **broken, not dormant**. `Alphabet.docx` has 0 tables and its alphabet chart is an embedded image; the pair regex extracts garbage like `ъ→П`, `Я→К`, `а→т`. Enabling it corrupts transcripts. **Delete it, don't fix it.** |

---

## Conventions

**Language.** Code, comments and docs in English. User-facing strings stay Russian.
Existing comments are mixed Russian/English; new code is English.

**Dependencies.** Pin exact versions in `backend/requirements.txt`. `front/requirements.txt`
already pins; the backend does not, and that is being fixed. Do not add an
unpinned dependency.

**Diagrams.** ASCII diagrams belong in code comments for anything non-obvious:
pipeline stages in Services, state transitions in Models, request flow in
Controllers, non-obvious setup in Tests. If you change code near a diagram, update
the diagram in the same commit. Stale diagrams are worse than none.

**Error handling.** No catch-all `except Exception`. Name the exception, log the
context (what was attempted, with what arguments, for which job and file), and
either retry with backoff, degrade with a user-visible message, or re-raise with
added context. "Swallow and continue" is not acceptable in this codebase; it is
how "layout detection is bad" stayed invisible for a year.

**Logging.** Structured, with `job_id` and `file_id` on every line. Replace `print()`.

**Tests.** pytest. Every new branch and error path gets a test. See the coverage
diagram in [docs/PLAN.md](docs/PLAN.md).

---

## Testing

```bash
pytest                    # unit + integration
make eval                 # CER/WER + layout metrics against ground truth
```

`make eval` writes a **committed** results file so accuracy changes appear in the
diff. It pins seeds and records torch/CUDA/device, because beam search is not
bit-reproducible across machines and two contributors on different hardware would
otherwise see phantom regressions.

There is no CI. That is deliberate for now (see `TODOS.md`).

---

## Architecture in one diagram

```
   sourced pages                    Digital Peter (9,694 annotated lines)
        │                                      │
        ▼                                      ▼
  pipeline/preprocess.py  ◄── SHARED ──►  training/
    deskew → find_spine → clahe           (synth + fine-tune)
    (ORDER MATTERS: deskew first)              │
        │                                      │
        ▼                                      │
  pipeline/layout.py                           │
    cv_detect / find_cells (classical)         │
    emits ──▶ PAGE XML                         │
        │                                      │
        ▼                                      ▼
  pipeline/recognize.py ── adapters ──▶ TrOCR | Kraken | Transkribus
    batched inference
        │
        ▼
  pipeline/postprocess.py   charset-constrained decode + SymSpell vocab
        │
        ▼
  TranscriptData{ text, coords, confidence, region_type, row, col, parent_region_id }
```

`preprocess.py` being shared by training and serving is not a style preference. It
is the guard against train/serve skew, which is the top technical risk in this
project.

---

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool.
When in doubt, invoke the skill.

- Product ideas / brainstorming → `/office-hours`
- Strategy / scope → `/plan-ceo-review`
- Architecture → `/plan-eng-review`
- Design system / plan review → `/design-consultation` or `/plan-design-review`
- Full review pipeline → `/autoplan`
- Bugs / errors → `/investigate`
- QA / testing site behavior → `/qa` or `/qa-only`
- Code review / diff check → `/review`
- Visual polish → `/design-review`
- Ship / deploy / PR → `/ship` or `/land-and-deploy`
- Save progress → `/context-save`
- Resume context → `/context-restore`
- Author a backlog-ready spec/issue → `/spec`

---

## Where things are

| Path | What |
|---|---|
| [docs/DESIGN.md](docs/DESIGN.md) | Architecture, decisions and their rationale |
| [docs/PLAN.md](docs/PLAN.md) | Phased implementation plan with verification steps |
| [TODOS.md](TODOS.md) | Deferred work with enough context to pick up cold |
| `backend/services/ocr_service.py` | The 525-line monolith being split into `pipeline/` |
| `new_code/` | Your collaborator's notebooks: preprocessing and layout prototypes |
