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


---

# Task 5: ASME B31.3-2024 — remaining appendices (E through Z)

**Source:** `(local)\...\B31- PRESSURE PIPING\ASME B31.3 2024 Process Piping.pdf`
**Destination:** `.../resources/ASME B31/ASME B31.3/APPEX/` — alongside the existing
`appendix_a`, `appendix_b`, `appendix_c`, which are **not** touched or re-extracted.
**Scope:** technical content only — no front/back matter, running heads, folios, change
markers, logos or watermarks. INDEX and NOTES FOR INDEX (idx 573-593) are back matter, excluded.

## Source facts established

- 594 pages. Appendices E-Z occupy PDF idx 462-572 (111 pages), ending where INDEX starts (573).
- **No raster images anywhere in this range** (`get_images()` empty on all 111 pages). Every
  figure is vector line-art, so figures must be *rendered* from a clip rect, not extracted.
- Page frame is constant: running head `ASME B31.3-2024` at y=39.3, printed folio at y=745.1.
  Content band is y in (50, 735).
- Two-column prose; left column starts x=54 or x=72 (alternating recto/verso), right column
  x=306/324. Column split is clean at x=306.
- Fonts carry the structure: `Ronnia-Bold` = headings (17.3 pt appendix title, 10.6/9.5 pt
  section heads), `Cambria` 9.6 = body prose, `Cambria` 8.0 = table body,
  `Cambria-Italic` = defined terms/variables, `STIXGeneral`/`ArnoPro` = math glyphs.
- **Justified lines drop their space glyphs** (e.g. `S302.8 CodeCompliance-SatisfyingtheIntentof`).
  Character gaps are strictly bimodal: 0.00 pt inside a word, ~1.40 pt at a word break, so word
  boundaries are recoverable from character positions. Threshold used: max(0.45, 0.055 x size).
- Table K-1 / K-1C are **two-page spreads** joined by `Line No.`, same as A-1/A-4.
- Figure M-1 is landscape (`rotation=90`).
- `d24TH` (the U+00F0/U+00DE revision marker) appears throughout -> stripped, not content.

## Appendix inventory (0-based idx)

| Appx | idx | pg | Content |
|---|---|---|---|
| E | 462-466 | 5 | Reference Standards - publisher-grouped specification list |
| F | 467-474 | 8 | Guidance and Precautionary Considerations - prose |
| G | 475-476 | 2 | Safeguarding - prose |
| H | 477-484 | 8 | Sample Calculations for Branch Reinforcement - prose + 2 full-page figures |
| J | 485-501 | 17 | Nomenclature - Symbol/Definition table |
| K | 502-531 | 30 | Allowable Stresses for High Pressure Piping - spec index, notes, K-1 + K-1C spreads |
| L | 532-534 | 3 | Aluminum Alloy Pipe Flanges - prose + 3 tables |
| M | 535-536 | 2 | Guide to Classifying Fluid Services - prose + Figure M-1 (landscape flowchart) |
| N | 537-540 | 4 | Application of ASME B31.3 Internationally - prose |
| Q | 541 | 1 | Quality System Program - prose |
| R | 542-544 | 3 | Alternative Ultrasonic Acceptance Criteria - prose + Figure R307-1 + 2 tables |
| S | 545-559 | 15 | Piping System Stress Analysis Examples - prose, equations, 3 figures, ~14 tables |
| V | 560-562 | 3 | Allowable Variations in Elevated Temperature Service - prose + equations |
| W | 563-567 | 5 | High-Cycle Fatigue Assessment - prose + 5 tables |
| X | 568-571 | 4 | Metallic Bellows Expansion Joints - prose |
| Z | 572 | 1 | Preparation of Technical Inquiries - prose |

## Decisions (confirmed with user)

- **Figures render to PNG** next to the JSON, referenced by `figure_image`, with caption and
  page recorded. Same rule as the BPVC II-D runs. Only technical figures; no page furniture.
- **Worked calculations captured in full** - narrative prose, every printed equation line as
  text, and all result tables typed as data. Equation lines stay strings: the PDF text layer
  gives characters, not math structure, so anything else would be interpretation.
- One JSON per table; prose appendices get a section-tree JSON. Folder per appendix.
- SI / U.S. Customary companions (K-1 / K-1C) kept separate, cross-referenced, never merged.
- The existing `asme_b31_3_2024_index.json` is extended with the new appendices, A/B/C entries
  left byte-identical.

## Steps

- [x] Build shared core: line reconstruction with space restoration, column split, furniture strip
- [x] Prose engine: heading hierarchy from fonts, paragraph joining, list-item structure
- [x] Appendix E (standards list), J (nomenclature), K (spec index + notes + K-1/K-1C spreads)
- [x] Table engines for L, R, S, W
- [x] Equation-line capture for H, S, V, W
- [x] Figure rendering: H301-1, H311-1, M-1, R307-1, S301.1-1, S302.1-1, S303.1-1
- [x] Validate: line-number continuity, SI/USC parity, null ratios, spot-checks vs the PDF
- [x] Write JSON + PNG to destination, extend the index manifest

## What had to be solved that the A/B/C run did not face

Appendices A, B and C are pure tables. E-Z are mostly prose, maths and line art, and five
source facts had to be handled before any of it came out right.

