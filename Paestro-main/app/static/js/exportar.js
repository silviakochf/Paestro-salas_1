// exportar.js v4

var escolaExportar = '';
var turmasExportar = [];
var marksExportar = {};
var allFolders = [];
var pastaIdSelecionada = '';
var pastaNomeSelecionada = '';

document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/get_current_user').then(function(r) { return r.json(); }).then(function(d) {
        document.getElementById('nome-usuario').textContent = d.username || '';
        document.getElementById('periodo-usuario').textContent = d.periodo || '';
    }).catch(function(){});

    document.getElementById('data-atual').textContent =
        new Date().toLocaleDateString('pt-BR', {weekday:'long', day:'numeric', month:'long', year:'numeric'});

    escolaExportar = sessionStorage.getItem('exportar_escola') || '';
    if (escolaExportar) {
        document.getElementById('escola-wrap').style.display = '';
        document.getElementById('escola-label').textContent = escolaExportar;
    }

    // Carrega pastas e configura tudo
    fetch('/api/list_drive_folders').then(function(r) { return r.json(); }).then(function(data) {
        allFolders = data.folders || [];

        if (escolaExportar) {
            fetch('/api/get_salas_turmas', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({escola: escolaExportar})
            }).then(function(r) { return r.json(); }).then(function(d) {
                turmasExportar = d.turmas || [];
                marksExportar = d.marks || {};
            }).catch(function(e) { console.error(e); });
        }

        var input = document.getElementById('folder-search');
        input.addEventListener('focus', function() { abrirDropdown(); });
        input.addEventListener('input', function() { filtrarPastas(); });

    }).catch(function(e) {
        console.error('Erro pastas:', e);
        allFolders = [];
    });
});

function abrirDropdown() {
    renderDropdown(allFolders);
}

function toggleDropdown() {
    var list = document.getElementById('folder-list');
    if (list.style.display === 'none' || list.style.display === '') {
        renderDropdown(allFolders);
    } else {
        list.style.display = 'none';
    }
}

function filtrarPastas() {
    var q = document.getElementById('folder-search').value.toLowerCase();
    var filtered = q ? allFolders.filter(function(f) {
        return f.name.toLowerCase().indexOf(q) >= 0;
    }) : allFolders;
    renderDropdown(filtered);
}

function renderDropdown(folders) {
    var list = document.getElementById('folder-list');
    var html = '';
    if (!folders.length) {
        html = '<div style="padding:.75rem 1rem;color:#94a3b8;font-size:.875rem">Nenhuma pasta encontrada</div>';
    } else {
        for (var i = 0; i < folders.length; i++) {
            var f = folders[i];
            var sel = f.id === pastaIdSelecionada ? ' selected' : '';
            var safeName = f.name.replace(/\\/g, '\\\\').replace(/'/g, "\\'");
            var safeId = f.id;
            html += '<div class="folder-item' + sel + '" onclick="selecionarPasta(\'' + safeId + '\', \'' + safeName + '\')">' + f.name + '</div>';
        }
    }
    list.innerHTML = html;
    list.style.display = 'block';
}

function selecionarPasta(id, nome) {
    pastaIdSelecionada = id;
    pastaNomeSelecionada = nome;
    document.getElementById('folder-search').value = nome;
    document.getElementById('folder-list').style.display = 'none';
}

document.addEventListener('click', function(e) {
    var wrap = document.querySelector('.folder-search-wrap');
    var list = document.getElementById('folder-list');
    if (!wrap || !list) return;
    if (!wrap.contains(e.target) && !list.contains(e.target)) {
        list.style.display = 'none';
    }
});

function salvarNoDrive() {
    if (!pastaIdSelecionada) {
        mostrarResultado('Selecione uma pasta antes de salvar.', false);
        return;
    }
    var btn = document.getElementById('btn-drive');
    btn.disabled = true;
    btn.textContent = 'Enviando...';

    fetch('/api/export_excel_drive', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            escola: escolaExportar,
            folder_id: pastaIdSelecionada,
            turmas: turmasExportar,
            marks: marksExportar
        })
    }).then(function(r) { return r.json(); }).then(function(data) {
        if (data.success) {
            mostrarResultado('Excel salvo no Drive com sucesso!', true);
        } else {
            mostrarResultado('Erro: ' + (data.error || 'Falha no envio'), false);
        }
    }).catch(function() {
        mostrarResultado('Erro de conexao ao enviar.', false);
    }).finally(function() {
        btn.disabled = false;
        btn.textContent = 'Salvar no Drive';
    });
}

function baixarExcel() {
    fetch('/api/exportar_relatorio_salas', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            escola: escolaExportar,
            turmas: turmasExportar,
            marks: marksExportar
        })
    }).then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.blob();
    }).then(function(blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        var date = new Date().toISOString().slice(0,10);
        var nome = (escolaExportar || 'salas').replace(/\s+/g,'_');
        a.href = url;
        a.download = 'conferencia_salas_' + nome + '_' + date + '.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(function(e) {
        alert('Erro ao baixar: ' + e.message);
    });
}

function mostrarResultado(msg, ok) {
    var el = document.getElementById('export-result');
    el.textContent = msg;
    el.className = ok ? 'result-ok' : 'result-fail';
    el.style.display = 'block';
    if (ok) {
        setTimeout(function() { el.style.display = 'none'; }, 6000);
    }
}
