# Lessons

Patterns worth not relearning. Written after the ASME PCC extraction, 2026-09-05.

## Verify the tool's data model before writing a walker against it

`Table` blocks in marker's JSON carry their cells as `Line` children. A walker
that recurses on "this node has children" emitted ~36 stray text fragments per
table and never emitted the table itself. 42 tables were destroyed **silently** —
no error, no warning, plausible-looking output.

Only the count reconciliation caught it: 59 `Table` blocks in the raw output vs
15 in the result. **Reconcile counts against the source at every stage.** The
bug is invisible if you only read the output and it looks reasonable.

Generalised: before flattening any tree, dump `type -> has_children` across the
whole document. Do not infer structure from one sample node.

## A low CPU-to-wall ratio means blocked I/O, not slow compute

A marker run sat at 16 min wall for 93 s CPU (14% busy). That is the signature of
API blocking, not heavy work. Probing the API directly returned
`429 RESOURCE_EXHAUSTED` on 5/5 calls — the run was burning wall clock retrying a
dead quota with every enhancement silently failing.

**Probe the dependency directly rather than waiting.** One 5-second test would
have saved 16 minutes. Later the same signal (CPU frozen at 251 s for 14 min)
correctly identified a runaway local generation.

## Never trust an exit code you did not verify

Background `uv` commands reported **exit 0 while actually failing**. Three times.
`uv pip install torch==2.13.0` also no-op'd against an installed `2.13.0+cpu`
("Checked 2 packages") because the `+cu130` local version tag is ignored in
version matching — reported success, changed nothing.

**Verify by importing the package / checking the artifact, never by exit code.**

## Read the code path before promising what a feature will do

Claimed marker's LLM pass would rebuild tables that had no grid. It cannot:
`llm_table.py:117` returns early when a block has neither `TableCell` children
nor html. The processor *corrects* an existing representation; it never builds
one. This was asserted to the user before reading the function, and was wrong for
every LLM provider, not just the one in use.

The real fix was only visible from the code: lower `min_recon_score` so the
heuristic emits a rough grid, giving the LLM something to correct.

## Bound anything that can run away, especially a local model

`marker/services/ollama.py` calls `requests.post()` with **no timeout**. One
oversized table overflowed the model's 4096 context and a single generation ran
14+ minutes against a measured 22 s norm, with no way for marker to give up.

An outlier had already been measured (a 140-row table, 3x the size of the rest)
and was still allowed into an unbounded run. **When sampling reveals an outlier,
bound it before scaling up** — `--max_table_rows` existed the whole time.

## For engineering data, a wrong structure is worse than no structure

Forcing table reconstruction raised the count from 22 to 68, but sampling showed
the extra grids were bad: headers split mid-phrase, one table 56/85 cells empty.
Someone reads dimensions or WPS parameters off those.

Shipped instead: confident grids keep their html; the rest keep complete cell
text flagged `structure: "not_reconstructed"`. Content never lost, structure
never faked.

Corollary — **make correctness measurable rather than asserted.** Scoring each
table's cells against the PDF's own text layer separated two very different
failures: content real but columns misaligned (0.851 traceability, 0 unsourced
words) versus text actually invented. Only the second is dangerous, and without
the measurement both look identical in the JSON.

## Check the interpreter before debugging the dependencies

`uv sync` picked Python 3.14, which has no wheels for marker's pinned
`pillow<11` or `lxml`, so both fell back to source builds needing MSVC. The
errors pointed at the packages; the cause was the interpreter. `--python 3.12`
fixed it. Also drop optional extras that pull unrelated build deps —
`--extra full` was for DOCX/XLSX/EPUB inputs and these were all PDFs.
