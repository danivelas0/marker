# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`marker-pdf` — converts PDFs, images, and office documents to markdown/JSON/HTML/chunks. It is a
pipeline around the [surya](https://github.com/datalab-to/surya) VLM (layout + OCR, served by a
separate inference server), `pdftext` (embedded text extraction), and small CPU models. Upstream is
`datalab-to/marker`; the default branch is `master`.

## Commands

Dependencies are managed with `uv` (`uv.lock` is committed). Everything runs through `uv run`.

```bash
uv sync --frozen --group dev --extra full   # dev env; --extra full adds docx/xlsx/pptx/epub support

uv run pytest                                # full suite (needs a GPU + HF_TOKEN)
uv run pytest -m cpu                         # CPU-only subset — the one to run locally without a GPU
uv run pytest tests/builders/test_structure.py::test_structure_builder   # single test
uv run pytest -m integration                 # slow end-to-end quality checks (runs the VLM)

uv run pre-commit run --all-files            # ruff lint + format (ruff is not a project dep; pre-commit fetches it)
```

CLI entry points (also runnable as the thin root wrappers `convert_single.py`, `convert.py`,
`marker_app.py`, `marker_server.py`):

```bash
uv run marker_single file.pdf --page_range 0 --output_format markdown
uv run marker /folder --workers 4 --max_files 2      # batch; parent spawns one shared inference server
uv run marker_single file.pdf config --help          # lists EVERY builder/processor/renderer config key
uv run marker_gui                                    # streamlit app
uv run marker_server --port 8001                     # fastapi server (page_range, mode, force_ocr, paginate_output, output_format only)
```

Benchmarks are not vendored — `benchmarks/README.md` has the olmOCR-bench harness and the
throughput/competitor methodology.

### Testing notes

- `tests/conftest.py` pulls PDFs from the HuggingFace dataset `datalab-to/pdfs`, so most tests need
  network + `HF_TOKEN`. Session-scoped `model_dict` builds the surya clients; anything OCR- or
  layout-bearing will spawn/attach an inference server.
- Tests are configured through custom markers, not fixture arguments:
  `@pytest.mark.config({...})` feeds the `config` dict into every builder/converter,
  `@pytest.mark.filename("x.pdf")` picks the source PDF, `@pytest.mark.output_format("json")` picks
  the renderer. `pdf_document` gives you a built `Document`; `pdf_converter` gives a full converter.
- `@pytest.mark.cpu` marks tests that must pass with no GPU/inference server (config parsing,
  providers). CI runs the full suite on a `t4_gpu` runner and the `cpu` subset on `ubuntu-latest`.

## Architecture

### The pipeline

`Converter` orchestrates everything (`marker/converters/pdf.py` is the reference implementation;
`TableConverter` and `OCRConverter` subclass it with trimmed `default_processors`):

1. **Provider** (`marker/providers/`) — reads the source file. `provider_from_filepath()` sniffs the
   type (`registry.py`); non-PDF providers render to PDF first. Supplies page images, page bboxes,
   links, and raw pdftext pages.
2. **Builders** (`marker/builders/`) — construct the `Document`:
   `DocumentBuilder` → `LayoutBuilder` (block regions) → `LineBuilder` (text lines + the per-page
   "is this text usable" decision) → high-res image render for pages that need it → `OcrBuilder` →
   `StructureBuilder` (grouping: captions with figures, lines into list items, etc.).
3. **Processors** (`marker/processors/`) — mutate blocks in order (`PdfConverter.default_processors`
   defines that order). Each declares `block_types` it handles.
4. **Renderer** (`marker/renderers/`) — walks the block tree to markdown/HTML/JSON/chunks.

`converter.build_document(path)` stops after step 3 and hands back the `Document`, which is the way
to work with blocks programmatically.

### Blocks and the registry

`BlockTypes` (`marker/schema/__init__.py`) is a closed enum; every member must be registered in
`marker/schema/registry.py`, which asserts registry size == enum size and that each class's
`block_type` default matches its key. Adding a block type means: enum member, class under
`marker/schema/blocks/`, export from `blocks/__init__.py`, `register_block_class(...)` call.

