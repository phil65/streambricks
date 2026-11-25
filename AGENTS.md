# AGENTS.md

## Overview

StreamBricks is a small library of reusable Streamlit widgets and helpers. Its core
feature is automatic form generation: `model_edit` / `model_display` render editable or
read-only forms for Pydantic models, dataclasses and other `fieldz`-supported classes.
It also ships a typed session-state base class, a multiselect for rich items, an LLM
model selector, image capture, and Google/Microsoft login helpers built on `st.login`.

## Architecture

All code lives in `src/streambricks/`; the public API is re-exported in `__init__.py`.

- `widgets/model_widget/main.py`: the form engine. `render_model_form` (exported as
  `model_edit`) iterates `fieldz.fields(...)`, groups fields by `metadata["category"]`
  into tabs, and calls `get_field_renderer(field_info)` per field. Dispatch order:
  `json_schema_extra["field_type"]` (see `FIELD_METADATA_RENDERERS`) → `SecretStr` →
  Optional/Union → Enum → `PRIMITIVE_RENDERERS` → Literal → set/sequence → nested model.
  Returns `fieldz.replace(instance, **values)`. `render_model_readonly` (`model_display`)
  is the read-only counterpart.
- `widgets/model_widget/type_renderers.py`: per-type renderers (`render_str_field`,
  `render_int_field`, ...). All share the signature
  `(*, key, value=None, label=None, disabled=False, help=None, **field_info)`.
- `widgets/model_widget/field_metadata_renderers.py`: renderers chosen via field metadata
  (`field_type="model_identifier"` → `model_selector`).
- `widgets/type_helpers.py`: typing introspection (union/literal/set detection, defaults,
  descriptions) on top of `fieldz`.
- `widgets/sequence.py`: list editor reusing `get_field_renderer`.
- `widgets/bind_kwargs.py`: `bind_kwargs_as_widget` builds a Pydantic model from a
  function's signature and renders it as a form to configure kwargs.
- `widgets/multi_select.py` (`MultiSelectItem`, `multiselect`),
  `widgets/image_capture.py`, `widgets/model_selector.py` (lazy `tokonomics` import).
- `state.py`: `State(BaseModel)` with `get` / `set_state` / `reset` / `form`, stored in
  `st.session_state` under the class name.
- `auth/`: `helpers.py` (`google_login`, `microsoft_login`, `get_current_user`),
  `models.py` (`GoogleUser`, `MicrosoftUser` Pydantic models of `st.user`),
  `decorator.py` (`requires_login`), `profile_widget.py` (avatar via Pillow).
- `helpers.py`: `run(fn)` (runs inside Streamlit, or relaunches the script via
  `streamlit run`), `get_column_for_type`. `sidebar.py`: CSS helpers. `log.py`: loggers.

## Where to look

| Task | Location |
| --- | --- |
| Support a new field type in forms | `widgets/model_widget/type_renderers.py` + `PRIMITIVE_RENDERERS` / `get_field_renderer` in `widgets/model_widget/main.py` |
| Union / Optional / set / nested handling | `widgets/model_widget/main.py` |
| Type introspection bugs | `widgets/type_helpers.py` |
| Login / user models | `src/streambricks/auth/` |
| Public exports | `src/streambricks/__init__.py` |
| Tests | `tests/test_widgets.py`, `tests/state_models.py` |
| CI | `.github/workflows/build.yml`, `.github/workflows/documentation.yml` |

## Commands

```bash
uv sync --all-extras                 # setup (default groups: dev, lint, docs)
uv run pytest                        # tests
uvx ruff check . && uvx ruff format --check .
uv run ty check                      # type check (src only, warnings fail CI)
uv run deptry src                    # dependency check
uv run mknodes build                 # docs (site = README + generated API pages)
uv run duty lint | lint-check | test | build | serve   # see duties.py
```

Most modules have an `if __name__ == "__main__":` demo; run with
`uv run streamlit run src/streambricks/<module>.py`.

## Conventions

- Python >= 3.13, PEP 695 generics (`def f[T](...)`), `from __future__ import annotations`.
- Ruff with many rules (line length 100, preview formatting), Google docstrings.
- ty for type checking; use `# ty: ignore[rule]` only for real checker limitations
  (mypy-style `# type: ignore[code]` comments are reported as unused).
- Widget renderers take keyword-only args and pass Streamlit's `help` through
  (`# noqa: A002`).
- Tests drive widgets headlessly with `streamlit.testing.v1.AppTest.from_function`.
  The app function is re-executed as a script on each run, so imports go inside it.
  Classes defined inside the app are recreated on every rerun; `State` subclasses that
  must persist across reruns belong in an importable module (`tests/state_models.py`).

## Pitfalls

- Copier-managed project (`.copier-answers.yml`, template `copier-phil65`): workflows,
  `duties.py`, `.pre-commit-config.yaml` and most of `pyproject.toml` come from the
  template. Add dependencies below the `# Only add below (Copier)` markers and update via
  `copier update` rather than hand-editing template-owned parts.
- Extras: `auth` (authlib, needed by `st.login`, not imported directly; ignored in deptry
  config) and `llm` (`tokonomics`, imported lazily by `model_selector`). Keep optional
  imports inside functions so `import streambricks` works without extras.
- Login helpers need Streamlit auth configured in `.streamlit/secrets.toml` (gitignored).
- `State` stores instances under the class name by default; two classes with the same
  name collide unless `key=` is passed.
- `uv.lock` is gitignored.
