/**
 * exportar.js — Pastas vêm do FOLDER_MAP (config.py), igual à foto.
 */

let escolaExportar       = '';
let turmasExportar       = [];
let marksExportar        = {};
let allFolders           = [];
let pastaIdSelecionada   = '';
let pastaNomeSelecionada = '';

document.addEventListener('DOMContentLoaded', async () => {
    // Header
    try {
        const r = await fetch('/api/get_current_user');
        const d = await r.json();
        document.getElementById('nome-usuario').textContent    = d.username || '';
        document.getElementById('periodo-usuario').textContent = d.periodo  || '';
    } catch(e) {}
    document.getElementById('data-atual').textContent =
        new Date().toLocaleDateString('pt-BR', {
            weekday:'long', day:'numeric', month:'long', year:'numeric'
        });

    // Escola vinda de salas.js via sessionStorage
    escolaExportar = sessionStorage.getItem('exportar_escola') || '';
    if (escolaExportar) {
        document.getElementById('escola-wrap').style.display = '';
        document.getElementById('escola-label').textContent  = escolaExportar;
        await carregarDadosEscola(escolaExportar);
    }

    await carregarPastas();

    // Busca/filtro no campo
    document.getElementById('folder-search').addEventListener('input', filtrarPastas);
    document.getElementById('folder-search').addEventListener('focus', abrirDropdown);
});

// ── Dados da escola ──────────────────────────────────────────────
async function carregarDadosEscola(escola) {
    try {
        const res  = await fetch('/api/get_salas_turmas', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({escola})
        });
        const data = await res.json();
        turmasExportar = data.turmas || [];
        marksExportar  = data.marks  || {};
    } catch(e) { console.error(e); }
}

// ── Pastas do FOLDER_MAP ─────────────────────────────────────────
async function carregarPastas() {
    try {
        const res  = await fetch('/api/list_drive_folders');
        const data = await res.json();
        allFolders = data.folders || [];
        // Não abre o dropdown ainda — só carrega
    } catch(e) {
        console.error('Erro ao carregar pastas:', e);
        allFolders = [];
    }
}

// ── Dropdown ─────────────────────────────────────────────────────
function abrirDropdown() {
    renderDropdown(allFolders);
}

function toggleDropdown() {
    const list = document.getElementById('folder-list');
    if (list.style.display === 'none' || !list.style.display) {
        renderDropdown(allFolders);
    } else {
        list.style.display = 'none';
    }
}

function filtrarPastas() {
    const q = document.getElementById('folder-search').value.toLowerCase();
    const filtered = q
        ? allFolders.filter(f => f.name.toLowerCase().includes(q))
        : allFolders;
    renderDropdown(filtered);
}

function renderDropdown(folders) {
    const list = document.getElementById('folder-list');
    if (!folders.length) {
        list.innerHTML = `<div style="padding:.75rem 1rem;color:#94a3b8;font-size:.875rem">
            Nenhuma pasta encontrada</div>`;
    } else {
        list.innerHTML = folders.map(f => `
            <div class="folder-item ${f.id === pastaIdSelecionada ? 'selected' : ''}"
                 onclick="selecionarPasta('${f.id}', '${f.name.replace(/'/g,"\\'")}')">
                ${f.name}
            </div>
        `).join('');
    }
    list.style.display = '';
}

function selecionarPasta(id, nome) {
    pastaIdSelecionada   = id;
    pastaNomeSelecionada = nome;
    document.getElementById('folder-search').value      = nome;
    document.getElementById('folder-list').style.display = 'none';
}

// Fecha ao clicar fora
document.addEventListener('click', e => {
    if (!e.target.closest('.folder-search-wrap') && !e.target.closest('#folder-list')) {
        const list = document.getElementById('folder-list');
        if (list) list.style.display = 'none';
    }
});

// ── Salvar no Drive ──────────────────────────────────────────────
async function salvarNoDrive() {
    if (!pastaIdSelecionada) {
        mostrarResultado('⚠️ Selecione uma pasta antes de salvar.', false);
        return;
    }

    const btn = document.getElementById('btn-drive');
    btn.disabled  = true;
    btn.innerHTML = '<i class="fas fa-circle-notch" style="animation:spin .8s linear infinite;display:inline-block"></i> Enviando…';

    try {
        const res = await fetch('/api/export_excel_drive', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                escola:    escolaExportar,
                folder_id: pastaIdSelecionada,
                turmas:    turmasExportar,
                marks:     marksExportar
            })
        });
        const data = await res.json();
        if (data.success) {
            mostrarResultado('✅ Excel salvo no Drive com sucesso!', true);
        } else {
            mostrarResultado('❌ ' + (data.error || 'Falha no envio'), false);
        }
    } catch(e) {
        mostrarResultado('❌ Erro de conexão ao enviar.', false);
    } finally {
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Salvar no Drive';
    }
}

// ── Baixar Excel ─────────────────────────────────────────────────
async function baixarExcel() {
    try {
        const res = await fetch('/api/exportar_relatorio_salas', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                escola: escolaExportar,
                turmas: turmasExportar,
                marks:  marksExportar
            })
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const blob = await res.blob();
        const url  = URL.createObjectURL(blob);
        const a    = document.createElement('a');
        const date = new Date().toISOString().slice(0,10);
        a.href     = url;
        a.download = `conferencia_salas_${escolaExportar || 'salas'}_${date}.xlsx`.replace(/\s+/g,'_');
        a.click();
        URL.revokeObjectURL(url);
    } catch(e) {
        alert('Erro ao baixar: ' + e.message);
    }
}

// ── Resultado ─────────────────────────────────────────────────────
function mostrarResultado(msg, ok) {
    const el = document.getElementById('export-result');
    el.textContent   = msg;
    el.className     = ok ? 'result-ok' : 'result-fail';
    el.style.display = '';
    if (ok) setTimeout(() => { el.style.display = 'none'; }, 6000);
}
