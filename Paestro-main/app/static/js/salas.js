/**
 * salas.js — Conferência de Salas (SN / NE / C)
 * - Sem filtros de série (só busca)
 * - Troca de escola limpa os dados anteriores
 * - Exportar só libera quando todas as turmas estiverem analisadas
 * - Exportar redireciona para /exportar passando a escola via sessionStorage
 */

let TURMAS       = [];
let marks        = {};
let escolaAtual  = '';

// ── Init ────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadSchools();

  document.getElementById('salas-search').addEventListener('input', renderTable);
  document.getElementById('salvar-salas-btn').addEventListener('click', saveMarks);
  document.getElementById('exportar-salas-btn').addEventListener('click', irParaExportar);
  document.getElementById('limpar-salas-btn').addEventListener('click', clearAll);
});

// ── Escolas ──────────────────────────────────────────────────────
async function loadSchools() {
  try {
    const res  = await fetch('/api/get_schools');
    const data = await res.json();
    const sel  = document.getElementById('escola-salas-select');
    sel.innerHTML = '<option value="">Selecione a escola</option>';
    (data.schools || []).forEach(e => {
      sel.innerHTML += `<option value="${e}">${e}</option>`;
    });
    sel.addEventListener('change', () => {
      const nova = sel.value;
      if (nova === escolaAtual) return;
      // Limpa tudo ao trocar de escola
      marks       = {};
      TURMAS      = [];
      escolaAtual = nova;
      renderTable();
      updateStats();
      loadTurmas(nova);
    });
  } catch (e) { console.error(e); }
}

async function loadTurmas(escola) {
  if (!escola) { renderTable(); return; }
  try {
    const res  = await fetch('/api/get_salas_turmas', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({escola})
    });
    const data = await res.json();
    TURMAS = data.turmas || [];

    // Carrega marks salvos no servidor para esta escola
    marks = (data.marks && Object.keys(data.marks).length) ? data.marks : {};

    renderTable();
    updateStats();
  } catch(e) { console.error(e); }
}

// ── Render Tabela ────────────────────────────────────────────────
function getVisible() {
  const q = document.getElementById('salas-search').value.toLowerCase();
  if (!q) return TURMAS;
  return TURMAS.filter(d =>
    d.turma.toLowerCase().includes(q) || d.sala.toLowerCase().includes(q)
  );
}

function renderTable() {
  const tbody  = document.getElementById('salas-tbody');
  const empty  = document.getElementById('salas-empty');
  const visible = getVisible();

  updateStats();

  if (!TURMAS.length) {
    tbody.innerHTML = '';
    empty.style.display = '';
    return;
  }
  empty.style.display = 'none';

  tbody.innerHTML = visible.map(d => {
    const i      = TURMAS.indexOf(d);
    const m      = marks[i] || {};
    const status = m.status || null;
    const tcls   = d.turno === 'MANHÃ'    ? 'turno-manha'
                 : d.turno === 'TARDE'    ? 'turno-tarde'
                 : 'turno-integral';

    const snCls = status === 'SN' ? 'sel-SN' : '';
    const neCls = status === 'NE' ? 'sel-NE' : '';
    const cCls  = status === 'C'  ? 'sel-C'  : '';
    const clearBtn = status
      ? `<button class="opt-btn clear" onclick="clearMark(${i})">✕</button>` : '';

    return `<tr id="salas-row-${i}">
      <td style="color:#94a3b8;font-size:.8rem">${i + 1}</td>
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
        <input class="sala-real-input ${status === 'NE' ? 'visible' : ''}"
               id="sala-real-${i}"
               placeholder="Sala real…"
               value="${m.sala_real || ''}"
               oninput="setMeta(${i},'sala_real',this.value)"/>
      </td>
      <td>
        <input class="obs-input"
               placeholder="Observação…"
               value="${m.obs || ''}"
               oninput="setMeta(${i},'obs',this.value)"/>
      </td>
    </tr>`;
  }).join('');
}

// ── Status ───────────────────────────────────────────────────────
function setStatus(i, st) {
  if (!marks[i]) marks[i] = {};
  marks[i].status = st;
  if (st !== 'NE') marks[i].sala_real = '';
  renderTable();
  const msgs = { SN:'✅ SN registrado', NE:'⚠️ NE — informe a sala real', C:'✔️ C registrado' };
  toast(msgs[st]);
}

function setMeta(i, key, val) {
  if (!marks[i]) marks[i] = {};
  marks[i][key] = val;
}

function clearMark(i) {
  delete marks[i];
  renderTable();
}

function clearAll() {
  if (!confirm('Limpar todas as marcações de salas?')) return;
  marks = {};
  renderTable();
  toast('🔄 Marcações limpas');
}

// ── Stats + controle do botão Exportar ──────────────────────────
function updateStats() {
  const total = TURMAS.length;
  const sn    = Object.values(marks).filter(m => m.status === 'SN').length;
  const ne    = Object.values(marks).filter(m => m.status === 'NE').length;
  const c     = Object.values(marks).filter(m => m.status === 'C').length;
  const done  = sn + ne + c;
  const pend  = total - done;

  document.getElementById('s-total').textContent = total;
  document.getElementById('s-sn').textContent    = sn;
  document.getElementById('s-ne').textContent    = ne;
  document.getElementById('s-c').textContent     = c;
  document.getElementById('s-pend').textContent  = pend;
  document.getElementById('prog-txt').textContent = `${done} de ${total} verificadas`;
  document.getElementById('prog-bar').value = done;
  document.getElementById('prog-bar').max   = total || 1;

  // Botão exportar: só habilitado quando todas analisadas
  const exportBtn   = document.getElementById('exportar-salas-btn');
  const avisoEl     = document.getElementById('aviso-pendentes');
  const avisoNumEl  = document.getElementById('aviso-pend-num');
  const tudoPronto  = total > 0 && pend === 0;

  exportBtn.disabled = !tudoPronto;
  exportBtn.style.opacity = tudoPronto ? '1' : '0.45';
  exportBtn.title = tudoPronto ? '' : `Faltam ${pend} turma(s) para analisar`;

  avisoEl.style.display   = (!tudoPronto && total > 0) ? '' : 'none';
  avisoNumEl.textContent  = pend;
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

// ── Ir para Exportar (salva e redireciona) ────────────────────────
async function irParaExportar() {
  const escola = document.getElementById('escola-salas-select').value;
  if (!escola)       { toast('⚠️ Selecione uma escola'); return; }
  if (!TURMAS.length){ toast('⚠️ Nenhuma turma carregada'); return; }

  const total = TURMAS.length;
  const done  = Object.values(marks).filter(m => m.status).length;
  if (done < total) {
    toast(`⚠️ Ainda faltam ${total - done} turma(s) para analisar`);
    return;
  }

  // Salva no servidor antes de redirecionar
  try {
    await fetch('/api/save_salas_marks', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ escola, turmas: TURMAS, marks })
    });
  } catch(e) {}

  // Passa a escola selecionada para a tela de exportar
  sessionStorage.setItem('exportar_escola', escola);
  window.location.href = '/exportar';
}

// ── Toast ────────────────────────────────────────────────────────
let toastTimer;
function toast(msg) {
  const el = document.getElementById('salas-toast');
  el.textContent = msg;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2800);
}
