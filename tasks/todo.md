# Task: Extract ASME B31.3-2024 Appendices A, B, C to JSON

**Source:** `(local)\...\B31- PRESSURE PIPING\ASME B31.3 2024 Process Piping.pdf`
**Destination:** `C:\Users\User\Google Drive Streaming\My Drive\DANIEL\Cloude\ASME PCC\resources`
**Scope:** technical content only — no icons, trademarks, watermarks, front/back matter.

## Source facts established

- 594 pages, PDF 1.6, real embedded text layer (no OCR needed, no raster images on appendix pages).
- Appendix A = PDF idx 197–429, B = 430–437, C = 438–461 (0-based). 265 pages total.
- `page.find_tables()` is unusable here — tables are whitespace-aligned, not ruled. Custom
  positional extraction required.
- Big tables (A-1, A-1C, A-4, A-4C) are **two-page spreads**: a material-identification half
  and a stress-values half, joined by `Line No.`
- A-1 and A-1C carry **different** material-half column sets — columns must be derived per page
  from the actual header, never hardcoded.
- Table C-3 / C-3C pages are **landscape (rotation=90)**.
- Tables B-2/B-3 share a page with B-1C; B-4/B-5 share a page — multiple tables per page.
- `…` (U+2026) is ASME's explicit "no value" marker; `−` is U+2212 minus.
- `ð24Þ` is the (24) revision change-marker → strip (not technical content).

## Table inventory

| Table | idx range | pg | Content |
|---|---|---|---|
| Spec Index A | 198–201 | 4 | Spec. No. → Title |
| Notes A-1/A-1C | 202–204 | 3 | General Notes + numbered notes |
| A-1 | 206–315 | 110 | Basic Allowable Stresses in Tension for Metals — SI |
| A-1C | 316–395 | 80 | same — U.S. Customary |
| A-2 | 396–397 | 2 | Basic Casting Quality Factors, Ec |
| A-3 | 398–401 | 4 | Basic Quality Factors for Longitudinal Weld Joints, Ej |
| Notes A-4/A-4C | 402 | 1 | Notes |
| A-4 | 404–419 | 16 | Design Stress Values for Bolting — SI |
| A-4C | 420–429 | 10 | same — U.S. Customary |
| Spec Index B | 431 | 1 | Spec. No. → Title |
| B-1 / B-1C | 432–433 / 434–435 | 4 | Hydrostatic Design Stresses, thermoplastic pipe |
| B-2, B-3 | 435 | — | share page with B-1C tail |
| B-4, B-5 | 436 | 1 | Allowable pressures, concrete pipe |
| B-6 | 437 | 1 | PEX-AL-PEX / PE-AL-PE pipe |
| C-1 / C-1C | 440–444 / 446–450 | 10 | Thermal Expansion Data |
| C-2 | 451–452 | 2 | Thermal Expansion Coefficients, Nonmetals |
| C-3 / C-3C | 453–455 / 456–459 | 7 | Moduli of Elasticity for Metals (landscape) |
| C-4 | 460–461 | 2 | Modulus of Elasticity for Nonmetals |

## Decisions (confirmed with user)

- One JSON file per table, under `appendix_a/`, `appendix_b/`, `appendix_c/`, plus `index.json`.
- Values typed: numbers as JSON numbers, `…` → `null`, temperature-keyed objects.
- SI and U.S. Customary companion tables kept **separate** (their line numbering differs — a
  merge by line number would silently mis-pair materials), cross-referenced via `companion_table`.

## Steps

- [x] Verify source, destination, text-layer quality
- [x] Map appendix page ranges and full table inventory
- [x] Resolve schema unknowns (spreads, rotation, shared pages, per-table columns)
- [x] Build positional extractor (row clustering, column-gap detection, rotation handling)
- [x] Handle spread joining by Line No. + section headings + wrapped cells
- [x] Extract prose blocks (spec indexes, notes) separately
- [x] Normalize + type values; strip page furniture
- [x] Validate: row counts, line-number continuity, null/value ratios, spot-check vs PDF
- [x] Write JSON to destination + index manifest

## Review — B31.3 (measured, not estimated)

24 files written to the resources folder: 19 tables + 2 specification indexes + 2 notes
documents + `asme_b31_3_2024_index.json` manifest. **3,147 data rows.**

| Table | Rows | | Table | Rows |
|---|---|---|---|---|
| A-1 | 1,146 | | B-1 / B-1C | 36 / 36 |
| A-1C | 1,140 | | B-2 / B-3 | 1 / 2 |
| A-2 | 24 | | B-4 / B-5 / B-6 | 9 / 5 / 9 |
| A-3 | 127 | | C-1 / C-1C | 52 / 52 |
| A-4 / A-4C | 142 / 142 | | C-2 | 44 |
| | | | C-3 / C-3C | 75 / 75 |
| | | | C-4 | 30 |

