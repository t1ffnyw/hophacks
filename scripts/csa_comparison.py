"""Pure comparison calculations and accessible, shared-scale profile rendering."""
from decimal import Decimal, ROUND_HALF_UP
from html import escape
import math

COLORS = ('#0072B2', '#D55E00')
# Whole-degree bounds enclosing all 55 CSA afternoon means (32.47–36.86°C).
# Keep the same scale for every profile, independent of the selected pair.
HEAT_MIN, HEAT_MAX = 32, 37
MONEY_INCREMENT = 20000
FIELDS = (
    ('trees17', 'Tree canopy', '% of area', '2017'),
    ('temp_af_mean', 'Modeled afternoon temperature', '°C', '29 August 2018 · approximately 3 PM'),
    ('mhhi23', 'Median household income', 'USD', '2023'),
    ('illness_pctile', 'Heat-Health vulnerability', 'index points / 100', '2020–2022 · HHI 2024 release'),
)
CAUSAL_NOTE = ('These comparisons describe area-level associations; they do not establish that '
               'differences in tree canopy caused differences in health.')


def number(row, field):
    try:
        value = float(row[field])
        if not math.isfinite(value) or value == -999:
            return None
        if field in ('trees17', 'illness_pctile') and not 0 <= value <= 100:
            return None
        if field == 'mhhi23' and value < 0:
            return None
        return value
    except (KeyError, TypeError, ValueError):
        return None


def exact(value, money=False):
    if value is None:
        return 'Data unavailable'
    result = format(Decimal(str(value)), ',f').rstrip('0').rstrip('.') if '.' in str(value) else f'{value:,}'
    return ('$' if money else '') + result


def display_measure(value, field):
    """Format hover and story values; money/temp/canopy use at most two decimals."""
    if value is None:
        return 'Data unavailable'
    places = Decimal('0.1') if field == 'illness_pctile' else Decimal('0.01')
    quantized = Decimal(str(value)).quantize(places, rounding=ROUND_HALF_UP)
    if field == 'mhhi23':
        return f'${quantized:,.2f}'
    text = format(quantized, 'f')
    if field == 'temp_af_mean':
        return f'{text} °C'
    if field == 'trees17':
        return f'{text}%'
    return text


HOVER_LABELS = {
    'temp_af_mean': 'Temperature',
    'illness_pctile': 'Heat-Health vulnerability',
    'mhhi23': 'Income',
    'trees17': 'Canopy',
}


def hover_caption(value, field, warning=''):
    body = warning or display_measure(value, field)
    return f'{HOVER_LABELS[field]}: {body}'


def speech_bubble(label, value, x, y, width, height, pointer):
    """Rounded callout with a triangular pointer on one side."""
    mid_x, mid_y = x + width / 2, y + height / 2
    if pointer == 'left':
        points = f'{x},{mid_y - 7} {x - 12},{mid_y} {x},{mid_y + 7}'
        notch = f'<rect x="{x - 1}" y="{mid_y - 7}" width="4" height="14" fill="#fff"/>'
    elif pointer == 'right':
        points = f'{x + width},{mid_y - 7} {x + width + 12},{mid_y} {x + width},{mid_y + 7}'
        notch = f'<rect x="{x + width - 3}" y="{mid_y - 7}" width="4" height="14" fill="#fff"/>'
    elif pointer == 'bottom':
        points = f'{mid_x - 7},{y + height} {mid_x},{y + height + 12} {mid_x + 7},{y + height}'
        notch = f'<rect x="{mid_x - 7}" y="{y + height - 3}" width="14" height="4" fill="#fff"/>'
    else:
        points = f'{mid_x - 7},{y} {mid_x},{y - 12} {mid_x + 7},{y}'
        notch = f'<rect x="{mid_x - 7}" y="{y - 1}" width="14" height="4" fill="#fff"/>'
    return (
        f'<g class="bubble">'
        f'<polygon points="{points}" fill="#fff" stroke="#243342" stroke-width="1.5"/>'
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="#fff" stroke="#243342" stroke-width="1.5"/>'
        f'{notch}'
        f'<text x="{x + 10}" y="{y + 20}" font-size="12" fill="#243342">{escape(label)}:</text>'
        f'<text x="{x + 10}" y="{y + 38}" font-size="13" font-weight="700" fill="#243342">{escape(value)}</text>'
        f'</g>'
    )


