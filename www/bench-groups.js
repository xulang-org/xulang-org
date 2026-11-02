'use strict';

// Disclosure changes presentation only. Tables and source links keep case IDs.
const benchGroupOpenBeforeSearch = new Map();

function searchBenchAll(query) {
  const q = (query || '').toLowerCase().trim();
  document.querySelectorAll('.bench-workload-block').forEach(block => {
    const group = block.closest('.bench-workload-group');
    const text = [block.dataset.name, block.dataset.desc, group?.dataset.groupTitle].join(' ').toLowerCase();
    block.hidden = !!q && !text.includes(q);
  });
  document.querySelectorAll('.bench-workload-group').forEach(group => {
    if (q) {
      if (!benchGroupOpenBeforeSearch.has(group)) benchGroupOpenBeforeSearch.set(group, group.open);
      group.hidden = !Array.from(group.querySelectorAll('.bench-workload-block')).some(block => !block.hidden);
      group.open = !group.hidden;
    } else {
      group.hidden = false;
      if (benchGroupOpenBeforeSearch.has(group)) group.open = benchGroupOpenBeforeSearch.get(group);
      benchGroupOpenBeforeSearch.delete(group);
    }
  });
  document.querySelectorAll('.bench-cat-section').forEach(section => {
    const blocks = Array.from(section.querySelectorAll('.bench-workload-block'));
    if (blocks.length) section.hidden = !!q && !blocks.some(block => !block.hidden);
  });
}

function revealBenchHash() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  if (!id.startsWith('workload-') && !id.startsWith('group-')) return;
  const target = document.getElementById(id);
  if (!target) return;
  const search = document.getElementById('bench-search');
  if (search) search.value = '';
  searchBenchAll('');
  const group = target.closest('.bench-workload-group');
  if (group) group.open = true;
  target.scrollIntoView({block: 'start'});
}

window.addEventListener('hashchange', revealBenchHash);
revealBenchHash();