Plus spec index A (192 entries), spec index B (28), notes for A-1/A-1C (6 general + 66
numbered), notes for A-4/A-4C (6 + 18).

### Verification performed

- **Line-number continuity:** every block of A-1 (9 blocks), A-1C (8), A-4 (1), A-4C (2)
  runs 1..N with no gaps and no duplicates.
- **SI / U.S. Customary parity:** A-4=A-4C=142, B-1=B-1C=36, C-1=C-1C=52, C-3=C-3C=75.
- **A-1 (1,146) vs A-1C (1,140) differ by 6 — this is real, not an extraction error.**
  Verified against the printed pages: A-1's first block ends at line 30 (p208) while
  A-1C's ends at line 24 (p318); the two tables also list materials in a different order
  (A-1 line 1 = A126, A-1C line 1 = A48). This is why they are NOT merged.
- **Spot-checks against the PDF:** A-1 block 2 line 2 (A672 A45, S = 103 MPa at 40°C down
  to 6.89 MPa at 600°C), A-1C block 1 line 1 (A48 Gray 20), C-3 carbon steel row,
  B-1 F441 row, C-4 first rows — all match the printed pages.
- `min_temp_c` legitimately holds letters (A/B/C) as well as numbers — those are ASME's
  minimum-temperature curve designations, kept verbatim.
- Page furniture stripped: running head, printed folio (removed by position, including on
  the rotated C-3 pages where it maps to the left edge), `ð24Þ` change markers,
  "TABLE STARTS ON NEXT PAGE", "(Cont'd)". No logos/watermarks exist in the text layer.
- Spacing lost in justified note text ("Notes(1)through(7)are...") restored from character
  positions; gaps measured bimodal (0.0 pt intra-word vs ~1.2 pt at word breaks).

---

# Task 2: ASME BPVC Section II Part D (Metric) 2025

Source: `(local)\...\BPVC\SECCION II\D Metric 2025 .pdf` (14.6 MB)
Destination: same resources folder.

- [x] Map document structure and table inventory (1,537 pages)
- [x] Adapt the extractor to Section II-D's layout
- [x] Extract the "NOTES TO TABLE x" sections the Notes columns reference
- [x] Validate and write JSON

## Source facts (BPVC II-D)

Same structural DNA as B31.3 — real text layer, bold headers, `Line No.` anchor,
multi-page spreads — so the same extractor was reused with three changes:

1. Table ids are `Table 1A` … `Table Y-1`, `Table TE-4`, and repeat on continuation pages
   as `Table 1A (Cont'd)`; running head is `ASME BPVC.II.D.M-2025`.
2. **Tables 2A and 2B set the whole page in a non-bold face**, so the font-weight header
   split fails there. Fallback: the body starts at the first row whose leftmost cell is a
   bare number. (Hybrid — bold first, numeric fallback.)
3. Page groups are 2–4 pages wide (ID page + 1–3 value pages continuing across temperature
   bands) and **line numbering restarts at 1 in every group**, so rows are keyed by
   (block, line_no).

Other document-specific handling: TE/TCD repeat sub-column labels (A/B/C, TC/TD) under
each material-group banner — labels are rebuilt from every overlapping header cell so they
stay unique; Table PRD is set two-up and uses indentation to separate sub-headings from
wrapped names, so it has a dedicated reader; note ids are `G1`/`W12`/`H1` style, set either
alone on a line (vertically centred against their text block) or inline — read in the PDF's
native line order, since sorting by y interleaves them.

## Review — BPVC II-D (measured)

**42 files, 12,515 data rows** in `bpvc_ii_d_metric_2025/`.

| Table | Rows | | Table | Rows |
|---|---|---|---|---|
| 1A | 1,808 | | 6A / 6B | 145 / 132 |
| 1B | 1,419 | | 6C / 6D | 58 / 95 |
| 2A | 1,010 | | U | 2,484 |
| 2B | 311 | | Y-1 / Y-2 | 2,475 / 10 |
| 3 | 243 | | TE-1..TE-5 | 168/13/17/390/17 |
| 4 | 74 | | TCD | 468 |
| 5A / 5B | 672 / 256 | | TM-1..TM-5 | 19/18/47/36/15 |
| | | | PRD | 115 |

Plus 14 `notes_table_*.json` (498 note items total, e.g. Table 1A: 84 items in 6 sections
covering G1–G33, H1–H6, S1–S11, T1–T12, W1–W15).

### Verification performed

- **Line-number continuity: 0 problems.** Every page-group block in all 15 spread tables
  runs 1..N with no gaps and no duplicates.
