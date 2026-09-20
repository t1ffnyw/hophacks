import * as leaflet from "https://esm.sh/leaflet@1.9.4";

const L = leaflet.default ?? leaflet;
const MIN_CHANGE = -30;
const MAX_CHANGE = 30;
const MIN_ZOOM = 10;
const MAX_ZOOM = 14;

function ringContains(lng, lat, ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const xi = ring[i][0];
    const yi = ring[i][1];
    const xj = ring[j][0];
    const yj = ring[j][1];
    const intersect =
      yi > lat !== yj > lat &&
      lng < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
    if (intersect) inside = !inside;
  }
  return inside;
}

function polygonContains(lng, lat, coords) {
  if (!ringContains(lng, lat, coords[0])) return false;
  for (let i = 1; i < coords.length; i += 1) {
    if (ringContains(lng, lat, coords[i])) return false;
  }
  return true;
}

function featureContains(latlng, feature) {
  const geometry = feature.geometry;
  if (!geometry) return false;
  const lng = latlng.lng;
  const lat = latlng.lat;
  if (geometry.type === "Polygon") {
    return polygonContains(lng, lat, geometry.coordinates);
  }
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.some((coords) =>
      polygonContains(lng, lat, coords)
    );
  }
  return false;
}

function formatNumber(value, digits) {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "missing";
  }
  return Number(value).toFixed(digits);
}

function signed(value, digits) {
  const number = Number(value);
  const prefix = number > 0 ? "+" : "";
  return `${prefix}${number.toFixed(digits)}`;
}

function parseJson(text, fallback) {
  try {
    return JSON.parse(text || "");
  } catch (error) {
    return fallback;
  }
}

function lookupStats(stats, name) {
  if (!name) return null;
  return stats[name] || null;
}

function paddedMaxBounds(bounds) {
  if (!Array.isArray(bounds) || bounds.length !== 2) return null;
  const [[south, west], [north, east]] = bounds;
  const latPad = (north - south) * 0.08;
  const lngPad = (east - west) * 0.08;
  return [
    [south - latPad, west - lngPad],
    [north + latPad, east + lngPad],
  ];
}

function projectedCanopy(row, treeChange) {
  if (!row || row.trees === null || row.trees === undefined) return null;
  return Math.max(0, Math.min(100, row.trees + Number(treeChange)));
}

function projectedIllness(row, treeChange, slope) {
  const newTree = projectedCanopy(row, treeChange);
  if (newTree === null || row.illness === null || row.illness === undefined) {
    return null;
  }
  const actualChange = newTree - row.trees;
  return Math.max(0, Math.min(100, row.illness + Number(slope) * actualChange));
}

function assignClass(value, thresholds) {
  if (
    value === null ||
    value === undefined ||
    Number.isNaN(value) ||
    !thresholds ||
    !thresholds.valid_count
  ) {
    return null;
  }
  if (thresholds.unique_values === 1) return "Medium";
  if (thresholds.unique_values === 2) {
    return value <= thresholds.low_max ? "Low" : "High";
  }
  if (value <= thresholds.low_max) return "Low";
  if (value <= thresholds.medium_max) return "Medium";
  return "High";
}

function fillFromProjection(illness, trees, rules) {
  if (!rules) return "#bdbdbd";
  const healthClass = assignClass(illness, rules.health);
  const treesClass = assignClass(trees, rules.trees);
  const order = rules.class_order || ["Low", "Medium", "High"];
  const healthIndex = order.indexOf(healthClass);
  const treesIndex = order.indexOf(treesClass);
  if (healthIndex < 0 || treesIndex < 0) {
    return rules.missing || "#bdbdbd";
  }
  return rules.palette[treesIndex][healthIndex];
}

function projectedFill(name, stats, slope, treeChange, rules) {
  const row = lookupStats(stats, name);
  if (!row || row.trees === null || row.illness === null) return null;
  const newTree = projectedCanopy(row, treeChange);
  const newIllness = projectedIllness(row, treeChange, slope);
  if (newTree === null || newIllness === null) return null;
  return fillFromProjection(newIllness, newTree, rules);
}

