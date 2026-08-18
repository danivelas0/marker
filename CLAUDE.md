# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependencies are managed with `uv` (`uv.lock` is committed; CI runs `uv sync --frozen --group dev --extra full`).

```shell
uv sync --group dev --extra full     # dev env (extra full = docx/pptx/xlsx/epub providers)
uv run pytest                        # full suite - needs a GPU + surya inference server
uv run pytest -m cpu                 # CPU-only subset (config parsing, providers) - what the ubuntu CI job runs
uv run pytest -m "not integration"   # skip slow end-to-end quality checks
uv run pytest tests/converters/test_pdf_converter.py::test_pdf_converter
uv run pre-commit run --all-files    # ruff lint (--fix) + ruff format
```

Running the tool during development (the root-level `convert.py`, `convert_single.py`, `marker_app.py`, `marker_server.py` are just shims over `marker/scripts/`):

```shell
uv run marker_single file.pdf --page_range 0 --output_format markdown
uv run marker /folder --max_files 2 --workers 4
uv run marker_single file.pdf config --help   # lists every builder/processor/renderer config key
```

Most tests pull PDFs from the HuggingFace dataset `datalab-to/pdfs` and spawn/attach to a surya inference server, so they are slow and require network + GPU. On a Turing GPU set `VLLM_DTYPE=float16` (bf16 is unsupported), as CI does.

## Architecture

Marker is a document → markdown/JSON/HTML/chunks pipeline. All heavy inference lives in **surya** (a separate package): a VLM served by a local inference server (vllm or llama.cpp), plus small server-backed CPU models. `marker/models.py::create_model_dict` builds only *thin clients* — marker worker processes hold no model weights, which is what lets many workers share one GPU.

### Pipeline

`Converter` (`marker/converters/`) orchestrates everything; `PdfConverter` is the default, with `TableConverter` and `OCRConverter` as narrower pipelines.

1. **Provider** (`marker/providers/`) reads the source file. `provider_from_filepath` sniffs the type (magic bytes, then extension); non-PDF providers render to PDF and delegate to `PdfProvider`, which uses pdftext for the embedded text layer.
2. **Builders** (`marker/builders/`) construct the `Document`, in this fixed order (`DocumentBuilder.__call__`):
   - `LayoutBuilder` — VLM layout (balanced) or the rf-detr `fast_layout_model` (fast / `disable_ocr`), producing the page's layout blocks.
   - `LineBuilder` — decides *per page* whether embedded text is usable (ocr-error model + layout-coverage heuristics) and merges provider lines in. This is where the balanced/fast split lives: balanced promotes a flagged page to full-page OCR, fast repairs individual blocks.
   - high-res page images are rendered only for pages that need them (see `highres_block_types`); everything else falls back to `page._highres_loader`.
   - `OcrBuilder` — full-page VLM OCR for pages `LineBuilder` marked, rebuilding page structure from the returned HTML; falls back to per-block OCR when a page fails.
   - `StructureBuilder` — groups blocks (captions with figures/tables, list items into `ListGroup`).
3. **Processors** (`marker/processors/`) mutate the document in list order — `PdfConverter.default_processors` order is significant. `marker/processors/llm/` holds the opt-in `--use_llm` processors.
4. **Renderer** (`marker/renderers/`) walks the block tree to output. Blocks emit `<content-ref src='...'>` placeholders for children; `BaseRenderer._splice_block_html` resolves them by string substitution and pulls out images.

### Schema and block registry

`marker/schema/` defines pydantic `Block` types. Every member of the `BlockTypes` enum (`marker/schema/__init__.py`) must have a class registered in `marker/schema/registry.py` — module-level asserts there fail at import if the enum and registry disagree, so adding a block type means touching both. Blocks are addressed by `BlockId` (`/page/{page}/{Type}/{idx}`) and looked up through `Document.get_block`. Callers can swap implementations per type via `PdfConverter.override_map` / `register_block_class`.

