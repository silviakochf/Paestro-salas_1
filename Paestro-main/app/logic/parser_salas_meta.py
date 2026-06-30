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
        # Turma: "5º ANO - 1" or "5o ANO - 1"
        if re.match(r'^\d+[ºo°]\s*ANO\s*[-–]\s*\d+$', t, re.IGNORECASE):
            turma_nome = re.sub(r'[o°]', 'º', t)  # normalise
            turno = ''
            sala  = ''
            for j in range(i + 1, min(i + 15, len(spans))):
                s = spans[j].upper()
                if s in ('MANHÃ', 'TARDE', 'NOITE', 'MANHA'):
                    turno = 'MANHÃ' if 'MAN' in s else ('TARDE' if 'TAR' in s else 'NOITE')
                if re.match(r'^SALA\s*\d+', s):
                    sala = spans[j].upper()
                    break
            if sala:
                turmas.append({'turma': turma_nome, 'sala': sala, 'turno': turno})
        i += 1

    # Sort by year then number
    def sort_key(x):
        m = re.search(r'(\d+)[^\d]*(\d+)', x['turma'])
        return (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    turmas.sort(key=sort_key)

    return {"escola": escola, "turmas": turmas}