function impactCopy(name, stats, slope, treeChange) {
  if (!name) {
    return {
      title: "Select a Community Statistical Area",
      body: "Click anywhere on the map to choose a CSA, then use the tree slider.",
    };
  }
  const row = lookupStats(stats, name);
  if (!row || row.trees === null || row.illness === null) {
    return {
      title: name,
      body: "This CSA is missing tree canopy or heat-health vulnerability data.",
    };
  }
  const newTree = projectedCanopy(row, treeChange);
  const newIllness = projectedIllness(row, treeChange, slope);
  return {
    title: name,
    body: `Tree Canopy: ${formatNumber(row.trees, 1)}% → ${formatNumber(newTree, 1)}%<br/>Heat-Health Vulnerability: ${formatNumber(row.illness, 1)} percentile → ${formatNumber(newIllness, 1)} percentile`,
  };
}

function featureStyle(feature, selectedName, fillOverride) {
  const name = feature.properties?.Community || "";
  const selected = name === selectedName;
  const fillColor =
    selected && fillOverride
      ? fillOverride
      : feature.properties?.baseFillColor ||
        feature.properties?.fillColor ||
        "#bdbdbd";
  return {
    color: selected ? "#111827" : "#4b5563",
    fillColor,
    fillOpacity: 1,
    weight: selected ? 2.8 : 0.6,
  };
}

function tooltipHtml(feature, projection) {
  const props = feature.properties || {};
  const treesValue =
    projection && projection.trees !== null && projection.trees !== undefined
      ? projection.trees
      : props.trees17;
  const illnessValue =
    projection &&
    projection.illness !== null &&
    projection.illness !== undefined
      ? projection.illness
      : props.illness_pctile;
  const trees =
    treesValue === null || treesValue === undefined
      ? "Missing"
      : `${Number(treesValue).toFixed(1)}%`;
  const illness =
    illnessValue === null || illnessValue === undefined
      ? "Missing"
      : Number(illnessValue).toFixed(1);
  const projectedNote =
    projection && projection.active ? "<br/><em>Projected</em>" : "";
  return `<strong>${props.Community || "Unknown CSA"}</strong><br/>Tree canopy: ${trees}<br/>Heat-health vulnerability: ${illness}${projectedNote}`;
}