- **Spot-check against known values:** SA-516 Gr 70 in Table 1A gives S = 138 MPa at 40 °C
  (correct); Table 1A line 1 = 78.6 MPa, matching printed page 60.
- Rows that are all-ellipsis but carry a printed line number (e.g. Table U line 20 —
  verified blank in the source) are **kept**, so `line_no` stays 1:1 with the book.
- 0 residual ellipsis-only string values across all 50 data files (they are `null`).

---

# Task 3: BPVC II-D Subpart 3 charts + appendix prose (follow-up request)

- [x] Subpart 3 chart tabular values → JSON curves
- [x] Subpart 3 chart figures → PNG
- [x] Mandatory + Nonmandatory appendix prose → structured sections
- [x] Tables and figures printed inside the appendices

## Key finding

Subpart 3 is **not only graphical**. Printed pp. 1328–1375 carry "Tabular Values for
Figure xx" — the digitised A/B data behind every chart. That is the usable form of the
external-pressure charts, so it was extracted as data, not just imaged.

ASME prints those values in a **carried-exponent notation**: an exponent appears only
when it changes, so `1.00 −05` followed by `7.00` means 7.00e-04. Confirmed by the
monotonic rise of A (1e-5 → 1e-1) and of B within every temperature block; resolved into
absolute values on extraction.

Three header variants had to be handled: the usual (Temp, A, B) triples; CS-3 keyed on
**yield strength**; CI-1 keyed on **class/temperature**; and NFN-15/16/18/19/20 set six-up
as (A, B) pairs with the temperature in a banner above each pair.

## Results

`subpart_3_external_pressure_charts/` — **79 figures (PNG) + 76 data tables**,
316 curves, 3,421 points. Figure G (geometric) and Figure NFN-21 have no tabular values
in the Code; every other figure does.

`appendices/` — **13 appendices, 131 sections, 36,867 words**, plus **35 tables**
(512 rows) and **90 figures (PNG)**, of which **19 carry their plotted values as a data
table** beneath the graph (251 rows) — the Smt / St / stress-rupture / isochronous curves.

| Appendix | Sections | Words | | Appendix | Sections | Words |
|---|---|---|---|---|---|---|
| Mandatory 1 | 1 | 802 | | Mandatory 10 | 3 | 711 |
| Mandatory 2 | 4 | 1,096 | | Nonmandatory A | 57 | 15,495 |
| Mandatory 3 | 8 | 2,563 | | Nonmandatory B | 11 | 1,634 |
| Mandatory 5 | 21 | 5,113 | | Nonmandatory C | 3 | 1,425 |
| Mandatory 6 | 3 | 708 | | Nonmandatory D | 11 | 1,062 |
| Mandatory 7 | 7 | 704 | | Nonmandatory E | 1 | 5,515 |
| Mandatory 9 | 1 | 39 | | | | |

## Verification

- **B never decreases** on any of the 316 curves. A is non-decreasing everywhere; the
  only 5 exceptions are 3 legitimate repeated points and 2 **source typos**, extracted as
  printed and recorded in `source_anomalies`:
  - Table NFN-5 curve 315–345: third point printed `9.00 −03`; the surrounding sequence
    (3.12e-04 → 1.50e-03) implies `9.00 −04`.
  - Table NFN-18 curve 260: first A printed `0.002`; companion columns all start ≈0.0002.
- CS-1 spot-checked against printed p1328: A = 1e-05→0.1, B = 1→95.1 MPa, exact match.
  Figure CS-2 renders 5 curves (150/260/370/425/480 °C) — the extraction has the same 5.
- Table E-100.3-3 nulls at 375 °C / 400 °C for the austenitics verified against p1437 —
  those cells really are printed `…` (So begins at 425 °C for those materials).
- Prose: two-column reading order; line-break hyphens rejoined using evidence from the
  document itself (a hyphen is kept only where that compound is attested elsewhere, so
  "pro-/cesses" → "processes" but "time-dependent" is preserved).
- Section headings are taken only at heading size (11.5 pt); the same numbers appear at
  body size inside A-110's list of issues and must not start sections. Appendix A: 57
  real sections, not 199. Only 2 of 131 sections lack a heading.

## Combined total

**361 files, 53.8 MB** in the resources folder:

| Set | Files | Content |
|---|---|---|
| B31.3-2024 Appendices A/B/C | 24 | 3,147 rows |
| BPVC II-D Subparts 1–2 | 42 | 12,515 rows + 498 note items |
| BPVC II-D Subpart 3 | 156 | 3,421 chart points + 79 PNG |
| BPVC II-D Appendices | 139 | 36,867 words + 763 rows + 90 PNG |

Not extracted: nothing remaining in either document beyond publisher front/back matter.

---

# Task 4: ASME BPVC Section II Part D (U.S. Customary) 2025

