# TODOS

Deferred work, with enough context to pick up cold in three months.

Active work lives in [docs/PLAN.md](docs/PLAN.md). This file is for things
deliberately *not* being done now. Each entry records why it was deferred, so the
decision can be revisited rather than rediscovered.

---

## P1 — Do these when their trigger fires

### Corrections auth + review gate + outlier filter
**Trigger:** before `T11` (`export_pairs`) ever runs against real corrections.

**What:** Authentication on `POST /documents/correction/{file_id}`, a `reviewed`
boolean gating a correction into the training export, and an edit-distance outlier
filter that rejects corrections wildly divergent from the OCR output.

**Why:** The plan turns an unauthenticated endpoint into a training-data input.
Anyone who can reach the service could inject arbitrary text into the training set,
undetectably. This path does not exist today only because nothing reads
`FileCorrection`.

**Deferred because:** `FileCorrection` has zero rows and the app has zero users.
Defending training data that does not exist yet is premature. But it becomes P0 the
moment the flywheel is switched on.

**Depends on:** nothing. **Blocks:** `T11` going live.

---

### Application-wide authentication
**Trigger:** before the service is reachable from anything but localhost.

**What:** Auth on every endpoint, per-user document scoping, rate limiting on
`/upload` and `/process`.

**Why:** Today anyone who can reach the service can upload files with no size cap,
start GPU jobs, and read every document and transcript in the system. `/process`
unauthenticated is a compute-exhaustion vector.

**Deferred because:** the review scoped security to what the plan itself creates
(D-16). This is a pre-existing gap, recorded rather than fixed.

**Context:** `docker-compose.prod.yml` also publishes Postgres on 5432 with
`postgres/postgres` credentials. If that file is what actually gets deployed, that
is the more urgent half of this item.

---

## P2 — Worth doing, no urgent trigger

### Full Celery / RQ + Redis migration
**What:** Move OCR and any training jobs to a worker process with Redis-backed
progress, bounded GPU concurrency, retries and job history.

**Why:** `BackgroundTasks` runs OCR inside the API process on the GPU, so one job
blocks the event loop. Progress lives in a module-level dict, which breaks
permanently with more than one uvicorn worker.

**Deferred because:** D-11 — zero users, single concurrency. The two *real* bugs (a
request-scoped session handed to a task that outlives it, and the module dict) are
fixed in `T7b` with roughly 30 lines. A distributed queue for a single-user service
is unearned complexity.

**Revisit when:** concurrent users exist, or training jobs start running inside the
web process.

---

### CI and an automated CER regression gate
**What:** GitHub Actions running pytest on every push, plus the eval harness as a
gate on a schedule or on demand.

**Why:** `make eval` with a committed results file makes regressions visible in
review, but nothing enforces that anyone runs it.

**Deferred because:** D-13 — no `.github` exists, TrOCR weights are ~1.4GB, and CPU
inference over the ground-truth set would take 30+ minutes per run. That is the kind
of gate that gets disabled within a week, leaving neither the gate nor the time
spent building it.

**Revisit when:** the eval numbers are stable and someone actually wants
enforcement. Start with lint and unit tests only; add the eval gate last, on a
schedule rather than per-push.

---

### Model weight publish pipeline
**What:** Weights to object storage or git-LFS, versioned, downloaded at worker
startup, checksum-verified at load.

**Why:** After three fine-tuning rounds you will not be able to say which model
produced which transcript. `T20b` stamps `model_version` into output, which is the
minimum; this is the rest.

**Deferred because:** storage-only was judged enough for now.

**Related:** the three git stashes hold a 59MB DBNet checkpoint and a 47MB zip that
exist nowhere else (see below).

---

### Populate `extracted_attributes`
**What:** Extract structured fields (ФИО, dates, village, parish) from recognized
cells into `RecognitionResult.extracted_attributes`, which is currently always `{}`.

**Why:** This is what turns transcripts into a queryable register, and it is what
`/reports/generate` would need to stop being mocked.

**Deferred because:** unblocked by D-08 (the schema now carries `row`/`col`), but
implementing extraction is separate scope.

**Depends on:** `E8` (region structure in the schema), `E6` (layout producing
reliable `(row, col)`).

---

### Replace or remove the mocked `/reports/generate`
**What:** `reports.py:24-27` returns two hardcoded fake people regardless of input.

**Why:** A user-facing endpoint that fabricates plausible-looking archival records is
worse than a missing one.

**Deferred because:** P3 in the review; nothing depends on it.

**Recommendation:** remove it until `extracted_attributes` is real, rather than
leaving fake data reachable.

---

## P3 — Recorded risks, no action planned

### The three git stashes
**What:** `stash@{0..2}` hold ~107MB of model weights (a 59MB DBNet checkpoint, a
47MB zip), six parallel OCR implementations, and `Alphabet.docx` / `F203.docx`.

**Why it matters:** Stashes never sync to a remote. A `git stash clear`, a bad pop,
or a dead disk erases them. They are 11 months old and exist on one machine.

**Deferred because:** D-17 — the user chose to leave them. The `.docx` files turned
out to be worthless (D-15), and the five superseded OCR variants are exactly what
the pipeline refactor replaces.

**Residual risk accepted:** the DBNet checkpoint is the only irreplaceable item, and
the reduced plan does not use it.

---

### Repo hygiene
**Remaining:**
- `.git` is 790MB
- `.gitignore:210` excludes `.jpg`, so no scan can be committed — this collides with
  the committed-eval-fixtures idea and needs an LFS or manifest decision (`E1`)

**Cleared 2026-09-02:** `.DS_Store` files removed repo-wide (two were tracked),
`__pycache__` and 45 `.pyc` files cleared, `pres.py` deleted, stray
`temp_00000015.jpg` gone, and the duplicate uploads purged.

---

### GPU / environment parity
**What:** `backend/Dockerfile:18` installs CUDA 12.8 torch, but `docker-compose.yml`
declares no `deploy.resources` or nvidia runtime. On a CPU-only machine the stack
silently falls back to CPU and runs roughly 50x slower, which presents as "the OCR
hung."

**Open question:** where does training compute come from at all? No GPU is
configured anywhere in the repo, and Phase 3 assumes fine-tuning.

---

## Open questions blocking planning

1. **Who can read pre-reform Russian cursive?** Ground-truth transcription is skilled
   paleography, plausibly 20-40 hours for 25 pages. If neither contributor can do it,
   the eval harness is unbuildable and the plan needs a different shape. Nobody has
   answered this.
2. **Is the "HTR for Russian Empire Period Manuscripts" dataset real and usable?**
   ([OpenReview](https://openreview.net/pdf/8fc2738629b918329dae9d7765f7d31e9cdb2dc7.pdf))
   Behind a login wall, unverified, and a closer orthographic match than Digital
   Peter if it delivers. ~20 minutes to check.
3. **Are cgamos.ru scans redistributable?** The plan involves committing eval
   fixtures. Licensing was never checked.