function renderScatterPlot(container, scatter, selectedName, projection) {
  if (!container) return;
  const points = scatter?.points || [];
  if (!points.length) {
    container.innerHTML = "";
    return;
  }

  const width = 270;
  const height = 210;
  const margin = { top: 18, right: 12, bottom: 36, left: 40 };
  const innerW = width - margin.left - margin.right;
  const innerH = height - margin.top - margin.bottom;

  const xs = points.map((p) => p.trees);
  const ys = points.map((p) => p.illness);
  if (projection?.trees != null) xs.push(projection.trees);
  if (projection?.illness != null) ys.push(projection.illness);

  let xMin = Math.min(...xs);
  let xMax = Math.max(...xs);
  let yMin = Math.min(...ys);
  let yMax = Math.max(...ys);
  if (xMin === xMax) {
    xMin -= 1;
    xMax += 1;
  }
  if (yMin === yMax) {
    yMin -= 1;
    yMax += 1;
  }
  const xPad = (xMax - xMin) * 0.08;
  const yPad = (yMax - yMin) * 0.08;
  xMin -= xPad;
  xMax += xPad;
  yMin -= yPad;
  yMax += yPad;

  const xScale = (value) =>
    margin.left + ((value - xMin) / (xMax - xMin)) * innerW;
  const yScale = (value) =>
    margin.top + ((yMax - value) / (yMax - yMin)) * innerH;

  const line = scatter.line || [];
  let lineMarkup = "";
  if (line.length >= 2) {
    const x0 = Math.max(xMin, Math.min(xMax, line[0].trees));
    const x1 = Math.max(xMin, Math.min(xMax, line[1].trees));
    const y0 = scatter.intercept + scatter.slope * x0;
    const y1 = scatter.intercept + scatter.slope * x1;
    lineMarkup = `<line class="whatif-reg-line" x1="${xScale(x0)}" y1="${yScale(y0)}" x2="${xScale(x1)}" y2="${yScale(y1)}" />`;
  }

  const pointMarkup = points
    .map((point) => {
      const selected = point.name === selectedName;
      const cls = selected ? "whatif-scatter-point is-selected" : "whatif-scatter-point";
      return `<circle class="${cls}" cx="${xScale(point.trees)}" cy="${yScale(point.illness)}" r="${selected ? 5 : 3.2}"><title>${point.name}: ${point.trees.toFixed(1)}% canopy, ${point.illness.toFixed(1)} vulnerability</title></circle>`;
    })
    .join("");

  let projectionMarkup = "";
  if (
    projection &&
    projection.active &&
    projection.trees != null &&
    projection.illness != null
  ) {
    projectionMarkup = `<circle class="whatif-scatter-point is-projected" cx="${xScale(projection.trees)}" cy="${yScale(projection.illness)}" r="5"><title>Projected: ${projection.trees.toFixed(1)}% canopy, ${projection.illness.toFixed(1)} vulnerability</title></circle>`;
  }

  const xTicks = [xMin, (xMin + xMax) / 2, xMax];
  const yTicks = [yMin, (yMin + yMax) / 2, yMax];
  const xTickMarkup = xTicks
    .map(
      (tick) =>
        `<g transform="translate(${xScale(tick)},${margin.top + innerH})"><line y2="4" stroke="#6b7280" /><text y="16" text-anchor="middle">${tick.toFixed(0)}</text></g>`
    )
    .join("");
  const yTickMarkup = yTicks
    .map(
      (tick) =>
        `<g transform="translate(${margin.left},${yScale(tick)})"><line x2="-4" stroke="#6b7280" /><text x="-8" dy="0.35em" text-anchor="end">${tick.toFixed(0)}</text></g>`
    )
    .join("");

  const corr = Number(scatter.corr);
  const r2 = Number(scatter.r_squared);
  container.innerHTML = `
    <div class="whatif-scatter-card">
      <div class="csa-legend-title">Tree cover vs vulnerability</div>
      <div class="whatif-scatter-stats">r = ${corr.toFixed(2)} · R² = ${r2.toFixed(2)}</div>
      <svg viewBox="0 0 ${width} ${height}" width="100%" height="${height}" role="img" aria-label="Scatterplot of tree canopy cover versus heat-health vulnerability">
        <line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${margin.top + innerH}" stroke="#9ca3af" />
        <line x1="${margin.left}" y1="${margin.top + innerH}" x2="${margin.left + innerW}" y2="${margin.top + innerH}" stroke="#9ca3af" />
        ${xTickMarkup}
        ${yTickMarkup}
        ${lineMarkup}
        ${pointMarkup}
        ${projectionMarkup}
        <text class="whatif-axis-label" x="${margin.left + innerW / 2}" y="${height - 4}" text-anchor="middle">${scatter.x_label || "Tree canopy cover (%)"}</text>
        <text class="whatif-axis-label" transform="translate(12 ${margin.top + innerH / 2}) rotate(-90)" text-anchor="middle">${scatter.y_label || "Heat-health vulnerability"}</text>
      </svg>
    </div>
  `;
}