Source: `(local)\...\BPVC\SECCION II\D Customary 2025 .pdf` (19.1 MB, 1,533 pages)
Destination: `.../resources/bpvc_ii_d_customary_2025/` — same rules as the Metric run.

- [x] Re-point the extractor at the Customary PDF and re-derive every page range
- [x] Subpart 1 + 2 tables, with the "NOTES TO TABLE x" documents
- [x] Subpart 3 charts (figures + tabular values)
- [x] Mandatory + Nonmandatory appendix prose, tables and figures
- [x] Validate and write JSON

## What had to change from the Metric run

The pipeline is the same; five document facts differ.

1. **Every page index.** Running head is `ASME BPVC.II.D.C-2025`; ranges re-derived from
   the bookmark tree and confirmed by a masthead scan (Subpart 2 starts idx 1200,
   Subpart 3 idx 1241, appendices idx 1371–1528).
2. **Thousands separators and an en-dash exponent sign** appear in the chart tables
   (`3,000`, `0.184 –01`); neither occurs in the Metric edition.
3. **The B column unit is not constant.** 74 chart sheets print `B, psi`, NFN-26 and
   NFN-27 print `B, ksi`. The unit is now read off each sheet and drives the field name
   (`b_psi` / `b_ksi`), recorded as `value_field` in every chart file and in the index.
4. **Figure G has tabular values in this edition** (the Metric edition prints none), and
   it is a geometric chart: `Do/t` indexes the curve, each point is `{l_over_do, a}` with
   no stress column. 77 chart tables here vs 76 in Metric.
5. **Table PRD density is `lb/in.3`**, so the field is `density_lb_in3`.

Two extraction rules were tightened, and they are improvements over the Metric run rather
than Customary-specific:

- The under-figure data tables of the design-fatigue figures key on the number of
  allowable cycles, printed as `Nd [Note (1)]` — the old header test only knew
  Temp/Time/Strain, so **E-100.16-1..5 were being missed**. E-100.16-5 is also only two
  columns wide, accepted now only when a numeric column of that width follows it.
  Result: 23 figures carry data (Metric run found 19; **4 of those 5 are missing from the
  Metric output and should be backfilled**).
- Figure G is printed over two sheets, so a chart file now carries `figure_images` as
  well as `figure_image` rather than pointing at a PNG that was never rendered.

## Review — BPVC II-D Customary (measured)

**361 files, 62.6 MB** (192 JSON + 169 PNG).

| Set | Files | Content |
|---|---|---|
| Subparts 1–2 | 42 | 12,340 rows + 14 notes documents |
| Subpart 3 | 157 | 77 chart tables, 341 curves, 3,814 points + 79 PNG |
| Appendices | 162 | 131 sections / 36,424 words, 35 tables (485 rows), 90 PNG, 23 figure-data tables (301 rows) |

### Verification performed

- **Line-number continuity: 0 problems.** Every page-group block of all 14 spread tables
  runs 1..N with no gaps or duplicates.
- **0 residual ellipsis-only strings** across all 192 JSON files (they are `null`).
- **Spot-checks:** SA-516 Gr 70 in Table 1A gives S = 20.0 ksi at 100°F and 18.1 ksi at
  700°F; Chart CS-1 starts at A = 1e-05, B = 145 psi (= the Metric edition's 1.0 MPa);
  Table PRD carbon steel ν = 0.30, ρ = 0.28 lb/in.3.
- **B never decreases** on any of the 341 curves; A is non-decreasing everywhere, the only
  exceptions being 2 legitimately repeated end points (NFN-15 at 600°F and 800°F).
- **One source typo**, recorded in `source_anomalies` and flagged on the point itself:
  Table NFN-27 at 200°F prints its fourth A as `1.30 −0.3`. An exponent is an integer and
  the surrounding sequence (9.50e-04 → 2.20e-03) fixes it as `−03`; read that way, because
  dropping the cell would have silently rescaled the rest of that curve by 10.
- **Row-count differences against the Metric set are real, not losses.** Checked
  material-by-material: Table U 2,433 vs 2,484 is mostly SA-231/SA-232 spring wire, where
  the editions list different diameter breakpoints (16 inch sizes vs 31 mm sizes); the
  TE/TCD tables differ because the °F and °C temperature grids have different row counts.
  Tables 1A, 1B, 2B, 3, 4, 5A, 5B, 6A, 6B, 6D, PRD, TM-1..5 and Y-2 match exactly.
- **0 dangling file references:** every `figure_image`, `figure_images` and `data_file`
  named in the three index files resolves to a rendered PNG or JSON on disk.

Not extracted: publisher front/back matter and the ENDNOTES page (idx 1530), matching the
Metric run's scope.
