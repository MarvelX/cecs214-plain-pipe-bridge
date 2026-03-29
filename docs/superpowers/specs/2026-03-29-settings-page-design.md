# Settings Page And Shared Template Design

## Summary

Add a dedicated `Settings` page to the Streamlit app so the repository can manage one shared JSON template for both UI preferences and default calculation parameters. The existing calculation workflow stays on its own `Engineering Workspace` page. New projects initialize from the shared template, imported projects can optionally apply the template, and the user can re-apply selected template groups to the current project at any time.

## Goals

- Introduce a true multi-page app structure with separate `Engineering Workspace` and `Settings` pages
- Store repository-level defaults in a single JSON file committed in the repo
- Cover both UI preferences and project calculation defaults
- Apply the shared template automatically for new projects
- Offer optional template application after importing a project JSON
- Allow re-applying template groups to the current project without overwriting everything blindly

## Non-Goals

- No per-user profile system
- No field-by-field diff viewer in the first version
- No migration of historic project files on disk
- No remote synchronization or database-backed settings

## Current State

The app is a single-page Streamlit experience implemented largely in [`app.py`](/Users/xiachen/Documents/New project/app.py). It keeps the active project in `st.session_state["project_input"]`, performs calculations from that state, and already supports JSON import/export for project data. The sidebar currently handles file import and usage tips, but there is no notion of repository-level settings or page navigation.

This matters for the design because:

- The current state model already supports replacing the active project in session state
- The app has only one large page file, so adding a settings feature is a good point to split page-level responsibilities
- Project JSON already exists, so the shared template should use JSON as well to maximize reuse and minimize conversion code

## User Experience

### Top-Level Navigation

The app becomes a two-page Streamlit app:

- `Engineering Workspace`
- `Settings`

`Engineering Workspace` remains the primary page for calculation work. `Settings` becomes the only place to edit repository defaults.

### Settings Page

The settings page exposes:

- Shared template metadata and file status
- UI preference editors
- Default project parameter editors
- `Save Template`
- `Restore Built-In Defaults`
- `Apply To Current Project`

The page should visually separate the two template domains:

- `UI Preferences`
- `Project Defaults`

### New Project Flow

When the app starts a new project session, it initializes project data from the shared template's `project_defaults` section rather than from hard-coded defaults alone.

### Import Project Flow

After a project JSON imports successfully:

1. The imported project becomes the current working project
2. The app shows a non-blocking prompt asking whether to apply the shared template to the imported project
3. If the user accepts, they choose which template groups to apply
4. The selected groups overwrite the active project state and, for UI preferences, the active page/session preferences

### Re-Apply To Current Project

From `Settings`, the user can trigger `Apply To Current Project`. The app then shows group-level checkboxes such as:

- UI preferences
- Project metadata defaults
- Geometry and material defaults
- Support scheme defaults
- Action defaults
- Combination factor defaults
- Pier foundation defaults

Only selected groups are overwritten.

## Data Model

### Shared Template File

Create a repository-tracked JSON file at:

`config/shared_template.json`

The file contains two top-level sections:

```json
{
  "ui_preferences": {
    "results_tab": "summary",
    "preview_height": 900,
    "show_formula_trace_expanded": false,
    "sidebar_tips_expanded": true
  },
  "project_defaults": {
    "meta": {},
    "geometry": {},
    "material": {},
    "support_scheme": {},
    "actions": {},
    "combination_factors": {},
    "pier_foundation": {}
  }
}
```

The exact field list under `project_defaults` should mirror the existing `ProjectInput` JSON structure as closely as possible. That keeps merge logic simple and predictable.

### Built-In Fallback

If the template file is missing or invalid, the app should fall back to a built-in template generated from the current `default_project_input()` data plus a small built-in UI preference object. The app should surface the failure as a visible warning on the settings page and use the fallback in memory so the app remains usable.

## Architecture

### Page Routing

Use Streamlit's native multi-page structure so `Engineering Workspace` and `Settings` are real separate pages, not an in-page tab simulation. Keep thin page entry files under a root `pages/` directory, and move shared rendering/state logic into reusable modules under `src/cecs214_plain_pipe/ui/`.

