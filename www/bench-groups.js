'use strict';

// Disclosure, domain filtering, and compact density change presentation only.
// Underlying tables, IDs, and source links keep every workload separate.
const benchGroupOpenBeforeSearch = new Map();
let activeBenchCategory = 'all';
let activeBenchQuery = '';

function applyBenchFilters() {
  const q = (activeBenchQuery || '').toLowerCase().trim();
  const cat = activeBenchCategory || 'all';
  const allBlocks = Array.from(document.querySelectorAll('.bench-workload-block'));
  let visibleCount = 0;

  allBlocks.forEach(block => {
    const group = block.closest('.bench-workload-group');
    const blockCat = block.dataset.category || block.closest('.bench-cat-section')?.dataset.category || '';
    const catOk = cat === 'all' || blockCat === cat;
    const text = [block.dataset.name, block.dataset.desc, group?.dataset.groupTitle, blockCat].join(' ').toLowerCase();
    const queryOk = !q || text.includes(q);
    const show = catOk && queryOk;
    block.hidden = !show;
    if (show) visibleCount += 1;
  });

  document.querySelectorAll('.bench-workload-group').forEach(group => {
    const hasVisible = Array.from(group.querySelectorAll('.bench-workload-block')).some(block => !block.hidden);
    if (q) {
      if (!benchGroupOpenBeforeSearch.has(group)) benchGroupOpenBeforeSearch.set(group, group.open);
      group.hidden = !hasVisible;
      group.open = hasVisible;
    } else {
      group.hidden = !hasVisible;
      if (benchGroupOpenBeforeSearch.has(group)) {
        group.open = benchGroupOpenBeforeSearch.get(group);
        benchGroupOpenBeforeSearch.delete(group);
      }
    }
  });

  document.querySelectorAll('.bench-cat-section[data-category]').forEach(section => {
    const secCat = section.dataset.category || '';
    if (cat !== 'all' && secCat !== cat) {
      section.hidden = true;
      return;
    }
    const blocks = Array.from(section.querySelectorAll('.bench-workload-block'));
    section.hidden = blocks.length > 0 && !blocks.some(block => !block.hidden);
  });

  document.querySelectorAll('.bench-cat-filter-pill').forEach(btn => {
    const isActive = (btn.getAttribute('data-cat') || '') === cat;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });

  document.querySelectorAll('.bench-domain-card').forEach(card => {
    const isActive = (card.getAttribute('data-cat') || '') === cat;
    card.classList.toggle('active', isActive);
    card.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });

  const statusEl = document.getElementById('bench-filter-status');
  if (statusEl) {
    const filtered = cat !== 'all' || !!q;
    statusEl.hidden = !filtered;
    if (filtered) {
      const tpl = statusEl.dataset.tplShown || 'Showing {shown} of {total}';
      const resetLbl = statusEl.dataset.labelReset || 'Reset';
      const msg = tpl.replace('{shown}', String(visibleCount)).replace('{total}', String(allBlocks.length));
      statusEl.innerHTML = '';
      const span = document.createElement('span');
      span.textContent = msg;
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'bench-filter-reset-btn';
      btn.textContent = resetLbl;
      btn.onclick = resetBenchFilters;
      statusEl.appendChild(span);
      statusEl.appendChild(btn);
    }
  }

  const emptyEl = document.getElementById('bench-empty-state');
  if (emptyEl) {
    emptyEl.hidden = visibleCount > 0 || allBlocks.length === 0;
  }
}

function selectBenchCategory(catKey, shouldScroll) {
  activeBenchCategory = catKey || 'all';
  applyBenchFilters();
  if (typeof history !== 'undefined' && history.replaceState) {
    const nextHash = activeBenchCategory === 'all' ? '' : '#cat-' + activeBenchCategory;
    const base = location.pathname + location.search + nextHash;
    try { history.replaceState(null, '', base); } catch {}
  }
  if (shouldScroll) {
    const target = activeBenchCategory === 'all'
      ? document.getElementById('bench-workloads-root')
      : document.querySelector('.bench-sec-' + activeBenchCategory);
    if (target) {
      const nav = document.querySelector('.bench-tabs-wrapper');
      const navHeight = nav ? nav.offsetHeight : 80;
      const top = target.getBoundingClientRect().top + window.pageYOffset - navHeight - 16;
      window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    }
  }
}

function searchBenchAll(query) {
  activeBenchQuery = query || '';
  applyBenchFilters();
}

function resetBenchFilters() {
  activeBenchCategory = 'all';
  activeBenchQuery = '';
  const search = document.getElementById('bench-search');
  if (search) search.value = '';
  applyBenchFilters();
  if (typeof history !== 'undefined' && history.replaceState && location.hash.startsWith('#cat-')) {
    try { history.replaceState(null, '', location.pathname + location.search); } catch {}
  }
}

function toggleBenchCompactMode(btn) {
  const root = document.getElementById('bench-workloads-root');
  if (!root) return;
  const compact = root.classList.toggle('bench-compact-mode');
  if (btn) {
    btn.classList.toggle('active', compact);
    btn.setAttribute('aria-pressed', compact ? 'true' : 'false');
    const labelEl = btn.querySelector('span');
    if (labelEl) {
      labelEl.textContent = compact
        ? (btn.dataset.labelFull || 'Full View')
        : (btn.dataset.labelCompact || 'Compact Tables');
    }
  }
}

function toggleAllBenchGroups(btn) {
  const groups = Array.from(document.querySelectorAll('.bench-workload-group')).filter(g => !g.hidden);
  const currentlyExpanded = btn ? btn.dataset.expanded === 'true' : false;
  const nextExpanded = !currentlyExpanded;
  groups.forEach(group => { group.open = nextExpanded; });
  if (btn) {
    btn.dataset.expanded = nextExpanded ? 'true' : 'false';
    btn.classList.toggle('active', nextExpanded);
    const labelEl = btn.querySelector('span');
    if (labelEl) {
      labelEl.textContent = nextExpanded
        ? (btn.dataset.labelCollapse || 'Collapse Groups')
        : (btn.dataset.labelExpand || 'Expand Groups');
    }
  }
}

function revealBenchHash() {
  let id;
  try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
  if (id.startsWith('cat-')) {
    const catKey = id.slice(4);
    if (document.querySelector('.bench-sec-' + catKey)) {
      selectBenchCategory(catKey, true);
    }
    return;
  }
  if (!id.startsWith('workload-') && !id.startsWith('group-')) return;
  const target = document.getElementById(id);
  if (!target) return;
  activeBenchCategory = 'all';
  activeBenchQuery = '';
  const search = document.getElementById('bench-search');
  if (search) search.value = '';
  applyBenchFilters();
  const group = target.closest('.bench-workload-group');
  if (group) group.open = true;
  target.scrollIntoView({ block: 'start' });
}

window.addEventListener('hashchange', revealBenchHash);
revealBenchHash();
