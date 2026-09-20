"""An anywidget bridge around the existing Folium map; never replace its frame on selection."""
from html import escape
from itertools import combinations
import json
from pathlib import Path

import anywidget
import folium
import traitlets
from branca.element import Element, MacroElement, Template

from scripts.csa_comparison import COLORS, number, exact
from scripts.csa_map_data import CATEGORY_ORDER
from scripts.csa_map_render import (
    build_csa_map,
    build_legend_html,
    _style_function,
    _single_legend,
    _bivariate_legend,
)


class ComparisonMap(anywidget.AnyWidget):
    _esm = (Path(__file__).with_name('csa_selection.mjs').read_text() + '\n' +
            Path(__file__).with_name('csa_widget.js').read_text())
    selected_ids = traitlets.List(default_value=[None, None]).tag(sync=True)
    mode = traitlets.Unicode('heat').tag(sync=True)
    map_html = traitlets.Unicode().tag(sync=True)
    region_names = traitlets.List().tag(sync=True)
    colors = traitlets.List(default_value=list(COLORS)).tag(sync=True)

    @traitlets.validate('selected_ids')
    def _valid_selection(self, proposal):
        values = proposal['value']
        if len(values) != 2 or any(v is not None and v not in self.region_names for v in values):
            raise traitlets.TraitError('Select two valid CSA slots.')
        if values[0] is not None and values[0] == values[1]:
            raise traitlets.TraitError('A and B must be different regions.')
        return values


def mode_payload(gdf, specs, thresholds):
    result = {}
    for keys in [(k,) for k in CATEGORY_ORDER] + list(combinations(CATEGORY_ORDER, 2)):
        styles, tooltips = {}, {}
        for _, row in gdf.iterrows():
            region = row['Community']
            styles[region] = _style_function(keys)({'properties': row.to_dict()})
            lines = [f'<strong>{escape(region)}</strong>']
            for key in keys:
                spec = specs[key]
                value = number(row, spec.column)
                lines.append(escape(f'{spec.label}: {exact(value, spec.units == "USD")} {spec.units if value is not None else ""} ({spec.period})'))
                if len(keys) == 2:
                    lines.append(escape(f'{spec.label} class: {row[f"{key}_class"]}'))
            tooltips[region] = '<br>'.join(lines)
        legend = (_single_legend(keys[0], specs[keys[0]], thresholds[keys[0]]) if len(keys) == 1 else
                  _bivariate_legend(*keys, specs, thresholds))
        result['|'.join(keys)] = dict(styles=styles, tooltips=tooltips, legend=legend)
    return result


def build_comparison_widget(gdf, specs, thresholds, tile_url=None, tile_attr=None):
    map_object = build_csa_map(gdf, ['heat'], specs, thresholds, tile_url, tile_attr)
    # Main's choropleth keeps the legend in the Marimo sidebar; the comparison
    # iframe still needs a .csa-map-layout host so mode switches can update it.
    map_object.get_root().html.add_child(
        Element(build_legend_html(['heat'], specs, thresholds))
    )
    geo = next(child for child in map_object._children.values() if isinstance(child, folium.GeoJson))
    bridge = MacroElement()
    bridge.map_name, bridge.geo_name = map_object.get_name(), geo.get_name()
    bridge.payload = json.dumps(mode_payload(gdf, specs, thresholds), ensure_ascii=True).replace('</', '<\\/')
    bridge.colors = json.dumps(COLORS)
    bridge._template = Template('''{% macro script(this, kwargs) %}
    (() => {
      const map = {{this.map_name}}, geo = {{this.geo_name}}, modes = {{this.payload}}, colors = {{this.colors}};
      let selected = [null, null], mode = 'heat';
      const outlines = L.layerGroup().addTo(map);
      function paint() {
        outlines.clearLayers();
        geo.eachLayer(layer => {
          const id = layer.feature.properties.Community;
          layer.setStyle(modes[mode].styles[id]);
          layer.unbindTooltip(); layer.bindTooltip(modes[mode].tooltips[id], {sticky:true});
          const slot = selected.indexOf(id);
          if (slot !== -1) {
            L.geoJSON(layer.feature, {interactive:false, style:{color:colors[slot],weight:5,opacity:1,fill:false,dashArray:slot===1?'9 4':null}}).addTo(outlines);
          }
        });
        document.querySelector('.csa-map-layout').innerHTML = modes[mode].legend;
      }
      geo.eachLayer(layer => {
        layer.on('click', () => parent.postMessage({channel:'csa-comparison',type:'click',id:layer.feature.properties.Community}, '*'));
        layer.on('mouseout', () => layer.setStyle(modes[mode].styles[layer.feature.properties.Community]));
      });
      window.addEventListener('message', event => {
        if (event.source !== parent || event.data?.channel !== 'csa-comparison' || event.data.type !== 'update') return;
        if (modes[event.data.mode]) mode = event.data.mode;
        if (Array.isArray(event.data.selected) && event.data.selected.length === 2) selected = event.data.selected;
        paint();
      });
      paint();
      parent.postMessage({channel:'csa-comparison',type:'ready'}, '*');
    })();
    {% endmacro %}''')
    map_object.add_child(bridge)
    return ComparisonMap(region_names=sorted(gdf.Community.tolist()), map_html=map_object.get_root().render())


def build_selection_widget(gdf):
    """A/B neighborhood selectors without the Folium comparison map."""
    return ComparisonMap(
        region_names=sorted(gdf.Community.astype(str).str.strip().tolist()),
        map_html="",
    )