### Configuration

There is no config schema file. Every tunable is an `Annotated` class attribute on a `BaseBuilder`/`BaseProcessor`/`BaseRenderer`/`BaseService`/`BaseConverter` subclass, with the annotation metadata as its help text.

- `marker/config/crawler.py` walks those subclasses at import to build the full key set; `marker/config/printer.py` renders it for `config --help`.
- `marker/util.py::assign_config` copies matching keys from the config dict onto the instance, and also supports class-scoped keys like `MarkdownRenderer_remove_blocks` to disambiguate a name shared by several classes.
- `ConfigParser` (`marker/config/parser.py`) turns CLI options into that dict; `BaseConverter.resolve_dependencies` injects models by *parameter name* from `artifact_dict` (e.g. a builder taking `recognition_model` gets `artifact_dict["recognition_model"]`), so renaming a constructor parameter silently breaks wiring.

So: to add an option, add an `Annotated` attribute to the class that uses it — it becomes configurable everywhere automatically.

### Modes and the inference server

`mode` defaults by device (`balanced` on CUDA, `fast` otherwise) and is threaded from the converter into `LayoutBuilder`/`LineBuilder`. `disable_ocr` is the third path: no VLM calls at all, forcing the fast layout detector so nothing needs a server.

`marker/scripts/convert.py` (the batch CLI) spawns *one* `SuryaInferenceManager` server in the parent, exports `SURYA_INFERENCE_URL`, and budgets `SURYA_INFERENCE_PARALLEL` per worker to ~1.5× server capacity across the pool. Workers are `spawn`-ed and force `pdftext_workers=1` (nesting pdftext's process pool inside the worker pool deadlocks). With `--disable_ocr` no server starts at all.

### LLM processors and services

`marker/services/` wraps each LLM backend behind `BaseService.__call__(prompt, image, block, response_schema)`; required keys are enforced by `verify_config_keys` at construction, so a service raises immediately if e.g. an API key is missing. A service is only constructed when `use_llm` is set. All `BaseLLMSimpleBlockProcessor`s are collected by `BaseConverter.initialize_processors` into a single `LLMSimpleBlockMetaProcessor`, which issues their requests concurrently — a simple LLM processor therefore contributes prompt/schema/block-selection, not its own execution loop.

## Tests

`tests/conftest.py` drives everything off pytest markers:

- `@pytest.mark.config({...})` — the dict becomes the config passed to builders/converters (also accepts `override_map`, `llm_service`).
- `@pytest.mark.filename("x.pdf")` — picks a file from the `datalab-to/pdfs` dataset for the `temp_doc`/`pdf_document`/`pdf_converter` fixtures (default `adversarial.pdf`).
- `@pytest.mark.output_format("json"|"markdown"|"html"|"chunks")` — selects the renderer fixture.
- `@pytest.mark.cpu` / `@pytest.mark.integration` — CI job selection (see pytest.ini).

`tests/converters/test_olmocr_bench.py` runs real olmocr-bench pages from `tests/data/olmocr_bench/` as quality regression checks.

## Benchmarks

`benchmarks/` reproduces the README's quality and throughput numbers: `inference.py` (runs marker over olmocr-bench at worker concurrency, prints sustained pages/sec), `postprocess.py` (output normalization for the checker), `summarize.py` (per-category rates → Overall/Digital-only), and `competitors/` (each needs its own venv). See `benchmarks/README.md`.

## Conventions

- ruff is the linter and formatter (pre-commit config pins v0.9.10); there is no separate lint CI job, so run pre-commit before pushing.
- Non-obvious behavior is documented in dense inline comments explaining *why* (deadlocks, VLM cost tradeoffs, heuristic thresholds) — match that style rather than restating what the code does.
- Contributions require signing the CLA in `CLA.md` (the `cla.yml` workflow records signatures in `signatures/`).
