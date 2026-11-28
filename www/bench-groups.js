'use strict';

// Disclosure, domain filtering, and compact density change presentation only.
// Underlying tables, IDs, and source links keep every workload separate.
const benchGroupOpenBeforeSearch = new Map();
let activeBenchCategory = 'all';
let activeBenchQuery = '';
let activeBenchPlatform = 'all';
let benchMatrixSortCol = '';
let benchMatrixSortAsc = true;

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

  document.querySelectorAll('.bench-matrix-row').forEach(row => {
    const rCat = row.dataset.category || '';
    const catOk = cat === 'all' || rCat === cat;
    const text = [row.dataset.name, row.dataset.desc, rCat].join(' ').toLowerCase();
    const queryOk = !q || text.includes(q);
    row.hidden = !(catOk && queryOk);
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

function toggleBenchMatrixView(btn) {
  const matrix = document.getElementById('bench-quick-matrix');
  const root = document.getElementById('bench-workloads-root');
  if (!matrix || !root) return;
  const showMatrix = matrix.hidden;
  matrix.hidden = !showMatrix;
  root.hidden = showMatrix;
  if (btn) {
    btn.classList.toggle('active', showMatrix);
    btn.setAttribute('aria-pressed', showMatrix ? 'true' : 'false');
    const labelEl = btn.querySelector('span');
    if (labelEl) {
      labelEl.textContent = showMatrix
        ? (btn.dataset.labelCards || 'Card Charts')
        : (btn.dataset.labelMatrix || 'Dense Matrix');
    }
  }
}

function fmtMatrixMs(v) {
  if (v === null || v === undefined || v <= 0) return '—';
  return v >= 100 ? v.toFixed(1) + ' ms' : v.toFixed(2) + ' ms';
}

function ratioClassFor(v) {
  if (v === null || v === undefined || v <= 0) return '';
  if (v <= 1.0) return 'is-fast';
  if (v <= 1.2) return 'is-close';
  return 'is-slow';
}

function refreshBenchMatrixPlatform(pid) {
  activeBenchPlatform = pid || 'all';
  document.querySelectorAll('.bench-matrix-row').forEach(row => {
    let payload = {};
    try { payload = JSON.parse(row.dataset.metrics || '{}'); } catch { return; }
    const m = payload[activeBenchPlatform] || payload.all || {};
    const setCell = (col, text, ratioVal) => {
      const td = row.querySelector('[data-col="' + col + '"]');
      if (!td) return;
      td.textContent = text;
      if (col === 'rc' || col === 'rr') {
        td.classList.remove('is-fast', 'is-close', 'is-slow');
        const cls = ratioClassFor(ratioVal);
        if (cls) td.classList.add(cls);
      }
    };
    setCell('xu', fmtMatrixMs(m.xu));
    setCell('c', fmtMatrixMs(m.c));
    setCell('rc', m.rc ? m.rc.toFixed(2) + '×' : '—', m.rc);
    setCell('r', fmtMatrixMs(m.r));
    setCell('rr', m.rr ? m.rr.toFixed(2) + '×' : '—', m.rr);
    setCell('rss', m.rss ? m.rss.toFixed(1) + ' MiB' : '—');
    setCell('kb', m.kb ? Math.round(m.kb) + ' KiB' : '—');
  });
}

function sortBenchMatrix(colKey, btn) {
  const tbody = document.getElementById('bench-quick-matrix-body');
  if (!tbody) return;
  if (benchMatrixSortCol === colKey) {
    benchMatrixSortAsc = !benchMatrixSortAsc;
  } else {
    benchMatrixSortCol = colKey;
    benchMatrixSortAsc = true;
  }
  const rows = Array.from(tbody.querySelectorAll('.bench-matrix-row'));
  rows.sort((a, b) => {
    let pa = {}; let pb = {};
    try { pa = JSON.parse(a.dataset.metrics || '{}'); } catch {}
    try { pb = JSON.parse(b.dataset.metrics || '{}'); } catch {}
    const ma = (pa[activeBenchPlatform] || pa.all || {})[colKey];
    const mb = (pb[activeBenchPlatform] || pb.all || {})[colKey];
    const va = (ma !== null && ma !== undefined && ma > 0) ? ma : 1e18;
    const vb = (mb !== null && mb !== undefined && mb > 0) ? mb : 1e18;
    if (va === vb) return 0;
    return benchMatrixSortAsc ? va - vb : vb - va;
  });
  rows.forEach(r => tbody.appendChild(r));
  document.querySelectorAll('.bench-matrix-sort').forEach(b => b.classList.remove('is-sorted'));
  if (btn) btn.classList.add('is-sorted');
}

function jumpToWorkloadCard(wname) {
  const matrix = document.getElementById('bench-quick-matrix');
  const root = document.getElementById('bench-workloads-root');
  const toggleBtn = document.getElementById('bench-matrix-toggle-btn');
  if (matrix && root && !matrix.hidden) {
    matrix.hidden = true;
    root.hidden = false;
    if (toggleBtn) {
      toggleBtn.classList.remove('active');
      toggleBtn.setAttribute('aria-pressed', 'false');
      const labelEl = toggleBtn.querySelector('span');
      if (labelEl) labelEl.textContent = toggleBtn.dataset.labelMatrix || 'Dense Matrix';
    }
  }
  const target = document.getElementById('workload-' + wname);
  if (target) {
    const group = target.closest('.bench-workload-group');
    if (group) group.open = true;
    const top = target.getBoundingClientRect().top + window.pageYOffset - benchStickyOffset();
    window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
  }
}

function benchStickyOffset() {
  const header = document.querySelector('.header-bar');
  const headerH = header ? header.offsetHeight : 56;
  const nav = document.querySelector('.bench-tabs-wrapper');
  const navSticky = nav && getComputedStyle(nav).position === 'sticky';
  const navH = navSticky ? nav.offsetHeight : 0;
  return headerH + navH + 16;
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
      const top = target.getBoundingClientRect().top + window.pageYOffset - benchStickyOffset();
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
  const el = document.getElementById(id);
  if (el) {
    const drawer = el.closest('.bench-section-drawer');
    if (drawer) drawer.open = true;
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