def differences(a, b):
    """Signed A minus B differences; Decimal avoids binary subtraction noise."""
    return {field: (None if number(a, field) is None or number(b, field) is None else
                    Decimal(str(number(a, field))) - Decimal(str(number(b, field))))
            for field, *_ in FIELDS}


# Stored CSA scores use the application's documented 0–100 scale, without
# pairwise normalization or conversion from the overall HHI's 0–1 ranks.
HEALTH_MAX = 100
HALO_DESCRIPTION = (
    'Halo fill equals 100 minus the Heat-Health vulnerability. It does not represent '
    'the percentage of residents who are healthy. '
    'Area-level derived index: the unweighted mean of available ZIP/ZCTA '
    'heat-related EMS percentile ranks, on the stored 0–100 scale. '
    'It is not a national CSA percentile, an individual’s health, or the '
    'percentage of people who are sick. Source values could not be independently '
    'regenerated from the bundled workbook.'
)


def health_halo(health):
    """Invert only the visual fill on the fixed 0–100 stored score scale."""
    if health is not None and (not math.isfinite(health) or not 0 <= health <= HEALTH_MAX):
        raise ValueError('Heat-Health vulnerability must be finite and between 0 and 100')
    arcs = []
    for i in range(20):
        start = math.radians(-90 + i * 18)
        end = start + math.radians(13)
        path = (f'M {150 + 27 * math.cos(start)} {36 + 27 * math.sin(start)} '
                f'A 27 27 0 0 1 {150 + 27 * math.cos(end)} {36 + 27 * math.sin(end)}')
        fraction = 0 if health is None else min(1, max(0, (HEALTH_MAX - health) / HEALTH_MAX * 20 - i))
        arcs.append(f'<path class="halo-track" d="{path}"/>')
        arcs.append(f'<path class="halo-fill" d="{path}" pathLength="1" '
                    f'stroke-dasharray="{fraction} 1"/>')
    missing = ' halo-missing' if health is None else ''
    marker = '<text x="150" y="7" text-anchor="middle" font-size="9">?</text>' if health is None else ''
    return f'<g class="health-halo{missing}">{"".join(arcs)}{marker}</g>'


def profile(row, slot):
    color = COLORS[slot]
    badge = f'<span class="badge" style="background:{color}">{"AB"[slot]}</span>'
    if row is None:
        return f'<article>{badge}<h3>Choose Neighborhood {"AB"[slot]}</h3><p>Click a region on the map or use its dropdown above.</p></article>'
    heat = number(row, 'temp_af_mean')
    income = number(row, 'mhhi23')
    canopy = number(row, 'trees17')
    health = number(row, 'illness_pctile')
    health_warning = ''
    if health is None:
        try:
            raw_health = float(row.get('illness_pctile'))
            invalid_health = not math.isnan(raw_health) and raw_health != -999
        except TypeError:
            invalid_health = False  # None / pandas.NA represent missing values.
        except ValueError:
            invalid_health = True
        if invalid_health:
            health_warning = 'Invalid Heat-Health vulnerability: expected a finite value from 0 to 100.'
    height = 0 if heat is None else 110 * min(1, max(0, (heat - HEAT_MIN) / (HEAT_MAX - HEAT_MIN)))
    dots = ''.join(f'<circle cx="{72 + (i % 10) * 16}" cy="{190 + (i // 10) * 12}" r="4" fill="{ "#24854b" if canopy is not None and i < math.floor(canopy + .5) else "#dce2e6"}"/>' for i in range(100))
    bills = ''
    if income is not None:
        for i in range(math.ceil(income / MONEY_INCREMENT)):
            fraction = min(1, income / MONEY_INCREMENT - i)
            bills += f'<rect x="220" y="{151-i*12}" width="55" height="10" rx="2" fill="#e0e5e9"/><rect x="220" y="{151-i*12}" width="{55*fraction}" height="10" rx="2" fill="#688776"/><text x="244" y="{160-i*12}" font-size="10" fill="white">$</text>'
    heat_value = display_measure(heat, 'temp_af_mean')
    income_value = display_measure(income, 'mhhi23')
    canopy_value = display_measure(canopy, 'trees17')
    health_value = 'Invalid Heat-Health vulnerability' if health_warning else display_measure(health, 'illness_pctile')
    heat_tip = hover_caption(heat, 'temp_af_mean')
    income_tip = hover_caption(income, 'mhhi23')
    canopy_tip = hover_caption(canopy, 'trees17')
    health_tip = hover_caption(health, 'illness_pctile', health_warning)
    svg = f'''<svg viewBox="-130 0 440 338">
      <g class="hotspot"><title>{escape(heat_tip)}</title>
      <rect x="31" y="31" width="22" height="120" rx="11" fill="#e0e5e9"/>
      <rect x="37" y="{145-height}" width="10" height="{height}" rx="5" fill="#b65e54"/>
      <circle cx="42" cy="153" r="16" fill="{'#b65e54' if heat is not None else '#dce2e6'}"/>
      <text x="4" y="23" font-size="12">{HEAT_MAX}°C</text><text x="3" y="183" font-size="12">{HEAT_MIN}°C</text>
      <rect x="-130" y="0" width="218" height="185" fill="transparent"/>
      {speech_bubble('Temperature', heat_value, -122, 78, 128, 52, 'right')}</g>
      <g class="hotspot"><title>{escape(health_tip)}</title>
      {health_halo(health)}<g fill="#77818d"><circle cx="150" cy="36" r="16"/><rect x="126" y="70" width="48" height="53" rx="18"/>
      <rect x="112" y="73" width="13" height="56" rx="6"/><rect x="175" y="73" width="13" height="56" rx="6"/>
      <rect x="128" y="110" width="18" height="54" rx="7"/><rect x="154" y="110" width="18" height="54" rx="7"/></g>
      <rect x="100" y="0" width="110" height="185" fill="transparent"/>
      {speech_bubble('Heat-Health vulnerability', health_value, 8, 8, 148, 50, 'right')}</g>
      <g class="hotspot"><title>{escape(income_tip)}</title>{bills}
      <rect x="210" y="0" width="100" height="185" fill="transparent"/>
      {speech_bubble('Income', income_value, 78, 70, 132, 52, 'right')}</g>
      <g class="hotspot"><title>{escape(canopy_tip)}</title>{dots}
      <rect x="60" y="178" width="190" height="137" fill="transparent"/>
      {speech_bubble('Canopy', canopy_value, 78, 128, 124, 50, 'bottom')}</g></svg>'''
    return f'<article>{badge}<h3>{escape(str(row["Community"]))}</h3>{svg}</article>'