1. **The rules give the column grid.** These tables are ruled horizontally only, but each
   rule is emitted as one segment per column, so the rule with the most segments *is* the
   column grid. That replaced the whitespace-gap column detection the A/B/C run needed and is
   considerably safer. Side-by-side tables (R308-1 next to R308-2) are separated by the gaps
   in those rules; stacked tables are separated by their printed captions, because rule
   spacing alone cannot tell a tall table from two short ones.
2. **Two opposite space failures on justified lines.** Some lines drop the space glyph and
   push the words apart by ~1.4 pt (`CodeCompliance`); others keep the spaces but track every
   letter out by ~0.6 pt, where a fixed threshold splits every word into letters. The
   threshold is therefore derived per line from that line's own median letter gap. A third
   variant - fully tracked-out text with a real space between every character, used for the
   URLs in Appendix N - is detected by its space ratio and collapsed.
3. **The minus signs are not in the text layer.** ASME draws them as short vector strokes, so
   `(2.5)(7.16 − 2.5)` arrives as `(2.5)(7.16` and `2.5)`. Strokes falling inside an equation
   band are restored as operator tokens; without that the equations read as though the
   subtraction were not there. The recovered equations then check out arithmetically, which
   is the strongest evidence the maths extraction is right: `d1 = [114.3 − (2)(5.27 − 2.5)]
   /sin 90 deg = 108.8 mm` reproduces the value printed in Figure H301-1.
4. **Displayed maths is a scatter of positioned glyph runs** - numerator, fraction rule,
   denominator, subscripts, plus ordinary Cambria runs for the units. Equations are found
   geometrically (a maths font locates a band; everything short and indented inside that band
   belongs to it) and linearised into reading order. They are stored as strings: the text
   layer carries positions, not structure, and inventing structure could change what an
   equation says.
5. **Line-break hyphens vs real compounds.** `selec- tively` must join, `tongue-and- groove`
   must not, and `low- and high-cycle` must stay as printed. Both candidate forms are tested
   against a vocabulary built from the whole document, so the code's own usage decides -
   which is how `nondestructive` and `postweld` come out unhyphenated.

Three extraction bugs were found by validation rather than by inspection, and are worth
recording because two of them silently *deleted* data:

- **A folio filter was eating table rows.** Stripping "any 2-4 digit number below y=700" as a
  printed page number removed the whole last row of a table whenever it fell that low - it
  cost Table K-1 line 59 and K-1C line 56, both of which are entirely numeric. The printed
  folio sits at y=745, already outside the content band, so the rule was never needed.
- **Fraction bars were being read as table rules**, which merged Table W302.1-4 with the
  equations below it and pulled 34 rows of maths fragments into the table. Table rules span
  the table; anything under 100 pt wide is maths.
- **The head/body split is not a fixed rule index.** Heads run to one, two or three tiers, so
  the split is taken as the first rule below the last bold label instead.

## Review - B31.3 Appendices E-Z (measured)

**55 files, 5.5 MB** written into the existing `APPEX/` folder: 48 JSON + 7 PNG, in 16 new
`appendix_*` folders. Appendices A, B and C were not touched, and their entries in the index
manifest are byte-identical to before (verified by comparison against a pre-run copy).

| Output | Count |
|---|---|
| Tables | 29 files, 546 data rows |
| Figures | 7 rendered at 300 dpi |
| Prose / list documents | 19 files - 219 sections, 25,337 words, 180 equations |
| Nomenclature (J) | 211 symbols, each with units, paragraph, table/figure and equation refs |
| Reference standards (E) | 446 standards under 23 publishers, plus 21 organizations |
| Specification Index (K) | 35 specifications |
| Tables K-1 / K-1C | 150 rows each |

### Verification performed

- **Line-number continuity: 0 problems.** Every one of the 13 two-page spreads of Tables K-1
  and K-1C runs contiguously with no gaps or duplicates, and every row carries stress values.
- **SI / U.S. Customary parity: K-1 = K-1C = 150 rows**, and the editions cross-check as unit
  conversions of each other. Line 1 (A53 Gr. B seamless pipe) reads 415 MPa / 240 MPa /
  371°C / 212 MPa at 40°C in K-1 and 60 ksi / 35 ksi / 700°F / 30.7 ksi at 100°F in K-1C -
  the same material to three figures in both unit systems.
- **The worked calculations validate arithmetically.** In H301 Example 1,
  `L4 = (2.5)(7.16 − 2.5) = 11.65 mm`, `d1 = 108.8 mm` and `d2 = 61.9 mm` all recompute from
  their own operands, and 108.8 mm is the value printed in Figure H301-1.
- **Table inventory matches the source contents list exactly** - 17 tables in Appendix S,
  5 in W, 3 in L, 2 in R, 2 in K. Ruled regions inside line-art figures were being picked up
  as tables at first; a region now counts as a table only if the caption above it says
  "Table".
- **0 dangling references:** every `figure_image` and every `file` named in the index
  manifest resolves to a file on disk, and every table's `row_count` matches its `rows`.
- **1 residual line-break hyphen, and it is correct as printed:** Appendix F FU315 reads
  "steam- (or sterilize-) in-place (SIP)", a suspended compound, not a missed join.
- **Figures checked by eye:** Figure M-1 renders complete and upright (it is set landscape on
  a portrait sheet, so the clip is computed in unrotated page space and the rotation
  reapplied at render time), and Figure H301-1 renders all four example illustrations.

### Where the extractor lives

