// Pure state transitions shared by the widget and Node tests. Slots never compact.
export function transition(selected, action, names) {
  const next = [...selected];
  if (action.type === 'clear') return {selected: [null, null], message: 'Selections cleared.'};
  if (action.type === 'swap') return {selected: [next[1], next[0]], message: 'A and B swapped.'};
  const id = action.id || null;
  if (id !== null && !names.includes(id)) return {selected: next, message: 'Unknown region.'};
  if (action.type === 'click') {
    const existing = next.indexOf(id);
    if (existing !== -1) next[existing] = null;
    else {
      const empty = next.indexOf(null);
      if (empty === -1) return {selected: next, message: 'Both slots are filled. Use either neighborhood dropdown to replace its selection.'};
      next[empty] = id;
    }
  } else if (action.type === 'choose') {
    const slot = action.slot;
    if (![0, 1].includes(slot)) return {selected: next, message: 'Unknown slot.'};
    if (id !== null && next[1-slot] === id) return {selected: next, message: 'Choose two different regions.'};
    next[slot] = id;
  }
  return {selected: next, message: next.every(Boolean) ? 'Two regions selected. Use either neighborhood dropdown to choose another.' : 'Choose a region for each empty slot.'};
}
