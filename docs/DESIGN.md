# Archive Vision — Design Document

**Status:** ACTIVE
**Branch:** `dev`
**Date:** 2026-09-02
**Produced by:** `/plan-ceo-review` (HOLD_SCOPE) then `/plan-eng-review` (SCOPE_REDUCED),
each with an independent outside-voice challenge.

---

## 1. Problem statement

Archive Vision transcribes scanned pre-1918 Russian handwritten church records from
Moscow archive Fund 203 into searchable text. Today it does this badly: layout
detection merges table columns, recognition quality is poor, and no part of the
system measures its own accuracy.

The stated complaint was "OCR is bad, layout detection is bad." The review found
the deeper problem underneath it.

### The real problem

**There was no way to tell whether any change made anything better.**

`RecognitionResult(wer=0.0)` is a hardcoded constant (`ocr_service.py:366`). No
ground-truth set exists. No CER or WER is ever computed. The `wer` column in the
database is populated from that constant.

What that produced is visible in the repository: **six parallel OCR
implementations** (`ocr.py`, `ocr_service.py`, `ocr_service (2).py`,
`ocr_service_easy.py`, `ocr_service_old.py`, `ocr_service_oldold.py`), cycling
through DBNet → EasyOCR → PaddleOCR, five of them stranded in unpushed local git
stashes, none of them measured against anything. That is the signature of iterating
blind. Swapping in engine number seven produces a seventh opinion, not a better
product.

### The second real problem

**The corpus does not exist.** `backend/data/uploads/` holds 27 JPEG files that are
byte-identical to each other — a single page uploaded 27 times through the API,
each upload receiving a fresh UUID filename.

```
27 files → 1 unique md5 (02146e7b36dc9d28b7dccc9ccc17f3e2)
27 files → 1 unique size (4,188,309 bytes)
27 files → 1 unique dimension (5282 × 4458)
```

Every phase of work beyond bug-fixing depends on data that has to be acquired
first. No task in the original plan owned this.

---

## 2. Domain constraints that drive the architecture

**These are ruled multi-column tables, not free prose.** Fund 203 metric books
(метрические книги) and confession books (исповедные ведомости) are pre-printed
forms with drawn rule lines. Entries are formulaic:

```
[дата] родился [имя] у [отецъ] и законной жены его [мать], деревни [село], [приходъ] церкви
```

Three consequences run through every decision below:

1. **Layout is geometric, not semantic.** The page has literal drawn lines. Classical
   morphology reads those lines directly. This is why we do not train a detector.
2. **Recognition needs the cell, not the line.** The product is "the mother's name
   in row 7," so table structure must survive to the output schema.
3. **Synthetic data is unusually tractable.** Formulaic text templates well, which
   is what makes the recognition track viable despite a tiny real corpus.

**Orthography.** Pre-reform Russian: ѣ (ять), і (и десятеричное), ѳ (фита),
ѵ (ижица), and terminal ъ after consonants. The character set must include
uppercase (these documents are wall-to-wall proper nouns and place names), digits,
abbreviation marks and ditto marks — not just 37 lowercase letters.

---

## 3. Prior art consulted