def comparison_text(a, b):
    diffs = differences(a, b)
    units = ['percentage points', '°C', 'USD', 'index points']
    lines, pattern = [], []
    for (field, label, _, _), unit in zip(FIELDS, units):
        delta = diffs[field]
        if delta is None:
            lines.append(f'{label}: Data unavailable for comparison.')
        elif delta == 0:
            lines.append(f'{label}: equal (difference 0 {unit}).')
            pattern.append(f'the same {label.lower()}')
        else:
            direction = 'higher' if delta > 0 else 'lower'
            amount = f'${abs(delta):,f}' if field == 'mhhi23' else f'{abs(delta):f} {unit}'
            lines.append(f'{label}: A is {amount} {direction} than B.')
            pattern.append(f'{direction} {label.lower()}')
    summary = ('Neighborhood A has ' + ', '.join(pattern) + ' than Neighborhood B.' if pattern else
               'No paired measurements are available.')
    return lines, summary


STORY_MEASURES = (
    ('temp_af_mean', '°C', 'temp', 'lower', 'higher'),
    ('illness_pctile', '', 'Heat-Health vulnerability', 'lower', 'higher'),
    ('mhhi23', '$', 'income', 'less', 'more'),
    ('trees17', '%', 'canopy', 'less', 'more'),
)
STORY_QUANTIZE = {
    'temp_af_mean': Decimal('0.01'),
    'illness_pctile': Decimal('0.1'),
    'mhhi23': Decimal('0.01'),
    'trees17': Decimal('0.01'),
}


def story_amount(delta, field):
    quantized = abs(delta).quantize(STORY_QUANTIZE[field], rounding=ROUND_HALF_UP)
    if field == 'mhhi23':
        return f'${quantized:,.2f}'
    text = format(quantized, 'f')
    if field == 'temp_af_mean':
        return f'{text} °C'
    if field == 'trees17':
        return f'{text}%'
    return text