function render({ model, el }) {
  el.innerHTML = `
    <div class="whatif-root">
      <div class="whatif-map-row">
        <div class="whatif-map-frame">
          <div class="whatif-map"></div>
        </div>
        <div class="whatif-legend">
          <div class="whatif-legend-key"></div>
          <div class="whatif-scatter"></div>
        </div>
      </div>
      <div class="whatif-controls">
        <div class="whatif-slider-col">
          <div class="whatif-slider-wrap">
            <span class="whatif-end-icon" title="Fewer trees">🌳</span>
            <div class="whatif-slider-track">
              <input class="whatif-slider" type="range" min="${MIN_CHANGE}" max="${MAX_CHANGE}" step="1" />
              <div class="whatif-slider-value" hidden>—</div>
            </div>
            <span class="whatif-end-icon" title="More trees">🌳🌳🌳</span>
          </div>
        </div>
        <div class="whatif-impact"></div>
      </div>
    </div>
  `;

  const mapEl = el.querySelector(".whatif-map");
  const legendKeyEl = el.querySelector(".whatif-legend-key");
  const scatterEl = el.querySelector(".whatif-scatter");
  const sliderEl = el.querySelector(".whatif-slider");
  const valueEl = el.querySelector(".whatif-slider-value");
  const impactEl = el.querySelector(".whatif-impact");

  const bounds = parseJson(model.get("bounds_json"), []);
  const maxBounds = paddedMaxBounds(bounds);
  // Zoom toward map center (not the cursor) so trackpad zoom only scales,
  // matching the calmer feel of the Folium map above.
  const mapOptions = {
    minZoom: MIN_ZOOM,
    maxZoom: MAX_ZOOM,
    zoomControl: true,
    attributionControl: true,
    scrollWheelZoom: "center",
    doubleClickZoom: "center",
    touchZoom: "center",
    boxZoom: false,
    keyboard: false,
    bounceAtZoomLimits: true,
    inertia: false,
    wheelPxPerZoomLevel: 220,
    zoomSnap: 0.25,
    zoomDelta: 0.5,
  };
  if (maxBounds) {
    mapOptions.maxBounds = maxBounds;
    mapOptions.maxBoundsViscosity = 1.0;
  }

  const map = L.map(mapEl, mapOptions);

  const tileUrl = model.get("tile_url");
  if (tileUrl) {
    L.tileLayer(tileUrl, {
      attribution: model.get("tile_attr") || "",
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
    }).addTo(map);
  }

  let geoLayer = null;
  if (Array.isArray(bounds) && bounds.length === 2) {
    map.fitBounds(bounds, { animate: false, padding: [12, 12] });
  }

  const reset = L.control({ position: "topright" });
  reset.onAdd = function onAdd() {
    const wrap = L.DomUtil.create(
      "div",
      "leaflet-bar leaflet-control csa-reset-control"
    );
    const button = L.DomUtil.create("button", "whatif-reset", wrap);
    button.type = "button";
    button.textContent = "Reset to Baltimore";
    button.title = "Reset to Baltimore";
    L.DomEvent.disableClickPropagation(wrap);
    button.onclick = () => {
      if (Array.isArray(bounds) && bounds.length === 2) {
        map.fitBounds(bounds, { animate: true, padding: [12, 12] });
      }
    };
    return wrap;
  };
  reset.addTo(map);

  function selectedName() {
    return model.get("selected_csa") || "";
  }

  function currentProjection(treeChange) {
    const name = selectedName();
    if (!name) return null;
    const stats = parseJson(model.get("csa_stats"), {});
    const row = lookupStats(stats, name);
    const change =
      treeChange === undefined || treeChange === null
        ? Number(model.get("tree_change") || 0)
        : Number(treeChange);
    const slope = model.get("slope");
    const trees = projectedCanopy(row, change);
    const illness = projectedIllness(row, change, slope);
    if (trees === null || illness === null) return null;
    return {
      active: change !== 0,
      trees,
      illness,
      fill: projectedFill(
        name,
        stats,
        slope,
        change,
        parseJson(model.get("color_rules"), null)
      ),
    };
  }

  function applyMapStyles(treeChange) {
    if (!geoLayer) return;
    const name = selectedName();
    const stats = parseJson(model.get("csa_stats"), {});
    const slope = model.get("slope");
    const rules = parseJson(model.get("color_rules"), null);
    const change =
      treeChange === undefined || treeChange === null
        ? Number(model.get("tree_change") || 0)
        : Number(treeChange);
    const fillOverride = name
      ? projectedFill(name, stats, slope, change, rules)
      : null;
    const projection = currentProjection(change);
    geoLayer.eachLayer((layer) => {
      const feature = layer.feature;
      layer.setStyle(featureStyle(feature, name, fillOverride));
      if (feature?.properties?.Community === name && projection) {
        layer.setTooltipContent(tooltipHtml(feature, projection));
      } else if (feature) {
        layer.setTooltipContent(tooltipHtml(feature, null));
      }
    });
  }

  function redrawLayer() {
    const geojson = parseJson(model.get("geojson"), {
      type: "FeatureCollection",
      features: [],
    });
    for (const feature of geojson.features || []) {
      const props = feature.properties || {};
      props.baseFillColor = props.fillColor || props.baseFillColor;
      feature.properties = props;
    }
    if (geoLayer) {
      map.removeLayer(geoLayer);
    }
    geoLayer = L.geoJSON(geojson, {
      style: (feature) => featureStyle(feature, selectedName(), null),
      onEachFeature: (feature, layer) => {
        layer.bindTooltip(tooltipHtml(feature, null), { sticky: false });
      },
    }).addTo(map);
    applyMapStyles();
  }

  function selectCsa(name) {
    if (!name || name === selectedName()) return;
    model.set("selected_csa", name);
    model.set("tree_change", 0);
    model.save_changes();
  }

  map.on("click", (event) => {
    const geojson = parseJson(model.get("geojson"), { features: [] });
    const match = (geojson.features || []).find((feature) =>
      featureContains(event.latlng, feature)
    );
    if (match?.properties?.Community) {
      selectCsa(match.properties.Community);
    }
  });

  function updateSliderValueLabel(treeChange) {
    const stats = parseJson(model.get("csa_stats"), {});
    const row = lookupStats(stats, selectedName());
    const canopy = projectedCanopy(row, treeChange);
    const pct =
      ((Number(treeChange) - MIN_CHANGE) / (MAX_CHANGE - MIN_CHANGE)) * 100;
    valueEl.style.left = `${pct}%`;
    if (canopy === null) {
      valueEl.hidden = true;
      valueEl.textContent = "—";
      return;
    }
    valueEl.hidden = false;
    valueEl.textContent = `${formatNumber(canopy, 1)}%`;
  }

  function renderControls() {
    const treeChange = Number(model.get("tree_change") || 0);
    sliderEl.value = String(treeChange);
    updateSliderValueLabel(treeChange);
    const copy = impactCopy(
      selectedName(),
      parseJson(model.get("csa_stats"), {}),
      model.get("slope"),
      treeChange
    );
    impactEl.innerHTML = `<h3>${copy.title}</h3><p>${copy.body}</p>`;
    legendKeyEl.innerHTML = model.get("legend_html") || "";
    renderScatterPlot(
      scatterEl,
      parseJson(model.get("scatter_json"), {}),
      selectedName(),
      currentProjection(treeChange)
    );
    applyMapStyles(treeChange);
  }

  function onSliderInput() {
    const treeChange = Number(sliderEl.value);
    updateSliderValueLabel(treeChange);
    applyMapStyles(treeChange);
    renderScatterPlot(
      scatterEl,
      parseJson(model.get("scatter_json"), {}),
      selectedName(),
      currentProjection(treeChange)
    );
    model.set("tree_change", treeChange);
    model.save_changes();
  }

  sliderEl.addEventListener("input", onSliderInput);

  model.on("change:selected_csa", renderControls);
  model.on("change:tree_change", renderControls);
  model.on("change:geojson", () => {
    redrawLayer();
    renderControls();
  });
  model.on("change:legend_html", renderControls);
  model.on("change:color_rules", renderControls);
  model.on("change:scatter_json", renderControls);

  redrawLayer();
  renderControls();

  // Marimo/anywidget mounts into a shadow root; Leaflet often measures a
  // zero-size container on first paint. Refresh after layout settles.
  const refreshSize = () => map.invalidateSize({ animate: false });
  requestAnimationFrame(refreshSize);
  setTimeout(refreshSize, 0);
  setTimeout(refreshSize, 250);
  if (typeof ResizeObserver !== "undefined") {
    const frame = el.querySelector(".whatif-map-frame");
    const observer = new ResizeObserver(() => refreshSize());
    if (frame) observer.observe(frame);
  }
}

export default { render };