**T-Bank production OCR/HTR** ([habr.com/ru/companies/tbank/articles/885558](https://habr.com/ru/companies/tbank/articles/885558/)).
Two-stage architecture: small detector (DbNet++, ~8-10M params) then a line
recognizer. They replaced TrOCR's autoregressive decoder with a CTC head for
speed, calibrated confidence and constrainable decoding. Headline lesson: *below
~200M parameters, data quality dominates architecture choice.* Their LineOCR
trained on ~6.9M lines including 5M synthetic. They report table extraction as
still unsolved.

**Kraken / eScriptorium** ([kraken.re](https://kraken.re/main/index.html)).
Open-source HTR for historical documents. Recognition engine is CNN + BiLSTM +
CTC. Model repository on Zenodo. No ready-made pre-reform Cyrillic model was
found, so adopting Kraken would mean fine-tuning it, not installing it.

**YALTAi** ([arXiv 2207.11230](https://arxiv.org/pdf/2207.11230)). Object detection
replacing region segmentation inside Kraken. **Explicitly targets unruled
manuscript layout** where there is no printed geometry to exploit. This is why we
rejected it — see D-07.

**Digital Peter** ([arXiv 2103.09354](https://arxiv.org/pdf/2103.09354)). 9,694
annotated line images from Peter the Great's manuscripts (1709-1713), ~265,788
symbols, ~51,000 words, with 6,237/1,930/1,527 train/val/test splits. Baseline is
CNN + BiGRU + CTC.

**Synthetic generation:** [SynthTIGER](https://github.com/clovaai/synthtiger)
(ICDAR 2021) and [trdg](https://github.com/Belval/TextRecognitionDataGenerator),
both mature, both support non-Latin scripts.

---

## 4. Target architecture

```
  ~20 sourced Fund 203 pages          Digital Peter (9,694 annotated lines)
       (layout measurement)                (recognition training)
            │                                        │
            ▼                                        ▼
   ┌──────────────────────────────────────────────────────────┐
   │  backend/services/pipeline/preprocess.py                 │
   │    deskew()  →  find_spine()  →  clahe()                 │
   │    ORDER IS LOAD-BEARING: deskew must precede the split  │
   │    SHARED by training and serving — the skew guard       │
   └───────────────────────┬──────────────────────────────────┘
                           │
                           ▼
   ┌──────────────────────────────────────────────────────────┐
   │  backend/services/pipeline/layout.py                     │
   │    cv_detect() / find_cells()   [classical morphology]   │
   │    adaptive threshold → h/v line masks → intersections   │
   │    → contours → cells sorted into (row, col)             │
   │    emits ──▶ PAGE XML                                    │
   └───────────────────────┬──────────────────────────────────┘
                           │  PAGE XML (regions, reading order, table structure)
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
     TrOCR             Kraken            Transkribus
     adapter           adapter            adapter
        └──────────────────┼──────────────────┘
                           ▼
   ┌──────────────────────────────────────────────────────────┐
   │  backend/services/pipeline/recognize.py                  │
   │    BATCHED inference (not per-unit)                      │
   └───────────────────────┬──────────────────────────────────┘
                           ▼
   ┌──────────────────────────────────────────────────────────┐
   │  backend/services/pipeline/postprocess.py                │
   │    charset-constrained decode                            │
   │    SymSpell / BK-tree vocabulary index                   │
   └───────────────────────┬──────────────────────────────────┘
                           ▼
   TranscriptData{ text, coordinates, confidence,
                   region_type, row, col, parent_region_id,
                   model_version, pipeline_version }
                           │
        ┌──────────────────┴──────────────────┐
        ▼                                     ▼
   transcripts/*.json              FileCorrection
                                   (anchored to transcript_id + bbox)
                                           │
                                           ▼   [gated: auth + reviewed flag]
                                   training/export_pairs.py
```

### Measurement architecture

Two metrics, not one. A single page-level CER conflates layout errors with
recognition errors and cannot tell you which change helped.

```
  LAYOUT METRIC                        RECOGNITION METRIC
  detection IoU                        CER / WER via jiwer
  reading-order correctness            measured on MANUALLY CROPPED lines
  page-split pass/fail                 (decoupled from the segmenter, so it
  (correct page count, no text                survives preprocessing changes)
   crossing the cut)
```

The page-split check exists because the `w // 2` → spine-detection fix is the
change most likely to silently destroy everything downstream on a bound register
with a curved gutter, and a cell-level metric would not catch it.

---

## 5. Decision record

Each decision below was made explicitly by the user during review. Dissent is
recorded where reviewers disagreed.

| # | Decision | Rationale |
|---|---|---|
| **D-01** | **Measure before optimizing.** Build a two-metric eval harness before touching quality. | Six unmeasured OCR variants in eleven months. Without a number, change seven is change one again. |
| **D-02** | **Layout before recognition.** | Verified: `ocr_service.py:236` emits `x=0..image.width` crops, so on a ruled table every "line" contains all columns merged. No recognition improvement can exceed that ceiling. |
| **D-03** | **Classical morphology for layout. No learned detector.** | See D-07. |
| **D-04** | **PAGE XML as the region interchange format.** | Kraken, eScriptorium and Transkribus already speak it; it encodes regions, reading order and table structure. Reverses an earlier decision to build a bespoke contract. |
| **D-05** | **Assemble where mature libraries exist; build where they don't.** | `trdg`/SynthTIGER for synthesis, `jiwer` for CER/WER, Kraken as a CTC baseline. Complexity check triggered at 12 new modules against a threshold of 2. |
| **D-06** | **Benchmark off-the-shelf engines against a pre-committed numeric threshold before building recognition.** | "Benchmark then decide" without a written number reliably becomes "we already started building." |
| **D-07** | **Reject YOLO / YALTAi for layout.** | YALTAi targets *unruled* manuscript layout. Fund 203 pages have literal drawn rules that morphology reads directly. A detector trained on pseudo-labels generated by that same morphology can at best approximate it, minus annotation noise, and there is no corpus to train it on. Converts ~2 weeks into ~2 days. |
| **D-08** | **Add region structure to the output schema now** (`region_type`, `row`, `col`, `parent_region_id`, all Optional, via Alembic). | Without it the layout work produces prettier crops but no usable structure, and `extracted_attributes` stays empty forever. Cheap now while the table is effectively empty. |
| **D-09** | **Anchor corrections to `transcript_id` + bounding box before any training export.** | `fragment_id` is a per-run counter (`ocr_service.py:360`) reassigned on every re-processing. Exporting against it silently poisons the training set, undetectably and irreversibly. |
| **D-10** | **Introduce Alembic.** | `Base.metadata.create_all` creates missing tables but never alters existing ones. D-08 and D-09 are both migrations. |
| **D-11** | **No Celery yet.** Fix the two real bugs with a fresh `SessionLocal()` inside the task and progress in a DB column. | Zero users, single concurrency. A distributed queue for a single-user service is unearned complexity. Full Celery deferred. |
| **D-12** | **Pin every dependency version.** | 0 of 19 backend deps pinned, on a repo dormant 10 months. Unpinned deps make cross-time CER comparison meaningless, which defeats D-01. |
| **D-13** | **pytest now; `make eval` locally with a committed results file; CI deferred.** | No `.github` exists; 1.4GB weights plus CPU inference on free runners is the kind of gate that gets disabled within a week. Committed results make accuracy changes visible in review instead. |
| **D-14** | **Pre-render synthetic data as a fixed seeded set**, gitignored, with a committed manifest (seed, config hash, counts, ~12 samples). | Inspectable data is how font and realism problems get caught. Start ~50k lines and measure before scaling. |
| **D-15** | **Delete all `.docx` parsing.** Define the charset as a constant. | The parser produces garbage mappings (`ъ→П`, `Я→К`, `а→т`) and F203 yields 179 modern-orthography words. Enabling it corrupts output. User decision: drop the files entirely. |
| **D-16** | **Harden only what this plan creates**: auth on corrections, a `reviewed` flag gating training export, edit-distance outlier filtering, upload size cap, magic-byte validation. | The plan turns an unauthenticated endpoint into a training-data input, which is a model-poisoning path that did not previously exist. App-wide auth deferred. |
| **D-17** | **Leave the three git stashes alone.** | ~107MB of weights and six OCR variants. User decision. Note the residual risk in TODOS. |
| **D-18** | **Corpus: Digital Peter for recognition, ~20 sourced Fund 203 pages for layout measurement.** | Choosing D-03 dropped the layout data requirement from "hundreds of labeled pages to train" to "twenty pages to measure." |
| **D-19** | **Keep the CTC decoder swap in Phase 3.** ⚠️ | **Recorded dissent:** two independent reviewers recommended gating this behind a measured trigger. Swapping TrOCR's decoder for CTC discards the pretrained decoder, leaving a ViT encoder plus a randomly initialized head. T-Bank could afford that on 6.9M lines. The user chose to keep it deliberately. It sits in Phase 3, after the benchmark, so the decision is revisitable with data. |

---

## 6. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| **No corpus.** Everything past bug-fixing is blocked. | **Critical** | `E1` is the longest-lead task. Digital Peter unblocks recognition immediately; archive access for layout pages is external and uncontrolled. |
| **TrOCR tokenizer may lack ѣ ѳ і ѵ.** If they map to `<unk>`, no fine-tuning can make the model emit them. | **Critical** | `E3`: a 10-minute check that runs before any font or synthesis work. Caps the whole recognition track if it fails. |
| **Nobody may read 19th-century Russian cursive.** Ground-truth transcription is skilled paleography, plausibly 20-40 hours for 25 pages. | **High** | Unresolved. Identify who can do this before scheduling Phase 0. If neither contributor can, the eval harness is unbuildable and the plan needs a different shape. |
| **Train/serve skew.** Synthetic lines are clean; real inputs are CLAHE'd and deskewed. | High | `preprocess.py` shared by both paths; augmentation tuned against real preprocessed output; a golden-fixture test asserting distribution overlap. |
| **Handwriting fonts may not render ѣ ѳ і ѵ.** Most Cyrillic script fonts ship a modern charset. | High | Verify at least one usable font before committing to synthesis. Can fail on day one. |
| **Morphology degrades on faded or hand-drawn rules.** | Medium | This is exactly what the layout metric measures. Escalate to a learned detector only if the number says so. |
| **CTC retrain underperforms simple fine-tuning** (D-19). | Medium | Gated behind the Phase 1 benchmark; the previous checkpoint remains the rollback. |
| **Timeline.** Two independent reviewers estimated 3-4 months for the pre-reduction plan. | Medium | Scope reduction removed the learned detector, hand-built synthesis and CI. 5-6 weeks assumes data access goes smoothly. |

---

## 7. What is explicitly not in scope

| Deferred | Why |
|---|---|
| All frontend work | User instruction |
| YOLO / learned layout detector | D-07 |
| Full Celery + Redis | D-11; zero users |
| App-wide authentication | D-16; only the new path is hardened |
| CI and an automated CER gate | D-13 |
| Stash recovery | D-17 |
| The `.docx` files | D-15 |
| Experiment tracking system | CSV + git tag for 3-5 runs |
| Model weight publish pipeline | Storage only; checksum-at-load deferred |
| `extracted_attributes` population | Unblocked by D-08, but implementing extraction is separate scope |

---

## 8. Open questions

1. **Who can read pre-reform Russian cursive?** Ground truth is blocked on this and
   nobody has answered it.
2. **Does the "HTR for Russian Empire Period Manuscripts" dataset deliver what its
   abstract implies?** ([OpenReview](https://openreview.net/pdf/8fc2738629b918329dae9d7765f7d31e9cdb2dc7.pdf))
   It sits behind a login wall and was not verified. It is a closer orthographic
   match than Digital Peter if real. ~20 minutes to check.
3. **Are cgamos.ru scans redistributable?** Licensing was never checked, and the
   plan involves committing eval fixtures.
4. **Where does training compute come from?** No GPU is configured anywhere.
   `docker-compose.yml` declares no `deploy.resources` while the Dockerfile installs
   CUDA 12.8 torch.
