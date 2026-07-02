/**
 * exportar.js
 * Recebe a escola via sessionStorage (enviada por salas.js),
 * carrega o resumo e permite enviar o Excel direto para o Drive.
 */

let escolaExportar = '';
let turmasExportar = [];
let marksExportar  = {};

document.addEventListener('DOMContentLoaded', async () => {
    // Header
    try {
        const r = await fetch('/api/get_current_user');
        const d = await r.json();
        document.getElementById('nome-usuario').textContent  = d.username || '';
        document.getElementById('periodo-usuario').textContent = d.periodo || '';
    } catch(e) {}
    document.getElementById('data-atual').textContent =
        new Date().toLocaleDateString('pt-BR', {weekday:'long', day:'numeric', month:'long', year:'numeric'});

    // Escola vinda da tela de salas
    escolaExportar = sessionStorage.getItem('exportar_escola') || '';

    await carregarEscola(escolaExportar);
    await carregarOutrasEscolas(escolaExportar);
});

async function carregarEscola(escola) {
    const semEscolaEl = document.getElementById('sem-escola');
    const comEscolaEl = document.getElementById('com-escola');

    if (!escola) {
        semEscolaEl.style.display = '';
        comEscolaEl.style.display = 'none';
        return;
    }

    try {
        const res  = await fetch('/api/get_salas_turmas', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({escola})
        });
        const data = await res.json();
        turmasExportar = data.turmas || [];
        marksExportar  = data.marks  || {};

        const sn    = Object.values(marksExportar).filter(m => m.status === 'SN').length;
        const ne    = Object.values(marksExportar).filter(m => m.status === 'NE').length;
        const c     = Object.values(marksExportar).filter(m => m.status === 'C').length;
        const total = turmasExportar.length;

        document.getElementById('escola-label').textContent = escola;
        document.getElementById('r-total').textContent = total;
        document.getElementById('r-sn').textContent    = sn;
        document.getElementById('r-ne').textContent    = ne;
        document.getElementById('r-c').textContent     = c;

        semEscolaEl.style.display = 'none';
        comEscolaEl.style.display = '';
    } catch(e) {
        console.error(e);
    }
}

async function carregarOutrasEscolas(escolaAtual) {
    try {
        const res    = await fetch('/api/get_schools');
        const data   = await res.json();
        const outras = (data.schools || []).filter(e => e !== escolaAtual);
        const el     = document.getElementById('outras-escolas');

        if (!outras.length) {
            el.innerHTML = '<p style="color:#94a3b8;font-size:.85rem">Nenhuma outra escola importada.</p>';
            return;
        }

        el.innerHTML = outras.map(escola => `
            <div style="display:flex;align-items:center;justify-content:space-between;
                        padding:.6rem 1rem;border:1px solid #e2e8f0;border-radius:8px;
                        margin-bottom:.5rem;background:#f8fafc">
                <span style="font-size:.875rem;font-weight:500;color:#1e293b">${escola}</span>
                <div style="display:flex;gap:.4rem">
                    <button onclick="selecionarEscola('${escola}')"
                        style="padding:.3rem .8rem;border-radius:6px;font-size:.78rem;
                               border:1px solid #0a192f;background:#0a192f;color:#fff;cursor:pointer">
                        <i class="fas fa-cloud-upload-alt"></i> Exportar esta
                    </button>
                </div>
            </div>
        `).join('');
    } catch(e) { console.error(e); }
}

function selecionarEscola(escola) {
    sessionStorage.setItem('exportar_escola', escola);
    window.location.reload();
}

// ── Enviar para o Drive ──────────────────────────────────────────
async function exportarParaDrive() {
    const btn       = document.getElementById('btn-drive');
    const resultEl  = document.getElementById('export-result');

    btn.disabled     = true;
    btn.innerHTML    = '<i class="fas fa-spinner fa-spin"></i> Enviando…';
    resultEl.style.display = 'none';

    try {
        const res = await fetch('/api/export_excel_drive', {
            method: 'POST',
            headers: {'Content-Type':'application/json'},
            body: JSON.stringify({
                escola: escolaExportar,
                turmas: turmasExportar,
                marks:  marksExportar
            })
        });
        const data = await res.json();

        resultEl.style.display = '';
        if (data.success) {
            resultEl.className = 'result-ok';
            resultEl.innerHTML = `<i class="fas fa-check-circle"></i> Excel enviado com sucesso para o Drive!
                ${data.file_id ? `<br><small>ID do arquivo: ${data.file_id}</small>` : ''}`;
        } else {
            resultEl.className = 'result-fail';
            resultEl.innerHTML = `<i class="fas fa-times-circle"></i> Erro: ${data.error || 'Falha no envio'}`;
        }
    } catch(e) {
        resultEl.style.display = '';
        resultEl.className = 'result-fail';
        resultEl.innerHTML = '<i class="fas fa-times-circle"></i> Erro de conexão ao enviar.';
        console.error(e);
    } finally {
        btn.disabled  = false;
        btn.innerHTML = '<i class="fas fa-cloud-upload-alt"></i> Enviar Excel para o Drive';
    }
}

// ── Baixar localmente ────────────────────────────────────────────
async function baixarLocal() {
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
        const date = new Date().toISOString().slice(0, 10);
        a.href     = url;
        a.download = `conferencia_salas_${escolaExportar}_${date}.xlsx`.replace(/\s+/g, '_');
        a.click();
        URL.revokeObjectURL(url);
    } catch(e) {
        console.error(e);
        alert('Erro ao baixar o arquivo.');
    }
}