`.../ASME PCC/tools/b31_3_appendix_extractor/` - eight modules plus a readme, kept next to the
resources rather than in this repo so it does not mix with the upstream marker code. The
readme records the five source facts the design depends on and the traps that cost real data
during the run, because two of them (the folio filter, the fraction bars) delete content
silently rather than failing.

Not extracted: the INDEX and NOTES FOR INDEX (pp. 574-594), which are back matter, and
publisher front matter - matching the scope of the A/B/C run. No page furniture, change
markers, logos or watermarks appear in any output; the source has no raster images at all in
this range, so nothing decorative could be picked up.

---

# Task 6: ASME B31.3-2024 — the body of the Code (Chapters I–X)

**Source:** `(local)\...\B31- PRESSURE PIPING\ASME B31.3 2024 Process Piping.pdf`
**Destination:** `.../resources/ASME B31/ASME B31.3/CHAPTERS/` — sibling of the existing
`APPEX/`, which is **not** touched or re-extracted.
**Scope:** PDF idx 33–196 only. Nothing before Chapter I (Contents, Foreword, Roster,
Correspondence, Introduction, Summary of Changes and the redesignation list are all front
matter, excluded by the user's decision). INDEX/back matter already out of scope.

## Decisions (confirmed with user)

- Start at idx 33; nothing earlier.
- One JSON per chapter, nested section tree keyed on the printed paragraph number.
- Output to `CHAPTERS/` beside `APPEX/`; the APPEX manifest stays byte-identical.

## Chapter ranges (from the bookmark tree)

| Ch | idx | pg | Title |
|---|---|---|---|
| I | 33–42 | 10 | Scope and Definitions |
| II | 43–81 | 39 | Design |
| III | 82–93 | 12 | Materials |
| IV | 94–97 | 4 | Standards for Piping Components |
| V | 98–116 | 19 | Fabrication, Assembly, and Erection |
| VI | 117–130 | 14 | Inspection, Examination, and Testing |
| VII | 131–152 | 22 | Nonmetallic Piping and Piping Lined With Nonmetals |
| VIII | 153–160 | 8 | Piping for Category M Fluid Service |
| IX | 161–188 | 28 | High Pressure Piping |
| X | 189–196 | 8 | High Purity Piping |

## Steps

- [x] Rename the tool package `b31_3_appendix_extractor` -> `b31_3_extractor`; readme updated
- [x] Probe: do the rotated pages (52, 53, 58, 59, 120, 121, 122) work through the existing
      rule-grid table engine, and in which coordinate space
- [x] Raster-aware figure extraction (20 body pages carry embedded images; the appendix
      range had none)
- [x] Chapter section tree from the paragraph-number hierarchy
- [x] 300.2 Definitions -> glossary JSON
- [x] Tables + their notes over the body range
- [x] Validate: bookmark-tree reconciliation, table/figure counts, dangling refs, furniture
- [x] Write JSON + PNG to CHAPTERS/ and a manifest

## What had to be solved that the appendix run did not face

Five properties of the source, all measured rather than assumed.

1. **PyMuPDF reports text and drawings in unrotated page space whatever the page /Rotate
   value says** - only `page.rect` changes. So on the seven landscape sheets the printed
   horizontal rules arrive as tall thin vertical rectangles and the rule-grid table engine
   finds nothing at all: Table 302.3.5-1 came back with zero rule rows. `rotate.UprightPage`
   turns the coordinates back (`upright_x = page_height - y`, `upright_y = x`, measured on
   idx 120) and every engine then sees an ordinary page. Rendering is the exception - it
   already honours /Rotate, and MuPDF rotated space proved to be exactly this upright space,
   checked by clipping to a caption bbox and getting that caption back - so the clip passes
   through untouched. Supplying a correcting matrix produced figures lying on their side.
2. **The running head and folio do not turn with the table**, so on a landscape sheet they
   bound the content in x rather than in y. The content band is carried on the page as a box.
3. **Twenty body pages carry the figure as an embedded raster image** and have an empty
   drawing list, where the whole appendix range has no raster images at all. Both sources are
   unioned, and the render dpi is raised to what the placed image actually holds, capped at
   600: Figure 328.4.2-1 is 3,892 px across a 468 pt box, so the appendices' 300 dpi would
   have thrown away more than half of it.
4. **Headings are set run-in** - "326.1.1 Listed Piping Components." in bold, the requirement
   continuing in roman on the same line. A whole-line font vote calls the entire line a
   heading, so the heading swallowed the first words of the text and the paragraph began
   "dards for piping components ...". Characters are now tagged with their span font and the
   line is split at the boundary.
5. **Group banners are set in the same bold face as the column labels.** Table 326.1.1-1
   sorts its standards under "Bolting", "Metallic Fittings, Valves, and Flanges" and so on,
   with a rule above and below each. The appendix head/body rule walked into the data and
   reclassified seven real rows as header. The split is now the last rule with nothing but
   bold above it, and the banners are kept as a `group` field on the rows they head.

Header labels also had to be placed geometrically rather than by column index. ASME writes
"Greater Material Thickness" once, centred over the mm and in. columns, and "Component
Temperature, Ti, degC (degF)" once over sixteen. Placed by midpoint, Table 302.3.5-1 came out
with a column called "Component 593 (1,100)" while fourteen other temperature columns carried
none of it. Each run is now assigned to every column it physically overlaps: a run over one
column is that column's label, a run over several is a banner recorded against all of them.

## Bugs found by validation, not by reading the output

Three of these deleted content silently - none of them failed, and all produced
plausible-looking output.

- **Any two rules on a page were treated as one table.** Page 89 carries the closing rule of
  a table continued from the page before and, 466 pt lower, the rule under an unruled inline
  list, with two columns of prose between them. They were glued into one region covering the
  whole left column, the prose pass was told to skip it, and **para. 323.3 disappeared from
  the Code entirely**. Only the bookmark reconciliation caught it (637 of 638). Fixing it
  also recovered 60 paragraphs in Chapter III and 13 in Chapter II being lost the same way.
- **Figure artwork was clustered by vertical proximity alone**, which is safe on a page that
  is nothing but a figure - all the appendices contain. Page 57 sets the miter-bend image in
  the left column, and vertical clustering pulled in vector strokes from the right column at
  the same height, stretching the clip from x 271 to x 518 and taking **para. 304.2.3 Miter
  Bends** with it. Clustering is now two-dimensional.
- **The figure clip rect was kept only for multi-sheet figures**, so all 39 single-sheet
  figures were never excluded from the prose pass at all, and their captions and internal
  callouts came through as stray sections of the Code.
- A table caption sits above its first rule and its NOTES below the last, both in the same
  faces as the surrounding prose, so excluding only the ruled grid dropped a table's notes
  into the running text of the paragraph that followed.
- Continuation lines in a key column are not distinguishable by their text: "N088xx and
  N066xx nickel" is a continuation though it opens with a capital, and "Other materials
  [Note (9)]" is a row of its own though it carries no values at all. ASME hangs the
  continuations by exactly one em (x=66.9 vs 74.9 in Table 302.3.5-1); the indent is the
  signal. Before this, Table 302.3.5-1 had 17 rows instead of its printed 7.
- The de-hyphenator was applied to paragraph text but not to headings, leaving twelve
  headings reading "Reinforcement of Welded Branch Connec- tions".

## Review - B31.3 Chapters I-X (measured)

**119 files, 13 MB** in `CHAPTERS/`: 78 JSON + 41 PNG. APPEX was not touched - its files were
last written at 10:58, before this run began.

| Ch | Sections | Paragraphs | Equations | Words | Tables | Rows | Figures |
|---|---|---|---|---|---|---|---|
| I | 10 | 66 | 0 | 1,717 | 1 | 19 | 1 |
| II | 242 | 816 | 42 | 19,354 | 8 | 36 | 8 |
| III | 24 | 128 | 0 | 3,519 | 6 | 122 | 2 |
| IV | 9 | 8 | 0 | 237 | 1 | 96 | 0 |
| V | 90 | 211 | 6 | 6,190 | 4 | 55 | 13 |
| VI | 89 | 251 | 2 | 7,006 | 2 | 22 | 1 |
| VII | 250 | 460 | 5 | 9,461 | 5 | 92 | 5 |
| VIII | 190 | 179 | 0 | 2,658 | 0 | 0 | 0 |
| IX | 308 | 607 | 13 | 12,512 | 7 | 73 | 3 |
| X | 87 | 140 | 0 | 2,390 | 0 | 0 | 6 |
| **All** | **1,299** | **2,866** | **68** | **65,044** | **34** | **515** | **39** |

Plus **189 definitions** (para. 300.2, one entry per term with its acronym and cross
references), **170 table note items** and **26 figure note items**.

Para. 300.2 is not repeated as prose. Read as running text the glossary came out as fifty-odd
paragraphs of terms welded together, with the italic terms mistaken for list markers - a worse
copy of what `definitions.json` holds properly structured - so the section keeps its lead-in
and its footnote and points at that file.

### Verification performed

- **Every one of the 638 paragraph numbers in the PDF bookmark tree is present in the section
  trees, and every one is on the page the book says it is** (0 off by more than a page). The
  bookmark tree is independent evidence: it was not used to build the trees.
- **Figures: 39 extracted against the 39 in the Code's own List of Figures** - none missing,
  none unexpected. Two (304.3.3-1, 304.3.4-1) are printed over two sheets, hence 41 PNGs.
- **Tables: all 33 entries in the List of Tables are present**, plus the Criterion Value Notes
  sheet for Table 341.3.2-1, which is printed but not listed. Nothing unexpected.
- **Spot-checks against the printed pages.** Table 302.3.5-1 comes out as the 7 steel groups
  printed, CrMo reading 1 / 0.95 / 0.91 / 0.86 / 0.82 across 427-538 degC and the austenitic
  row holding 1 at 816 degC; Table 330.1.1-1 P-No. 1 carbon steel <=25 mm gives 10 degC
  (50 degF); Table 341.3.2-1 lists the 10 printed imperfections with Crack = A in all ten weld
  columns, visual and radiography both required; Criterion A = "Zero (no evident
  imperfection)".
