# CSA region popup on map click

## Goal

When a user clicks a Community Statistical Area (CSA) on the choropleth, show a Leaflet popup (“region card”) with that area’s name and all four metrics. Hover tooltips remain unchanged.

## Decisions

| Topic | Choice |
|-------|--------|
| Placement | Folium / Leaflet popup on the map |
| Content | CSA name + Heat, Heat-health vulnerability, Median household income, Tree canopy coverage |
| Hover | Keep existing tooltip (selected categories only) |
| Implementation | Folium `GeoJsonPopup` (Approach 1) |
| Notebook / Marimo | No new UI state; popup is entirely inside the map HTML |

## Behavior

1. Clicking a CSA opens a popup anchored to that feature.
2. Popup fields, in order:
   - **CSA** — `Community`
   - **Heat** — formatted `temp_af_mean`
   - **Heat-health vulnerability** — formatted `illness_pctile`
   - **Median household income** — formatted `mhhi23`
   - **Tree canopy coverage** — formatted `trees17`
3. Formatting matches existing tooltip helpers: USD with `$` and no decimals for income; one decimal for other metrics; `Missing` when the value is null/NaN.
4. Hover tooltip continues to show only the currently selected one or two categories.
5. Region outline on hover/focus is unchanged.
6. Popup closes via Leaflet defaults (close button / click elsewhere on the map).

## Implementation

### Files

- **Change:** `scripts/csa_map_render.py`
- **Unchanged:** `maps.py`, `scripts/csa_map_data.py` (data already has all four columns)

### Data prep

- Extend feature property prep so every feature always has formatted popup value columns for all keys in `CATEGORY_ORDER` (e.g. `_popup_value_heat`, …), regardless of `selected_keys`.
- Reuse `_format_measurement` and `LAYER_SPECS` so popup and tooltip formatting stay consistent.
- Tooltip columns continue to be prepared only for `selected_keys`.

### Map binding

In `build_csa_map`, pass `popup=folium.GeoJsonPopup(...)` to `folium.GeoJson` alongside the existing `tooltip`:

- `fields`: `Community` + `_popup_value_{key}` for each key in `CATEGORY_ORDER`
- `aliases`: `CSA` + each `LAYER_SPECS[key].label`
- Style: same compact white box style string already used for tooltips

### Out of scope

- Custom HTML card chrome beyond Folium popup defaults + shared style
- Marimo sidebar region panel or click → Python state bridge
- Showing Low/Medium/High class labels in the popup
- Changing category selection or legend behavior

## Testing

In `tests/test_csa_map_render.py`:

- Rendered map HTML includes popup wiring and aliases for all four metric labels plus Community/CSA.
- With a single selected category, tooltip field markers still reflect only that selection (popup still lists all four).

## Success criteria

- Clicking any CSA shows a popup with name + all four metrics.
- Hover still shows the selected-category tooltip.
- Existing map tests continue to pass; new assertions cover popup presence.