### File Structure

Refactor the app from one large file into small page-oriented modules:

- `app.py`
  - lightweight entry/bootstrap
  - shared initialization and page config
- `pages/1_Engineering_Workspace.py`
  - native Streamlit page entry for the calculation workspace
- `pages/2_Settings.py`
  - native Streamlit page entry for the settings page
- `src/cecs214_plain_pipe/ui/state.py`
  - session state keys
  - load/save/apply helpers
- `src/cecs214_plain_pipe/ui/template_store.py`
  - shared template loading, validation, saving, fallback handling
- `src/cecs214_plain_pipe/ui/template_apply.py`
  - group-based merge/apply logic
- `src/cecs214_plain_pipe/ui/pages/workspace.py`
  - current engineering workspace page
- `src/cecs214_plain_pipe/ui/pages/settings.py`
  - settings page

This is a targeted refactor, not a broad redesign. The goal is to isolate page orchestration and template management from calculation logic.

## Session State

Introduce explicit state keys:

- `project_input`
- `calculation_result`
- `calculation_error`
- `ui_preferences`
- `shared_template`
- `shared_template_status`
- `pending_import_template_prompt`

`project_input` remains the source of truth for current engineering data. `ui_preferences` becomes the session-level source for view behavior. `shared_template` caches the loaded template so both pages work from the same object.

## Page Initialization

At app startup:

1. Load the shared template from disk or fallback
2. Ensure `ui_preferences` exists in session state
3. Ensure `project_input` exists, seeded from template `project_defaults`
4. Route rendering to the selected Streamlit page

## Apply Logic

Apply behavior should be explicit and deterministic:

- Applying `ui_preferences` updates session UI state only
- Applying project groups overwrites only those named groups inside `project_input`
- Applying template groups clears stale calculation outputs because results may no longer match inputs

After any project-group application:

- remove `calculation_result`
- remove `calculation_error`
- show a success notice identifying which groups were updated

## Validation And Error Handling

### Template Load

- Invalid JSON: show warning, use built-in fallback
- Missing keys: fill from fallback defaults rather than failing hard
- Unknown keys: ignore for runtime use, preserve only if the save flow intentionally round-trips them

### Template Save

- Validate edited values before writing
- Reject writes that produce invalid project-default structures
- Write UTF-8 JSON with stable indentation for clean diffs
- On save failure, keep the in-memory edited state and show an actionable error

### Import Plus Apply

- If project import fails, preserve current state and show the existing import error pattern
- If project import succeeds but template application fails validation, keep the imported project loaded and report the apply error separately
- Saving the shared template does not automatically overwrite the active project; re-application remains an explicit user action

## Testing Strategy

Add automated coverage for the new template system in focused unit tests.

### Template Store Tests

- load valid template
- fallback on missing file
- fallback on invalid JSON
- merge missing keys from fallback
- save validated template

### Apply Logic Tests

- apply UI preferences only
- apply one selected project group
- apply multiple project groups
- clear stale calculation outputs after apply
- preserve unselected groups

### Page/Workflow Tests

- new session seeds project from shared template defaults
- import workflow sets prompt flag for optional template application
- restore built-in defaults resets settings editor state

## Open Questions Resolved In This Design

- Settings are repository-level, not per-user
- The template is a shared JSON file, not YAML or TOML
- The app uses a true separate settings page, not an in-page panel
- Re-apply uses group-level overwrite selection, not full overwrite and not fill-only merge
- New projects auto-apply defaults; imported projects get an automatic optional prompt

## Implementation Notes

- Keep the current project JSON import/export format unchanged
- Reuse existing `ProjectInput` parsing and validation wherever possible
- Keep first-version UI preferences intentionally small and tied to real view controls already present in the app
- Prefer helper functions over additional framework abstractions; the app is still a local Streamlit tool

## Rollout

Implement this in one feature slice:

1. Extract template/state helpers
2. Add shared template file and fallback logic
3. Split workspace and settings pages
4. Wire new-project, import, and re-apply flows
5. Add tests for template loading and apply behavior

The result should be a clearer app structure without changing the calculation engine or report-generation behavior.
