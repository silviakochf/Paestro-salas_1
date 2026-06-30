document.addEventListener('DOMContentLoaded', () => {
    const escolasList = document.getElementById('escolas-list');
    const exportAllBtn = document.getElementById('export-all-drive-btn');
    const exportResult = document.getElementById('export-result');

    // Header padrão
    (async () => {
        try {
            const r = await fetch('/api/get_current_user');
            const d = await r.json();
            document.getElementById('nome-usuario').textContent = d.username || '';
            document.getElementById('periodo-usuario').textContent = d.periodo || '';
        } catch (e) {}
        document.getElementById('data-atual').textContent =
            new Date().toLocaleDateString('pt-BR');
    })();

    loadEscolas();

    async function loadEscolas() {
        try {
            const res = await fetch('/api/get_schools');
            const data = await res.json();
            const escolas = data.schools || [];

            if (!escolas.length) {
                escolasList.innerHTML = `<p style="color:#94a3b8;font-size:.875rem">
                    Nenhuma escola importada ainda. Vá em <a href="/importar">Importar</a>.
                </p>`;
                return;
            }

            escolasList.innerHTML = escolas.map(escola => `
                <div class="escola-export-row">
                    <div>
                        <div class="escola-nome">${escola}</div>
                    </div>
                    <div class="escola-export-actions">
                        <button class="btn-export-mini xml" data-escola="${escola}" data-tipo="xml">
                            <i class="fas fa-file-code"></i> XML
                        </button>
                        <button class="btn-export-mini excel" data-escola="${escola}" data-tipo="excel">
                            <i class="fas fa-file-excel"></i> Excel
                        </button>
                    </div>
                </div>
            `).join('');

            document.querySelectorAll('.btn-export-mini').forEach(btn => {
                btn.addEventListener('click', () => {
                    const escola = btn.dataset.escola;
                    const tipo = btn.dataset.tipo;
                    exportarEscola(escola, tipo, btn);
                });
            });
        } catch (e) {
            console.error(e);
            escolasList.innerHTML = `<p style="color:#991b1b">Erro ao carregar escolas.</p>`;
        }
    }

    async function exportarEscola(escola, tipo, btn) {
        const original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

        try {
            const endpoint = tipo === 'xml'
                ? '/api/exportar_relatorio_xml'
                : '/api/exportar_relatorio_salas';

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ escola })
            });

            if (!res.ok) throw new Error('Erro HTTP ' + res.status);

            const blob = await res.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            const date = new Date().toISOString().slice(0, 10);
            const ext = tipo === 'xml' ? 'xml' : 'xlsx';
            a.href = url;
            a.download = `conferencia_salas_${escola}_${date}.${ext}`.replace(/\s+/g, '_');
            a.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error(e);
            alert('Erro ao exportar ' + escola);
        } finally {
            btn.disabled = false;
            btn.innerHTML = original;
        }
    }

    exportAllBtn.addEventListener('click', async () => {
        const original = exportAllBtn.innerHTML;
        exportAllBtn.disabled = true;
        exportAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
        exportResult.innerHTML = '';

        try {
            const res = await fetch('/api/exportar_todas_xml_drive', { method: 'POST' });
            const data = await res.json();

            if (data.resultados && data.resultados.length) {
                exportResult.innerHTML = data.resultados.map(r => {
                    if (r.success) {
                        return `<div class="res-ok"><i class="fas fa-check-circle"></i> ${r.escola} — enviado com sucesso</div>`;
                    } else {
                        return `<div class="res-fail"><i class="fas fa-times-circle"></i> ${r.escola} — ${r.error}</div>`;
                    }
                }).join('');
            } else {
                exportResult.innerHTML = `<div class="res-fail">${data.error || 'Nenhum resultado retornado.'}</div>`;
            }
        } catch (e) {
            console.error(e);
            exportResult.innerHTML = `<div class="res-fail">Erro de conexão ao exportar para o Drive.</div>`;
        } finally {
            exportAllBtn.disabled = false;
            exportAllBtn.innerHTML = original;
        }
    });
});
