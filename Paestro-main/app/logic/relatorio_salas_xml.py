"""
relatorio_salas_xml.py
Gera o relatório XML de conferência de salas para UMA escola.
"""
import io
from datetime import datetime
from xml.sax.saxutils import escape


def _esc(s) -> str:
    return escape(str(s) if s is not None else "")


def gerar_relatorio_salas_xml(escola: str, turmas: list, marks: dict) -> io.BytesIO:
    """
    Parâmetros:
        escola  – nome da escola
        turmas  – lista de dicts: [{turma, sala, turno}, ...]
        marks   – dict indexado por str(i) ou int(i): {status, sala_real, obs}

    Retorna:
        BytesIO com o XML pronto para send_file
    """
    marks_int = {int(k): v for k, v in (marks or {}).items() if v}

    total = len(turmas)
    sn_ct = sum(1 for m in marks_int.values() if m.get("status") == "SN")
    ne_ct = sum(1 for m in marks_int.values() if m.get("status") == "NE")
    c_ct = sum(1 for m in marks_int.values() if m.get("status") == "C")
    pend = total - sn_ct - ne_ct - c_ct
    now = datetime.now().isoformat()

    linhas = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<conferencia_salas>',
        f'  <escola>{_esc(escola)}</escola>',
        f'  <data_geracao>{_esc(now)}</data_geracao>',
        '  <resumo>',
        f'    <total>{total}</total>',
        f'    <sem_necessidade>{sn_ct}</sem_necessidade>',
        f'    <numero_errado>{ne_ct}</numero_errado>',
        f'    <correto>{c_ct}</correto>',
        f'    <pendente>{pend}</pendente>',
        '  </resumo>',
        '  <turmas>',
    ]

    for i, d in enumerate(turmas):
        m = marks_int.get(i, {})
        linhas.append('    <turma>')
        linhas.append(f'      <nome>{_esc(d.get("turma",""))}</nome>')
        linhas.append(f'      <sala_sistema>{_esc(d.get("sala",""))}</sala_sistema>')
        linhas.append(f'      <turno>{_esc(d.get("turno",""))}</turno>')
        linhas.append(f'      <status>{_esc(m.get("status") or "Pendente")}</status>')
        linhas.append(f'      <sala_real>{_esc(m.get("sala_real",""))}</sala_real>')
        linhas.append(f'      <observacao>{_esc(m.get("obs",""))}</observacao>')
        linhas.append('    </turma>')

    linhas.append('  </turmas>')
    linhas.append('</conferencia_salas>')

    xml_str = '\n'.join(linhas)
    buf = io.BytesIO(xml_str.encode('utf-8'))
    buf.seek(0)
    return buf
