"""
parser_salas_meta.py
Extrai metadados de sala (número da sala e turno) do HTML do EducarWEB
para enriquecer a tela de Conferência de Salas.
"""
import re
from lxml import html as lhtml


def _spans(tree):
    texts = []
    for sp in tree.xpath('//span'):
        t = sp.text_content().replace('\xa0', ' ').strip()
        t = re.sub(r'\s+', ' ', t)
        if t:
            texts.append(t)
    return texts


def parse_salas_meta(html_content: str) -> dict:
    """
    Retorna:
    {
      "escola": "EBM PROF. OSMAR ...",
      "turmas": [
        {"turma": "5º ANO - 1", "sala": "SALA 05", "turno": "MANHÃ"},
        ...
      ]
    }
    """
    try:
        tree = lhtml.fromstring(html_content)
    except Exception:
        return {"escola": "", "turmas": []}

    spans = _spans(tree)

    # Detecta escola: procura no primeiro span que comece com EBM/EB/CEI/ESCOLA/E.B.M
    escola = ""
    escola_patterns = [
        r'^(EBM\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(E\.B\.M\.?\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(EB\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(CEI\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(ER\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(GE\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
        r'^(ESCOLA\s+[^\-]{3,60})(?:\s*-\s*\d+)?$',
    ]
    for sp in spans:
        sp_clean = sp.strip()
        matched = False
        for pat in escola_patterns:
            m = re.match(pat, sp_clean, re.IGNORECASE)
            if m:
                escola = m.group(1).strip().rstrip(',.')
                matched = True
                break
        if matched:
            break
    turmas = []
    i = 0
    while i < len(spans):
        t = spans[i]
        # Turma escola regular: "5º ANO - 1" ou "5o ANO - 1"
        # Turma creche (CEI): "GT 0 A", "GT 1 B", "BERÇÁRIO I A" etc.
        is_ano_serie = re.match(r'^\d+[ºo°]\s*ANO\s*[-–]\s*\d+$', t, re.IGNORECASE)
        is_gt = re.match(r'^GT\s*\d+\s*[A-Z]$', t, re.IGNORECASE)
        is_creche_nome = re.match(
            r'^(BERÇÁRIO|MATERNAL|PRÉ\s*[I1]{0,3}|JARDIM)\s*[I1]{0,3}\s*[A-Z]?$',
            t, re.IGNORECASE
        )

        if is_ano_serie or is_gt or is_creche_nome:
            turma_nome = re.sub(r'[o°]', 'º', t)  # normalise º
            turma_nome = re.sub(r'\s+', ' ', turma_nome).strip()
            turno = ''
            sala = ''
            for j in range(i + 1, min(i + 15, len(spans))):
                s = spans[j].upper()
                if s in ('MANHÃ', 'TARDE', 'NOITE', 'MANHA', 'INTEGRAL'):
                    if 'MAN' in s:
                        turno = 'MANHÃ'
                    elif 'TAR' in s:
                        turno = 'TARDE'
                    elif 'INTEG' in s:
                        turno = 'INTEGRAL'
                    else:
                        turno = 'NOITE'
                if re.match(r'^SALA\s*\d+', s):
                    sala = spans[j].upper()
                    break
            if sala:
                turmas.append({'turma': turma_nome, 'sala': sala, 'turno': turno})
        i += 1

    # Sort: GT N por número, ANO/SÉRIE por (ano, número), demais por ordem de aparição
    def sort_key(x):
        nome = x['turma']
        m_gt = re.match(r'^GT\s*(\d+)\s*([A-Z])$', nome, re.IGNORECASE)
        if m_gt:
            return (0, int(m_gt.group(1)), m_gt.group(2))
        m_ano = re.search(r'(\d+)[^\d]*(\d+)', nome)
        if m_ano:
            return (1, int(m_ano.group(1)), int(m_ano.group(2)))
        return (2, 0, nome)
    turmas.sort(key=sort_key)

    return {"escola": escola, "turmas": turmas}
