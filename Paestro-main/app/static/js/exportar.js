/**
 * exportar.js
 * Tela de exportar: busca pasta no Drive, salva Excel, ou baixa localmente.
 * A escola vem via sessionStorage (enviada por salas.js ao clicar Exportar).
 */

let escolaExportar  = '';
let turmasExportar  = [];
let marksExportar   = {};
let allFolders      = [];   // pastas carregadas do Drive
let pastaIdSelecionada   = '';
let pastaNomeSelecionada = '';

document.addEventListener('DOMContentLoaded', async () => {
    // Header
    try {
        const r = await fetch('/api/get_current_user');
        const d = await r.json();
        document.getElementById('nome-usuario').textContent   = d.username || '';
        document.getElementById('periodo-usuario').textContent = d.periodo  || '';
    } catch(e) {}
    document.getElementById('data-atual').textContent =
        new Date().toLocaleDateString('pt-BR', {weekday:'long', day:'numeric', month:'long', year:'numeric'});

    // Escola vinda de salas.js
    escolaExportar = sessionStorage.getItem('exportar_escola') || '';
    if (escolaExportar) {
        document.getElementById('escola-wrap').style.display = '';
        document.getElementById('escola-label').textContent  = escolaExportar;
        await carregarDadosEscola(escolaExportar);
    }

    // Carrega pastas do Drive
    await carregarPastas();
});

// ── Dados da escola ──────────────────────────────────────────────
async function carregarDadosEscola(escola) {
    try {
        const res  = await fetch('/api/get_salas_turmas', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({escola})
        });
        const data = await res.json();
        turmasExportar = data.turmas || [];
        marksExportar  = data.marks  || {};
    } catch(e) { console.error(e); }
}

// ── Pastas do Drive ──────────────────────────────────────────────
async function carregarPastas() {
    try {
        const res  = await fetch('/api/list_drive_folders');
        const data = await res.json();
        allFolders = data.folders || [];

        // Se não houver subpastas, usa a pasta padrão como única opção
        if (!allFolders.length && data.default_folder_id) {
            allFolders = [{id: data.default_folder_id, name: 'Pasta principal (Secretaria)'}];
        }

        renderFolderList(allFolders);
    } catch(e) {
        console.error('Erro ao carregar pastas:', e);
        allFolders = [];
    }
}

function renderFolderList(folders) {
    const list = document.getElementById('folder-list');
    if (!folders.length) {
        list.innerHTML = '<div class="folder-item" style="color:#94a3b8">Nenhuma pasta encontrada</div>';
        return;
    }
    list.innerHTML = folders.map(f => `
        <div class="folder-item ${f.id === pastaIdSelecionada ? 'selected' : ''}"
             onclick="selecionarPasta('${f.id}', '${f.name.replace(/'/g,"\\'")}')">
            <i class="fas fa-folder"></i> ${f.name}
        </div>
    `).join('');
}

function filtrarPastas() {
    const q = document.getElementById('folder-search').value.toLowerCase();
    const filtered = allFolders.filter(f => f.name.toLowerCase().includes(q));
    renderFolderList(filtered);
    document.getElementById('folder-list').style.display = '';
}

function toggleDropdown() {
    const list = document.getElementById('folder-list');
    renderFolderList(allFolders);
    list.style.display = list.style.display === 'none' || !list.style.display ? '' : 'none';
}

function selecionarPasta(id, nome) {
    pastaIdSelecionada   = id;
    pastaNomeSelecionada = nome;

    document.getElementById('folder-search').value = nome;
    document.getElementById('folder-list').style.display = 'none';

    document.getElementById('pasta-selecionada').style.display  = '';
    document.getElementById('pasta-nome-label').textContent = nome;

    // Re-renderiza com item marcado
    renderFolderList(allFolders);
}

// Fecha dropdown ao clicar fora
document.addEventListener('click', e => {
    if (!e.target.closest('.folder-search-wrap') && !e.target.closest('.folder-list')) {
        document.getElementById('folder-list').style.display = 'none';
    }
});

// ── Salvar no Drive ──────────────────────────────────────────────
async function salvarNoDrive() {
    if (!pastaIdSelecionada) {
        mostrarResultado('❌ Selecione uma pasta do Drive primeiro.', false);
        return;
    }

    const btn = document.getElementById('btn-drive');
    btn.disabled  = true;
    btn.innerHTML = '<i class="fas fa-circle-notch loading-spin"></i> Enviando…';

    try {
        const res = await fetch('/api/export_excel_drive', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
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
            mostrarResultado('❌ Erro: ' + (data.error || 'Falha no envio'), false);
        }
    } catch(e) {
        mostrarResultado('❌ Erro de conexão ao enviar.', false);
        console.error(e);
    } finally {
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Salvar no Drive';
    }
}

// ── Baixar Excel localmente ──────────────────────────────────────
async function baixarExcel() {
    try {
        const res = await fetch('/api/exportar_relatorio_salas', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
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
        const nome = escolaExportar || 'conferencia_salas';
        a.href     = url;
        a.download = `conferencia_salas_${nome}_${date}.xlsx`.replace(/\s+/g,'_');
        a.click();
        URL.revokeObjectURL(url);
    } catch(e) {
        alert('Erro ao baixar o arquivo: ' + e.message);
        console.error(e);
    }
}

// ── Resultado ─────────────────────────────────────────────────────
function mostrarResultado(msg, ok) {
    const el = document.getElementById('export-result');
    el.textContent  = msg;
    el.className    = ok ? 'result-ok' : 'result-fail';
    el.style.display = '';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}
