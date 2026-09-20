function render({model, el}) {
  el.classList.add('csa-selection');
  const style = document.createElement('style');
  style.textContent = `.csa-selection .selection-controls{display:flex;gap:12px;flex-wrap:wrap;align-items:end;margin:12px 0;font:14px system-ui}.csa-selection label{display:grid;gap:6px;flex:1;min-width:200px}.csa-selection select{width:100%;padding:8px;background:white;color:#243342;border:2px solid;border-radius:6px}.csa-selection button{padding:9px 14px;background:#f5f7f9;color:#243342;border:1px solid #aab6c0;border-radius:6px;cursor:pointer}.csa-selection iframe{width:100%;height:620px;border:1px solid #d6dde3;border-radius:10px}.csa-selection .selection-status{font:14px system-ui;margin:8px 0}`;
  const controls = document.createElement('div'); controls.className = 'selection-controls';
  const names = model.get('region_names');
  const selects = [0,1].map(slot => {
    const label = document.createElement('label'); label.textContent = `Neighborhood ${'AB'[slot]}`;
    const select = document.createElement('select'); select.setAttribute('aria-label', label.textContent);
    select.style.borderColor = model.get('colors')[slot];
    const empty = new Option('Select a region (or deselect)', ''); select.add(empty);
    names.forEach(name => select.add(new Option(name, name)));
    label.append(select); controls.append(label);
    select.addEventListener('change', () => act({type:'choose', slot, id:select.value}));
    return select;
  });
  ['Clear selections', 'Swap A/B'].forEach((text, i) => {
    const button = document.createElement('button'); button.type = 'button'; button.textContent = text;
    button.addEventListener('click', () => act({type:i === 0 ? 'clear' : 'swap'})); controls.append(button);
  });
  const status = document.createElement('p'); status.className = 'selection-status'; status.setAttribute('role','status');
  const frame = document.createElement('iframe'); frame.title = 'Interactive Baltimore Community Statistical Areas map';
  frame.setAttribute('sandbox', 'allow-scripts allow-same-origin');
  frame.srcdoc = model.get('map_html');
  el.append(style, frame, controls, status);
  function send() {
    frame.contentWindow?.postMessage({channel:'csa-comparison', type:'update', selected:model.get('selected_ids'), mode:model.get('mode')}, '*');
  }
  function sync() {
    const selected = model.get('selected_ids');
    selects.forEach((select, slot) => {
      select.value = selected[slot] || '';
      Array.from(select.options).forEach(option => { option.disabled = Boolean(option.value && option.value === selected[1-slot]); });
    });
    send();
  }
  function act(action) {
    const result = transition(model.get('selected_ids'), action, names);
    status.textContent = result.message;
    model.set('selected_ids', result.selected); model.save_changes(); sync();
  }
  function message(event) {
    if (event.source !== frame.contentWindow || event.data?.channel !== 'csa-comparison') return;
    if (event.data.type === 'ready') send();
    if (event.data.type === 'click') act({type:'click', id:event.data.id});
  }
  window.addEventListener('message', message);
  model.on('change:selected_ids', sync); model.on('change:mode', send);
  status.textContent = 'Click a region for A, then a different region for B. Use either dropdown to replace a neighborhood, or click a selected region to deselect it.';
  sync();
  return () => { window.removeEventListener('message', message); model.off('change:selected_ids', sync); model.off('change:mode', send); };
}
export default {render};
