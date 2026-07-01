/**
 * salas.js — Conferência de Salas (SN / NE / C)
 * Carrega turmas do servidor, gerencia marcações, salva e exporta.
 */

let TURMAS  = [];
let marks   = {};          // { index: { status, sala_real, obs } }
let currentFilter = 'all';

// ── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadSchools();
  loadMarks();
  setupFilters();

  document.getElementById('salas-search').addEventListener('input', renderTable);
  document.getElementById('salvar-salas-btn').addEventListener('click', saveMarks);
  document.getElementById('exportar-salas-btn').addEventListener('click', exportarExcel);
  document.getElementById('exportar-salas-xml-btn').addEventListener('click', exportarXML);
  document.getElementById('limpar-salas-btn').addEventListener('click', clearAll);
});

// ── Escolas e Turmas ────────────────────────────────────────────
async function loadSchools() {
  try {
    const res  = await fetch('/api/get_schools');
    const data = await res.json();
    const sel  = document.getElementById('escola-salas-select');
    sel.innerHTML = '<option value="">Selecione a escola</option>';
    (data.schools || []).forEach(e => {
      sel.innerHTML += `<option value="${e}">${e}</option>`;
    });
    sel.addEventListener('change', () => loadTurmas(sel.value));
  } catch (e) { console.error(e); }
}

async function loadTurmas(escola) {
  if (!escola) { TURMAS = []; renderTable(); return; }
  try {
    const res  = await fetch('/api/get_salas_turmas', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({escola})
    });
    const data = await res.json();
    TURMAS = data.turmas || [];
    // Marks salvos no servidor têm prioridade sobre o localStorage para esta escola
    if (data.marks && Object.keys(data.marks).length) {
      marks = data.marks;
      saveMarksLocal();
    }
    currentFilter = 'all';
    document.querySelectorAll('.filtro-pill').forEach(p => p.classList.remove('active'));
    const allBtn = document.querySelector('.filtro-pill[data-f="all"]');
    if (allBtn) allBtn.classList.add('active');
    renderSerieFilters();
    renderTable();
    updateStats();
  } catch(e) { console.error(e); }
}

// ── Filtros de série dinâmicos (escolas: 5º-9º ano | creches: GT 0-5) ──
function renderSerieFilters() {
  const container = document.getElementById('filtros-serie-dinamicos');
  if (!container) return;

  const series = new Set();
  TURMAS.forEach(d => {
    const mGt = d.turma.match(/^GT\s*(\d+)/i);
    const mAno = d.turma.match(/^(\d+)[ºo°]\s*ANO/i);
    if (mGt) series.add('GT' + mGt[1]);
    else if (mAno) series.add(mAno[1]);
  });

  const sorted = Array.from(series).sort((a, b) => {
    const na = parseInt(a.replace('GT', ''));
    const nb = parseInt(b.replace('GT', ''));
    return na - nb;
  });

  container.innerHTML = sorted.map(s => {
    const label = s.startsWith('GT') ? `GT ${s.replace('GT','')}` : `${s}º Ano`;
    return `<button class="filtro-pill" data-f="${s}">${label}</button>`;
  }).join('');

  container.querySelectorAll('.filtro-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filtro-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.f;
      renderTable();
    });
  });
}

// ── Marcações (localStorage) ────────────────────────────────────
function loadMarks() {
  try { marks = JSON.parse(localStorage.getItem('paestro_salas_marks') || '{}'); }
  catch(e) { marks = {}; }
}
function saveMarksLocal() {
  localStorage.setItem('paestro_salas_marks', JSON.stringify(marks));
}

// ── Filtros ──────────────────────────────────────────────────────
function setupFilters() {
  document.querySelectorAll('.filtro-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filtro-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentFilter = btn.dataset.f;
      renderTable();
    });
  });
}

function getVisible() {
  const q = document.getElementById('salas-search').value.toLowerCase();
  return TURMAS.filter((d, i) => {
    const m = marks[i] || {};
    let pass = true;
    if      (currentFilter === 'NE')   pass = m.status === 'NE';
    else if (currentFilter === 'C')    pass = m.status === 'C';
    else if (currentFilter === 'pend') pass = !m.status;
    else if (currentFilter === 'MANHÃ' || currentFilter === 'TARDE' || currentFilter === 'INTEGRAL') pass = d.turno === currentFilter;
    else if (currentFilter.startsWith('GT')) {
      const num = currentFilter.replace('GT', '');
      pass = new RegExp('^GT\\s*' + num + '\\b', 'i').test(d.turma);
    }
    else if (currentFilter !== 'all')  pass = d.turma.startsWith(currentFilter + 'º');
    if (!pass) return false;
    if (q) return d.turma.toLowerCase().includes(q) || d.sala.toLowerCase().includes(q);
    return true;
  });
}

