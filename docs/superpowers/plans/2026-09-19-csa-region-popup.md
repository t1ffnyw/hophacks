# CSA Region Popup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** On CSA click, show a Folium `GeoJsonPopup` with Community name plus all four metrics, while keeping the existing hover tooltip.

**Architecture:** Extend GeoDataFrame prep in `csa_map_render.py` with always-on `_popup_value_*` columns for every key in `CATEGORY_ORDER`. Bind `folium.GeoJsonPopup` on the existing `GeoJson` layer alongside the current tooltip. No Marimo state changes.

**Tech Stack:** Python, Folium (`GeoJsonPopup` / `GeoJsonTooltip`), GeoPandas, unittest

## Global Constraints

- Popup content: CSA name + Heat, Heat-health vulnerability, Median household income, Tree canopy coverage (always all four)
- Hover tooltip unchanged (selected categories only)
- Formatting via existing `_format_measurement` (USD / one decimal / `Missing`)
- Change only `scripts/csa_map_render.py` and `tests/test_csa_map_render.py` for this feature
- `maps.py` stays unchanged

## File Structure

| File | Role |
|------|------|
| `scripts/csa_map_render.py` | Prep popup columns; `_popup()` helper; wire `popup=` on `GeoJson` |
| `tests/test_csa_map_render.py` | Assert popup fields/aliases present; tooltip still selection-scoped |

---

### Task 1: Popup columns + GeoJsonPopup on map click

**Files:**
- Modify: `scripts/csa_map_render.py`
- Test: `tests/test_csa_map_render.py`

**Interfaces:**
- Consumes: `CATEGORY_ORDER`, `LAYER_SPECS` / `specs`, `_format_measurement`, existing `_prepare_tooltip_columns`
- Produces: `_prepare_popup_columns(gdf, specs) -> gpd.GeoDataFrame`; `_popup(specs) -> folium.GeoJsonPopup`; `build_csa_map` passes `popup=_popup(specs)`

- [ ] **Step 1: Write the failing test**

Add to `CsaMapRenderTests` in `tests/test_csa_map_render.py`:

```python
def test_map_popup_lists_all_four_metrics_while_tooltip_stays_scoped(self):
    rendered = build_csa_map(
        self.gdf,
        ["heat"],
        self.diagnostics.layer_specs,
        self.diagnostics.thresholds,
        tile_url=None,
        tile_attr=None,
    ).get_root().render()

    self.assertIn("bindPopup", rendered)
    self.assertIn("_popup_value_heat", rendered)
    self.assertIn("_popup_value_health", rendered)
    self.assertIn("_popup_value_income", rendered)
    self.assertIn("_popup_value_trees", rendered)
    for label in (
        "Heat",
        "Heat-health vulnerability",
        "Median household income",
        "Tree canopy coverage",
    ):
        self.assertIn(label, rendered)

    self.assertIn("_tooltip_value_heat", rendered)
    self.assertNotIn("_tooltip_value_health", rendered)
    self.assertNotIn("_tooltip_value_income", rendered)
    self.assertNotIn("_tooltip_value_trees", rendered)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_csa_map_render.CsaMapRenderTests.test_map_popup_lists_all_four_metrics_while_tooltip_stays_scoped -v`

Expected: FAIL (`bindPopup` or `_popup_value_*` not found)

- [ ] **Step 3: Implement popup prep + binding**

In `scripts/csa_map_render.py`:

1. Add `_TOOLTIP_STYLE` constant shared by tooltip and popup (extract from `_tooltip`).

2. Add:

```python
def _prepare_popup_columns(
    gdf: gpd.GeoDataFrame,
    specs: Mapping[str, LayerSpec],
) -> gpd.GeoDataFrame:
    prepared = gdf.copy()
    for key in CATEGORY_ORDER:
        spec = specs[key]
        prepared[f"_popup_value_{key}"] = prepared[spec.column].map(
            lambda value, s=spec: _format_measurement(value, s)
        )
    return prepared
```

(Use default-arg capture `s=spec` to avoid the classic loop-closure bug.)

3. Add:

```python
def _popup(specs: Mapping[str, LayerSpec]) -> folium.GeoJsonPopup:
    fields = ["Community"]
    aliases = ["CSA"]
    for key in CATEGORY_ORDER:
        fields.append(f"_popup_value_{key}")
        aliases.append(specs[key].label)
    return folium.GeoJsonPopup(
        fields=fields,
        aliases=aliases,
        labels=True,
        localize=True,
        style=_TOOLTIP_STYLE,
    )
```

4. In `build_csa_map`, after tooltip prep:

```python
render_gdf = _prepare_tooltip_columns(gdf, selected, specs)
render_gdf = _prepare_popup_columns(render_gdf, specs)
```

And on `folium.GeoJson`:

```python
tooltip=_tooltip(selected, specs),
popup=_popup(specs),
```

Also fix `_prepare_tooltip_columns` lambda the same way if needed (`s=spec`) while touching that area — only if the closure bug is present.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests.test_csa_map_render -v`

Expected: OK (all tests)

- [ ] **Step 5: Commit**

```bash
git add scripts/csa_map_render.py tests/test_csa_map_render.py
git commit -m "Show all four CSA metrics in map click popup"
```

---

## Spec coverage (self-review)

| Spec requirement | Task |
|------------------|------|
| Leaflet popup on click | Task 1 (`GeoJsonPopup`) |
| Name + all four metrics | Task 1 (`CATEGORY_ORDER` popup fields) |
| Keep hover tooltip | Task 1 (tooltip unchanged; test asserts scope) |
| Shared formatting | Task 1 (`_format_measurement`) |
| `maps.py` unchanged | Task 1 (not modified) |
| Tests for popup + scoped tooltip | Task 1 |