Blocks are pydantic models addressed by `BlockId` (`/page/{page_id}/{block_type}/{block_id}`).
Rendering is HTML-first: `Block.assemble_html` emits `<content-ref src='...'></content-ref>`
placeholders for children, which the renderers (and `marker/output.py:json_to_html`) splice via
`CONTENT_REF_RE`. Markdown is produced by converting that HTML.

`PdfConverter.override_map` / `register_block_class` let callers swap a block class at runtime —
this is how the tests' `override_map` config key works.

### Configuration

There is no config schema file. Configurable options are **`Annotated` class attributes with
defaults** on any `BaseBuilder`/`BaseProcessor`/`BaseConverter`/`BaseProvider`/`BaseRenderer`/
`BaseService` subclass. Three pieces make that work:

- `marker/util.py:assign_config` copies matching keys from the config dict onto the instance, and
  also honours class-prefixed keys like `MarkdownRenderer_remove_blocks` for disambiguation.
- `marker/config/crawler.py:ConfigCrawler` walks the packages at import time to discover every such
  attribute; this is what powers `config --help` and CLI validation.
- `marker/config/parser.py:ConfigParser` maps click options to config keys (with special cases:
  `--debug` fans out to four keys, `--disable_multiprocessing` → `pdftext_workers=1`, etc.).

So: **to add an option, add an `Annotated` attribute with a default** — no registration needed. The
docstring metadata in the `Annotated[...]` tuple becomes the `config --help` text.

`BaseConverter.resolve_dependencies` injects constructor args by name from `artifact_dict` (the
model dict) plus `config`; a constructor param that is neither in `artifact_dict` nor defaulted
raises. `marker/settings.py` holds env/`local.env` settings (`GOOGLE_API_KEY`, `TORCH_DEVICE`,
`OUTPUT_IMAGE_FORMAT`, paths). `local.env` is gitignored and may hold real API keys — never commit
it or echo its contents.

### Modes: `balanced` vs `fast`

The single most load-bearing runtime switch, threaded through `PdfConverter`, `LayoutBuilder`,
`LineBuilder`, and `OcrBuilder`. Default is device-derived in `PdfConverter.__init__`: `balanced` on
CUDA, `fast` on CPU/MPS.

- `balanced` — VLM layout model, full-page OCR whenever a page's embedded text is bad, inline math
  OCR'd automatically.
- `fast` — lightweight rf-detr layout detector, pdftext for text, VLM only for equations, surgical
  per-block repair, and full-page passes on genuinely scanned pages. A clean digital doc never
  starts the VLM server.
- `disable_ocr` — no VLM calls at all in either mode; forces the fast layout path so nothing needs a
  server.

When changing builder behaviour, check both paths — several methods branch on
`self.mode == "fast" or self.disable_ocr` (e.g. `LayoutBuilder.use_fast_layout`).

### Models are thin server clients

`marker/models.py:create_model_dict()` returns the "artifact dict". Every predictor in it is a
*client* of a shared surya server — worker processes hold no model weights, which is what lets many
workers share one GPU. `device`/`dtype`/`attention_implementation` args are accepted for call-site
compatibility but are no-ops. There is no dedicated table model: tables are reconstructed from the
text layer, with a VLM fallback for low-confidence results.

### LLM services (`--use_llm`)

`marker/services/` holds interchangeable backends (Gemini is the default; Vertex, Claude, OpenAI,
Azure, OpenRouter, Ollama). Selected by full import path via `--llm_service`. `BaseService.__init__`
calls `verify_config_keys`, which asserts every `Annotated` attr is non-`None` — that's how missing
API keys surface.

LLM processors come in two shapes. `BaseLLMComplexBlockProcessor` runs standalone.
`BaseLLMSimpleBlockProcessor` subclasses are *not* run in place: `BaseConverter.initialize_processors`
pulls them out of the processor list and folds them into a single `LLMSimpleBlockMetaProcessor`
inserted at the position of the last one, so their per-block prompts are batched into one concurrent
pass. Adding a simple LLM processor means implementing `block_prompts` / `rewrite_block`, not a
`__call__`.

## Conventions

- Config knobs are `Annotated[type, "description..."] = default` class attributes; the description
  strings are user-facing docs.
- Comments in this codebase explain *why* a non-obvious choice was made (see `models.py`,
  `builders/document.py`). Match that: explain the reasoning, not the mechanics.
- Contributions upstream require signing the CLA (`CLA.md`); `.github/workflows/cla.yml` enforces it.