def comparison_story(a, b):
    """Four-box sentence: '{A} has [measures] than {B}.'"""
    diffs = differences(a, b)
    boxes, spoken_parts = [], []
    for field, unit, noun, less_word, more_word in STORY_MEASURES:
        delta = diffs[field]
        if delta is None:
            amount, phrase = 'Data unavailable', f'{noun} unavailable'
        elif delta == 0:
            amount, phrase = story_amount(delta, field), f'the same {noun}'
        else:
            amount = story_amount(delta, field)
            phrase = f'{(more_word if delta > 0 else less_word)} {noun}'
        spoken_parts.append(phrase if delta is None else f'{amount} {phrase}')
        boxes.append(
            f'<div class="diff-box"><strong class="amount">{escape(amount)}</strong>'
            f'<span class="phrase">{escape(phrase)}</span></div>'
        )
    name_a = escape(str(a['Community']))
    name_b = escape(str(b['Community']))
    spoken = f'{name_a} has {", ".join(spoken_parts)} than {name_b}.'
    return (
        f'<article class="story" aria-label="{spoken}">'
        f'<h3><span class="name-a">{name_a}</span> has</h3>'
        f'<div class="diff-grid">{"".join(boxes)}</div>'
        f'<p class="than">than <span class="name-b">{name_b}</span>.</p></article>'
    )


def render_comparison(gdf, selected):
    selected = list(selected or [None, None])
    rows = [None, None]
    for i, region in enumerate(selected[:2]):
        match = gdf.loc[gdf.Community.eq(region)]
        if not match.empty:
            rows[i] = match.iloc[0]
    if all(row is not None for row in rows):
        third = comparison_story(*rows)
    else:
        prompt = ('Select two different regions to compare their measurements.'
                  if all(row is None for row in rows) else
                  'One region selected. Choose a second region to see differences.')
        third = f'<article class="story"><h3>Choose two neighborhoods</h3><p class="placeholder">{prompt}</p></article>'
    css = '''<style>.csa-comparison{font:14px/1.5 system-ui;color:#243342}.csa-comparison .cards{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.csa-comparison article{border:1px solid #d6dde3;border-radius:14px;padding:18px;background:#fff;min-width:0;overflow:visible;overflow-wrap:anywhere}.csa-comparison h3{font-size:18px;min-height:54px;margin:10px 0}.csa-comparison svg{width:100%;max-height:338px;overflow:visible}.csa-comparison .hotspot{cursor:pointer}.csa-comparison .hotspot .bubble{opacity:0;pointer-events:none}.csa-comparison .hotspot:hover .bubble{opacity:1}.csa-comparison .health-halo path{fill:none;stroke-width:4;stroke-linecap:butt}.csa-comparison .halo-track{stroke:#e0e5e9}.csa-comparison .halo-fill{stroke:#d9b526;animation:csa-halo-enter 220ms ease-out}.csa-comparison .halo-missing .halo-track{stroke:#aeb7c0;stroke-dasharray:2 2}.csa-comparison .badge{color:white;border-radius:50%;padding:5px 11px;font-weight:700}.csa-comparison .key{font-size:12px;color:#52616f}.csa-comparison .story{display:flex;flex-direction:column;justify-content:center}.csa-comparison .story h3,.csa-comparison .story .than{color:#243342;font-size:22px;font-weight:600;text-align:center;min-height:0;margin:10px 4px}.csa-comparison .story .name-a{color:#0072B2}.csa-comparison .story .name-b{color:#D55E00}.csa-comparison .story .placeholder{text-align:center}.csa-comparison .diff-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:8px 0 12px}.csa-comparison .diff-box{border:2.5px solid #0072B2;color:#243342;padding:16px 10px;min-height:118px;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;background:#fff}.csa-comparison .diff-box:nth-child(1){border-radius:18px 14px 16px 12px}.csa-comparison .diff-box:nth-child(2){border-radius:12px 22px 10px 18px}.csa-comparison .diff-box:nth-child(3){border-radius:16px 10px 20px 14px}.csa-comparison .diff-box:nth-child(4){border-radius:10px 16px 22px 12px}.csa-comparison .diff-box .amount{font-size:20px;font-weight:700;margin:0 0 8px}.csa-comparison .diff-box .phrase{font-size:16px;line-height:1.2}@keyframes csa-halo-enter{from{opacity:.25}to{opacity:1}}@media(prefers-reduced-motion:reduce){.csa-comparison .halo-fill{animation:none}}@media(max-width:850px){.csa-comparison .cards{grid-template-columns:1fr}}</style>'''
    return f'<section class="csa-comparison" aria-label="Neighborhood comparison">{css}<div class="cards">{profile(rows[0],0)}{profile(rows[1],1)}{third}</div></section>'
