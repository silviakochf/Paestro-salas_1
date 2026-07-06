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

    escolaExportar = sessionStorage.getItem('exportar_escola') || '';
    if (escolaExportar) {
        document.getElementById('escola-wrap').style.display = '';
        document.getElementById('escola-label').textContent  = escolaExportar;
        await carregarDadosEscola(escolaExportar);
    }

    await carregarPastas();
});

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

async function carregarPastas() {
    try {
        const res  = await fetch('/api/list_drive_folders');
        const data = await res.json();
        allFolders = data.folders || [];

        const input = document.getElementById('folder-search');
        input.addEventListener('focus', () => renderDropdown(allFolders));
        input.addEventListener('input', filtrarPastas);

    } catch(e) {
        console.error('Erro ao carregar pastas:', e);
        allFolders = [];
    }
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
        list.innerHTML = '<div style="padding:.75rem 1rem;color:#94a3b8;font-size:.875rem">Nenhuma pasta encontrada</div>';
    } else {
        list.innerHTML = folders.map(f => {
            const sel = f.id === pastaIdSelecionada ? 'selected' : '';
            const nome = f.name.replace(/'/g, "\\'");
            return '<div class="folder-item ' + sel + '" onclick="selecionarPasta(\'' + f.id + '\', \'' + nome + '\')">' + f.name + '</div>';
        }).join('');
    }
    list.style.display = '';
}

function selecionarPasta(id, nome) {
    pastaIdSelecionada   = id;
    pastaNomeSelecionada = nome;
    document.getElementById('folder-search').value       = nome;
    document.getElementById('folder-list').style.display = 'none';
}

document.addEventListener('click', e => {
    if (!e.target.closest('.folder-search-wrap') && !e.target.closest('#folder-list')) {
        const list = document.getElementById('folder-list');
        if (list) list.style.display = 'none';
    }
});

async function salvarNoDrive() {
    if (!pastaIdSelecionada) {
        mostrarResultado('Selecione uma pasta antes de salvar.', false);
        return;
    }

    const btn = document.getElementById('btn-drive');
    btn.disabled  = true;
    btn.innerHTML = 'Enviando...';

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
            mostrarResultado('Excel salvo no Drive com sucesso!', true);
        } else {
            mostrarResultado('Erro: ' + (data.error || 'Falha no envio'), false);
        }
    } catch(e) {
        mostrarResultado('Erro de conexao ao enviar.', false);
    } finally {
        btn.disabled  = false;
        btn.innerHTML = 'Salvar no Drive';
    }
}

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
        a.download = ('conferencia_salas_' + (escolaExportar || 'salas') + '_' + date + '.xlsx').replace(/\s+/g,'_');
        a.click();
        URL.revokeObjectURL(url);
    } catch(e) {
        alert('Erro ao baixar: ' + e.message);
    }
}

function mostrarResultado(msg, ok) {
    const el = document.getElementById('export-result');
    el.textContent   = msg;
    el.className     = ok ? 'result-ok' : 'result-fail';
    el.style.display = '';
    if (ok) setTimeout(function() { el.style.display = 'none'; }, 6000);
}