- **0 dangling file references**, and every table `row_count` matches both its own `rows` and
  the manifest.
- **No page furniture** in any output: no running heads, no printed folios, no revision change
  markers, no "(Cont'd)" - including in the group banners, which repeat with that tag on
  continuation pages.
- **1 residual line-break hyphen, and it is correct as printed:** "instruments as
  temperature- or pressure-responsive devices", a suspended compound.
- Figure renders checked by eye: Figure 304.3.3-1 comes out upright, complete and at 600 dpi
  with its caption and every callout, on a sheet set landscape.

Not extracted: publisher front matter (Contents, Foreword, committee roster, Correspondence,
Introduction, Summary of Changes, the redesignation list) and the INDEX - front and back
matter, per the scope decision. The source has no logos or watermarks in its text layer.

---

# Task 6: ANSI/AISC 360-16 - Specification + Commentary

**Source:** `(local)\...\0-STANDARDS\ASCI\AISC 360-16.pdf` (10.1 MB, 680 pages)
**Destination:** `Engineering_Hub\database\asci\asci_360\` (Daniel's path, given mid-run;
short snake_case file names, longest 40 characters)
**Scope:** technical content only - front matter (idx 0-26), the blank leaf, the back cover
and page furniture excluded.

## Decisions (confirmed with Daniel, 2026-09-06)

- **Commentary is in scope** (idx 310-675), filed under `commentary/`.
- **Equations: PNG + LaTeX transcription.** The text layer is unusable for maths, so every
  numbered equation is rendered and transcribed by reading the image.
- **Tables: cell grid where the rules give one unambiguously, PNG always.**
- Path and naming per Daniel: `asci/asci_360`, short snake_case.

## Source facts established

- 680 pages, native text layer, no OCR. Page box 432 x 648 pt, **single column**.
- Frame constant: folio + running head y < 26, publisher two-liner y > 620.
- Fonts carry the structure: `HelveticaNeue-Bold` 14 = part title, `Times-Bold` 10 =
  Specification section head, **`Times-Bold` 9.5 = Commentary section head** (the same face
  as a User Note, so the User Note test has to come first), `Times-Roman` 9.5 = body,
  `Times-Italic` 9.0 = figure caption (used by nothing else), `Helvetica-Bold` 13-14 =
  table caption, `Symbol` 9.5 = maths.
- **9 raster images in 620 pages of body, none of them a figure.** All 120 figures are
  vector line art.

## What had to be solved

1. **PyMuPDF's box metrics lie on maths pages.** The one-word block `where` on p136 is
   reported 33 pt tall. Every equation decision is made on boxes rebuilt from each span's
   baseline origin instead; a block-level band fuses an equation with its surrounding prose.
2. **Maths is typeset glyph by glyph.** Equation F2-5 comes back as `L r E F p y y = 1 76 .`
   Equations are located by their printed tag - the one part always plain text, always
   right-set, always vertically centred - then rendered and transcribed.
3. **Bands grow text and rules alternately.** A fraction's denominator sits further below
   the numerator than the adjacency threshold allows; it is the bar between them that
   brings the band down far enough. Growing once left F4-12 rendered without its denominator.
4. **A maths fragment sharing a baseline row with prose is a where-list term, not part of
   the equation.** `a_c` beside "= convective heat transfer coefficient" is a definition.
5. **Subscripts set tight against a variable are not words.** `Fybitbi` and `Pstory` read as
   prose to a naive lowercase-run test, which dropped G6-1, K3-11, K3-12, K4-8 and A-8-8.
6. **An equation tag always carries a digit.** Prose ending `..., kip-in. (N-mm)` was being
   read as equation `(N-mm)` on four pages.
7. **Vector art is not bounded by `get_drawings()`.** The full-page chart on p251 returns 15
   rects spanning x -27..456. Figures render a generous band and are trimmed to their ink.
8. **The Symbols list is set two ways.** Most pages put the symbol at x=42 and the
   definition at x=90; the rest run both on one line separated by literal spaces. And
   **where a definition wraps, its first line is set up to 3.4 pt ABOVE its symbol** - so a
   reading-order pairing silently gives Zx the definition of Zy. Each definition line is
   assigned to the last symbol at or near its own baseline. That fix took the list from 424
   entries with Zx wrong to 436 with every spot-check right.
9. **Rows separated by leading, not by a rule.** Table J3.1's nine bolt sizes live in one
   ruled band. Bands are split on shared baselines, but only where at least two columns
   carry the same number of lines and the leading is regular - the modal line count, not the
   maximum, because a column of stacked fractions prints two lines per data row.

## Review - measured

**805 files, 35 MB.** 52 part documents (14 chapters, 8 appendices, 26 commentary parts,
4 supplements) + 120 figure PNGs + 89 table PNGs + 544 equation PNGs + `document.json`,
`toc.json` and three indexes.

| | Count |
|---|---|
| Words of prose | 212,972 |
| Numbered equations | 544, **all 544 with LaTeX** |
| Figures | 120, all rendered, 0 dangling references |
| Tables | 89 rendered; 73 gridded, 756 data rows |
| Symbols / glossary / abbreviations | 436 / 272 / 46 typed entries |

### Verification performed

- **Text coverage 98.3%** of every content block on every in-scope page, measured
  character for character against the source. The shortfall is `sup_symbols` at 70%, which
  is the dot leaders being dropped (~12,000 characters of `. . . .`), not content.
- **Validator: 0 failures** across 18 checks - one file per part, every file wraps
  source + data, no dangling image reference, no page furniture in any record, indexes
  match the records, every equation carries LaTeX and an image, figure ids unique per page,
  chapter section numbers match their chapter letter, part page ranges tile the body with
  no gap or overlap.
- **Equations cross-checked against an independent reading.** 56 are simple enough to
  rebuild from glyph geometry alone; **36 agree exactly** and are marked
  `latex_confirmed_by_geometry`. All 20 disagreements were checked one by one and are the
  geometry reader's blind spots, not transcription errors: it cannot see a radical stroke
  (I8-1, J8-2, A-1-3, C-B3-1, C-I6-3), it reads the prime glyph as `¢` (I3-1a..I3-2b,
  J3-2), and it returns `05.` for `0.5` because the decimal point is drawn out of order.
- **Spot-checks against the printed pages:** Table J3.1 bolt pretension 1/2 in. -> 12/15
  kips, 1 in. -> 51/64/90, 1-1/2 in. -> 118/148; Table J3.2 A307 -> 45 (310) ksi tension,
  27 (186) shear; Table E7.1 c1/c2 = 0.18/1.31, 0.20/1.38, 0.22/1.49; symbols Fy, Fu, Cb,
  Lb, Lp, Lr, Z, Zx, Zy all correctly paired with their definitions and clauses.
- **Known limits recorded in every file's `source.note` and in `document.json`:**
  16 tables have no lattice and 27 more carry line art in their cells, so they are
  image + text only; 37 gridded tables still hold at least one cell of stacked lines and
  say so via `grid_rows_merged`; 2 grids are lossy (J3.5/J3.5M, a stacked fraction
  straddling a column rule); a value printed only inside a figure is not in the text; and
  the LaTeX is a transcription - the one interpreted field in the extraction - with the raw
  glyph run kept beside it as `glyph_order_text`.

Not extracted: cover, copyright page, preface, table of contents, running heads, printed
folios, the publisher footer, the blank leaf and the back cover.

---

# Task 7: ANSI/AISC 360-16 re-run from the five split PDFs, filed to Engineering_Hub

**Source:** `(local)\...\0-STANDARDS\ASCI\AISC 360-16_p1-p150.pdf` and the four further
splits (`p151-p300`, `p301-p450`, `p451-p600`, `p601-p680`).
**Destination:** `Engineering_Hub\database\asci\asci_360\` - filed this time; Task 6 built
the extraction but never copied it out of the scratchpad, so the folder was empty.

## Source facts established

- The five splits concatenate to exactly 680 pages and are **page-for-page identical** to
  the single-file `AISC 360-16.pdf`: 0 mismatches over all 680 pages comparing every span's
  font, size, origin and text, and 0 mismatches in `get_drawings()` counts.
- **Native text layer on every page, 0 raster images on the pages sampled. No OCR was
  needed and none was used** - so Ollama was not installed. A local VLM would have replaced
  a lossless text layer with a guess.

## What had to be solved

**Splitting re-roots orphaned bookmarks.** All 176 bookmarks survive (69+72+20+9+6) with
their titles and pages intact, but `insert_pdf` carries no outline at all, and each split
promotes to level 1 any entry whose parent stayed behind in an earlier file. The part map
is read from the bookmark tree, so `aisc_parts.parts()` died on `StopIteration` looking for
the Commentary node. Two rules restore the real depth: only a named part (Chapter A-N,
Appendix 1-8, Commentary, Symbols, Glossary, Abbreviations, References, Index, Metric
Conversion Factors) is top level, and nothing after the Commentary node is. That
reconstruction was then checked against the original PDF's outline as an oracle - **176/176
entries identical, level for level**.

## Steps

1. `merge_splits.py` - concatenate the five splits in printed-page order, re-base each
   split's TOC on its page offset, repair the orphaned levels, save `aisc_360_16_merged.pdf`.
2. Repoint `aisc_lib.PDF_PATH` at the merged file; record the five split names in
   `document.source_pdf` with a `source_note`.
3. `aisc_build.py` -> `aisc_tab.py` as of 16:21, which is *newer* than the output Task 6
   left behind: grids now carry `ruled_bands`, `bands_split_on_leading` and
   `grid_rows_merged`, and empty cells are `null` rather than `""`.
4. `validate.py`, `crosscheck.py`, copy to the destination, re-validate in place.

## Review - measured

**810 files, 35 MB**, in `chapters/` (14), `appendices/` (8), `commentary/` (26),
`supplements/` (4), `figures/` (120 PNG), `tables/` (89 PNG), `equations/` (544 PNG),
plus `document.json`, `toc.json` and three indexes. Longest file name **40 characters**,
all `snake_case`.

| | Count |
|---|---|
| Words of prose | 212,972 |
| Numbered equations | 544, all 544 with LaTeX |
| Figures | 120, all rendered, 0 dangling references |
| Tables | 89 rendered; 73 gridded, 37 flagged `grid_rows_merged`, 9 lossy |
| Symbols / glossary / abbreviations | 436 / 272 / 46 typed entries |

### Verification performed

- **Validator: 0 failures across 18 checks**, run twice - on the build output and again on
  the filed copy in `Engineering_Hub`.
- **Equation cross-check reproduces Task 6 exactly:** 56 geometry-checkable, 36 agree, 20
  differ, and the 20 are the geometry reader's known blind spots (it cannot see a radical
  stroke, reads the prime glyph as `¢`).
- **Payload compared against Task 6's output part by part:** all 52 parts present, 30
  byte-identical, and every one of the 22 differences is confined to the `tables` field and
  is the newer grid provenance, not different content.

### Known limit, unchanged and worth stating

**Figures are image + caption + reference only.** All 120 are vector line art rendered to
PNG with `figure_id`, caption, page and part; a value printed *inside* a figure is not in
the JSON. 24 captions read as data-bearing, of which only 4 are numbers a designer reads
off the page rather than commentary illustration: A-2.1 and A-2.2 (ponding flexibility
coefficients) and C-A-7.1 and C-A-7.2 (the alignment charts). Digitising those curves is a
separate job and was not attempted - a guessed curve is worse than an image.

Not extracted: cover, copyright page, preface, table of contents, running heads, printed
folios, the publisher footer, the blank leaf and the back cover. No trademarks, logos or
icons - the 9 raster images in the body are all page furniture and none is a figure.

---

# Task 8: ANSI/AISC 360-22 - Specification + Commentary

**Source:** `(local)\...\0-STANDARDS\ASCI\AISC 360-22.pdf` (106 MB, 780 pages)
**Destination:** `Engineering_Hub\database\aisc\aisc_360_2022\`
(note: Daniel renamed `database\asci` -> `database\aisc` between runs; the 360-16
extraction from Task 7 now lives at `aisc\aisc_360\`)

## Source facts established

- 780 pages. Page box 432 x 648 pt on 769 of them; 3 odd sizes and **1 page rotated 270**.
- **Real embedded text layer** (`TimesLTStd-*`, `HelveticaNeueLTPro-*`, `SymbolMT`),
  1.96 M characters, no page under 50 characters. **Not an OCR layer - no OCR is needed
  and Ollama is not used.** Running a VLM over exact text would replace it with a guess.
- **Every page also carries a full-page JPX raster** (2400 x 3600 = ~400 dpi) covering the
  whole page box, 3 kB on a text-only page up to 278 kB on a figure page.
- **Only 8 of 745 body pages have any vector geometry at all.** Every table rule, every
  figure line and every fraction bar lives in that raster. This is the fundamental
  difference from 360-16, where all 120 figures were vector line art.
- No running head and no printed folio in the text layer (0 of 99 sampled pages carry a
  `16.1-nnn` folio), so the only page furniture is the two-line footer at y=592.8 /
  y=600.8: 'Specification for Structural Steel Buildings, August 1, 2022' /
  'American Institute of Steel Construction'.
- Font -> role map (all changed from 360-16): `HelveticaNeueLTPro-Bd` 14 = part title,
  `TimesLTStd-Bold` 10 = section head, `TimesLTStd-Bold` 9.5 = User Note,
  `TimesLTStd-Roman` 9.5 = body, `TimesLTStd-Italic` 9.0 = figure caption,
  `HelveticaNeueLTPro-Bd` 13.5 = table caption, `SymbolMT` 9.5 = maths.
- Bookmark tree is intact and well formed: 180 entries, front matter to p32, Symbols p33,
  Glossary p52, Abbreviations p67, Chapters A-N, Appendices 1-8, Commentary p355 with
  References p735 and Metric Conversion Factors p777 beneath it.
- Maths is typeset glyph by glyph again, so the text layer still cannot be read as a line.
- Counted: **719 right-set equation tags, 131 figure captions, ~112 table captions**
  (360-16 had 544 / 120 / 89).

## The problem to solve, and the fix

The 360-16 pipeline leans on `get_drawings()` in three places, and all three are empty here:
table gridding (ruled bands), figure trimming (band trimmed to its ink), and equation band
growth (the fraction bar is what pulls a band down over its denominator).

**Fix: one `ink` abstraction with a raster implementation.** Render the page at 200 dpi to
greyscale, threshold to an ink mask, and read geometry off that wherever the 2016 code read
it off vectors. A rule is a row (or column) whose ink both covers >20% of the span and
contains a contiguous run >25% of it - the contiguous test is what separates a rule from a
dense line of text.

**Proven on Table D3.1 (idx 101): 11 horizontal and 5 vertical rules, and 0 of each on a
prose page.** Vertical rules are something the 2016 vector path never recovered, so column
boundaries can come from the real lattice instead of being inferred from text gaps.

## Steps

- [ ] Port `aisc_lib` constants: fonts, frame band, footer marks, body range, rotated page
- [ ] Add the raster `ink` module; replace the three `get_drawings()` call sites
- [ ] Re-derive the part map from the 360-22 bookmark tree
- [ ] Prose, sections, User Notes, Symbols/Glossary/Abbreviations lists
- [ ] Tables: lattice from raster rules, cells from text within the lattice, PNG always
- [ ] Figures: caption-anchored bands trimmed to raster ink, PNG + caption + references
- [ ] Equations: locate by printed tag, render PNG, transcribe to LaTeX
- [ ] Validate, cross-check, file to the destination, re-validate in place

## What had to be solved (Task 8)

1. **The delivered PDF is defective: its graphics layer is misregistered.** The file is two
   layers - a text layer with every glyph, and a full-page raster carrying what the text
   layer cannot express: the radicals and fraction bars of the maths, and the grey tint
   panels behind the User Notes. They do not line up. Equation F2-5 prints as `E` over
   `F_y` with no radical and no bar, while a stray radical is drawn 34 pt away across the
   prose beneath. **PDFium renders it identically to PyMuPDF, so it is the document, not
   the reader.** The displacement is a pure translation and the tint panels measure it:
   comparing each panel's CENTRE with the centre of the text it encloses, over 315 panels,
   gives **dx +34.28, dy -34.06 pt, sd 1.78**. Panel *edges* give -27.9 and are wrong - the
   padding is not symmetric about the text's ascender-to-descender box. Checked against
   ground truth: F2-5 stacks E (baseline 229.9) over F_y (243.5), so its bar belongs near
   y=233 and its vinculum just above 223; the raster bars sit at 266.4 and 253.4, and
   -34.06 puts them at 232.3 and 219.3. `repair_layer.py` rewrites the image placement
   matrix on 779 of 780 pages before anything is extracted. Residual over the same panels:
   **0.00 pt**. The offset is scaled by the page box for the 12 pages that are not
   432 x 648 and the one that is landscape.
2. **No vector geometry to grid tables with.** Only 8 of 745 body pages return a drawing,
   and `find_tables(strategy="lines")` reads `get_drawings()`. Rules are detected in the
   raster instead and drawn onto a throwaway copy of the page as real vector lines, so
   PyMuPDF's table finder works unchanged. Nothing rendered for output comes from that
   copy. This recovers **vertical** rules, which the 2016 vector path never had - 97 of 112
   tables gridded here against 73 of 89 in 360-16.
3. **The frame is not constant.** 12 pages are not 432 x 648 and one is rotated 270, where
   PyMuPDF reports text in unrotated landscape space. An absolute footer y is wrong on all
   of them, so each page's footer is found from its own text; all 745 carry it.
4. **A fraction bar had to be followed as a bar, not as ink.** Growing an equation band
   towards any adjacent ink walks into the next equation, because on a page of stacked
   display maths there is nearly always ink in the next sliver.
5. **A condition line was read as part of the equation above it.** '(a) When L_c/r <= ...'
   never reached the prose test because of its leading enumerator, and a 36 pt scalable
   parenthesis - line box 44 pt deep - then bridged E3-2 into the next condition. Two
   fixes: strip the enumerator before the prose test, and disqualify any fragment sharing
   rows with prose regardless of how far across the measure it sits.
6. **17 highlighter annotations on 7 pages** - someone's markup, not the standard - were
   being rendered into the output images; a yellow Ink stroke sits squarely over Equation
   J4-3. All rendering and the ink mask now pass `annots=False`.
7. **A unit was read as an equation.** 'kip-in.2 (N-mm2)' became equation `N-mm2`; the
   360-16 digit test passed it because of the superscript. Every printed AISC equation
   number ends in a digit-initial part; a unit does not.

## Review - Task 8 (measured)

**903 files, 59 MB** in `aisc\aisc_360_2022\`: 52 part documents (14 chapters, 8 appendices,
27 commentary parts, 3 supplements) + 129 figure PNGs + 112 table PNGs + 605 equation PNGs
+ `document.json`, `toc.json` and three indexes. Longest file name **41 characters**, all
`snake_case`.

| | 360-22 | (360-16 for comparison) |
|---|---|---|
| Words of prose | 250,675 | 212,972 |
| Numbered equations | 607, **all 607 with LaTeX** | 544 |
| Figures | 129 | 120 |
| Tables | 112 rendered, **97 gridded** | 89 / 73 |
| Symbols / glossary / abbreviations | 542 / 291 / 47 | 436 / 272 / 46 |

### Verification performed

- **Validator: 0 failures across 18 checks**, run on the build and again on the filed copy.
- **Equation cross-check: 125 geometry-checkable, 93 agree, 32 differ - and all 32 were
  read one by one and are the geometry reader's blind spots, not transcription errors.**
  It drops the solidus (I6-1, A-8-4, C-A-6-10 and 11 more), cannot see a radical (I4-1,
  I8-1, J8-2, K1-7, C-I3-3/4), drops Symbol-font glyphs (alpha in C2-1, A-7-1, A-7-2;
  epsilon read as 'e' in A-4-2), and returns '05.' for '0.5'.
- **Spot-checks against the printed pages, edition-correct for 2022:** Table J3.1 bolt
  pretension 1/2 in. -> 12/15 kips, 5/8 -> 19/24, 3/4 -> 28/35, 7/8 -> 39/49, including the
  new Group 144 and Group 200 columns; Table J3.2 A307 -> 45 (310) tension, 27 (190) shear,
  Group 120 -> 90 (620)/54 (370)/68 (470), Group 150 -> 113 (780)/68 (470)/84 (580).
- **Symbols pairing verified** on the entries that broke the 360-16 run: Zx and Zy take
  their own definitions, and all five Fy entries carry the right clause.
- Equations that changed between editions were caught rather than carried over: D5-2 gains
  C_r, E3-2/E3-4 use L_c/r, and Appendix 2 is a different subject entirely in 2022.

### Known limits, recorded in every file

- **No OCR was used and Ollama was not installed** - the text layer is real embedded type.
- Figures are image + caption + reference; a value printed inside a figure is not in the
  JSON.
- 15 tables have a lossy grid and are flagged; 49 more carry at least one cell of stacked
  lines and say so via `grid_rows_merged`.
- Some equations set inside Chapter K's tables render clipped at the foot, because a table
  cell's text bounds the band; the table image is the complete record for those, and the
  LaTeX was transcribed from the page.
- The LaTeX is a transcription - the one interpreted field - with `glyph_order_text` beside
  it. Where an equation is printed as a continuation of a where-list entry (E3-4, F9-3,
  I2-5, A-8-5 and others print with no left-hand side), the subject is supplied from the
  line above and that is visible in `glyph_order_text`.

Not extracted: cover, title page, copyright, dedication, preface, table of contents, the
publisher footer, and the back matter after Metric Conversion Factors.