// ── Render Table ─────────────────────────────────────────────────
function renderTable() {
  const tbody = document.getElementById('salas-tbody');
  const empty = document.getElementById('salas-empty');
  const visible = getVisible();

  updateStats();

  if (!visible.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';

  tbody.innerHTML = visible.map(d => {
    const i      = TURMAS.indexOf(d);
    const m      = marks[i] || {};
    const status = m.status || null;
    const tcls   = d.turno === 'MANHÃ' ? 'turno-manha' : d.turno === 'TARDE' ? 'turno-tarde' : 'turno-integral';

    const snCls = status === 'SN' ? 'sel-SN' : '';
    const neCls = status === 'NE' ? 'sel-NE' : '';
    const cCls  = status === 'C'  ? 'sel-C'  : '';

    const salaRealVis = status === 'NE' ? 'visible' : '';
    const clearBtn    = status
      ? `<button class="opt-btn clear" onclick="clearMark(${i})">✕</button>` : '';

    return `<tr id="salas-row-${i}">
      <td style="color:#94a3b8;font-size:.8rem">${TURMAS.indexOf(d)+1}</td>
      <td style="font-weight:500">${d.turma}</td>
      <td class="sala-col">${d.sala}</td>
      <td><span class="turno-badge ${tcls}">${d.turno}</span></td>
      <td>
        <div class="opt-group">
          <button class="opt-btn ${snCls}" onclick="setStatus(${i},'SN')">SN</button>
          <button class="opt-btn ${neCls}" onclick="setStatus(${i},'NE')">NE</button>
          <button class="opt-btn ${cCls}"  onclick="setStatus(${i},'C')">C</button>
          ${clearBtn}
        </div>
        <input class="sala-real-input ${salaRealVis}"
               id="sala-real-${i}"
               placeholder="Sala real…"
               value="${m.sala_real||''}"
               oninput="setMeta(${i},'sala_real',this.value)"/>
      </td>
      <td>
        <input class="obs-input"
               placeholder="Observação…"
               value="${m.obs||''}"
               oninput="setMeta(${i},'obs',this.value)"/>
      </td>
    </tr>`;
  }).join('');
}

// ── Status / Marcação ────────────────────────────────────────────
function setStatus(i, st) {
  if (!marks[i]) marks[i] = {};
  marks[i].status = st;
  if (st !== 'NE') marks[i].sala_real = '';
  saveMarksLocal();
  renderTable();
  const msgs = { SN:'✅ SN registrado', NE:'⚠️ NE — informe a sala real', C:'✔️ C registrado' };
  toast(msgs[st]);
}

function setMeta(i, key, val) {
  if (!marks[i]) marks[i] = {};
  marks[i][key] = val;
  saveMarksLocal();
}

function clearMark(i) {
  delete marks[i];
  saveMarksLocal();
  renderTable();
}

function clearAll() {
  if (!confirm('Limpar todas as marcações de salas?')) return;
  marks = {};
  saveMarksLocal();
  renderTable();
  toast('🔄 Marcações limpas');
}

// ── Stats ────────────────────────────────────────────────────────
function updateStats() {
  const total = TURMAS.length;
  const sn  = Object.values(marks).filter(m => m.status === 'SN').length;
  const ne  = Object.values(marks).filter(m => m.status === 'NE').length;
  const c   = Object.values(marks).filter(m => m.status === 'C').length;
  const done= sn + ne + c;

  document.getElementById('s-total').textContent = total;
  document.getElementById('s-sn').textContent    = sn;
  document.getElementById('s-ne').textContent    = ne;
  document.getElementById('s-c').textContent     = c;
  document.getElementById('s-pend').textContent  = total - done;
  document.getElementById('prog-txt').textContent= `${done} de ${total} verificadas`;
  document.getElementById('prog-bar').value      = done;
  document.getElementById('prog-bar').max        = total || 1;
}

// ── Salvar no servidor ──────────────────────────────────────────
async function saveMarks() {
  const escola = document.getElementById('escola-salas-select').value;
  if (!escola) { toast('⚠️ Selecione uma escola'); return; }

  try {
    const res = await fetch('/api/save_salas_marks', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ escola, turmas: TURMAS, marks })
    });
    const data = await res.json();
    if (data.success) toast('💾 Marcações salvas!');
    else toast('❌ Erro ao salvar: ' + data.error);
  } catch(e) { toast('❌ Erro de conexão'); }
}

// ── Exportar Excel ───────────────────────────────────────────────
async function exportarExcel() {
  const escola = document.getElementById('escola-salas-select').value;
  if (!escola) { toast('⚠️ Selecione uma escola'); return; }
  if (!TURMAS.length) { toast('⚠️ Nenhuma turma carregada'); return; }

  const btn = document.getElementById('exportar-salas-btn');
  btn.disabled = true;
  btn.textContent = '⏳ Gerando…';

  try {
    const res = await fetch('/api/exportar_relatorio_salas', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ escola, turmas: TURMAS, marks })
    });

    if (!res.ok) throw new Error('Erro HTTP ' + res.status);

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const date = new Date().toISOString().slice(0,10);
    a.href     = url;
    a.download = `conferencia_salas_${date}.xlsx`;
    a.click();
    URL.revokeObjectURL(url);
    toast('✅ Excel exportado com sucesso!');
  } catch(e) {
    toast('❌ Erro ao gerar Excel');
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-file-excel"></i> Exportar Excel';
  }
}

// ── Exportar XML ─────────────────────────────────────────────────
async function exportarXML() {
  const escola = document.getElementById('escola-salas-select').value;
  if (!escola) { toast('⚠️ Selecione uma escola'); return; }
  if (!TURMAS.length) { toast('⚠️ Nenhuma turma carregada'); return; }

  const btn = document.getElementById('exportar-salas-xml-btn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Gerando…';

  try {
    const res = await fetch('/api/exportar_relatorio_xml', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ escola, turmas: TURMAS, marks })
    });

    if (!res.ok) throw new Error('Erro HTTP ' + res.status);

    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    const date = new Date().toISOString().slice(0,10);
    a.href     = url;
    a.download = `conferencia_salas_${escola}_${date}.xml`.replace(/\s+/g,'_');
    a.click();
    URL.revokeObjectURL(url);
    toast('✅ XML exportado com sucesso!');
  } catch(e) {
    toast('❌ Erro ao gerar XML');
    console.error(e);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-file-code"></i> Exportar XML';
  }
}


let toastTimer;
function toast(msg) {
  const el = document.getElementById('salas-toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}
