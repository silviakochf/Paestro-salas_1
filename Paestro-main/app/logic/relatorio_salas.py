import io
import re
from datetime import datetime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

# ── Paleta ────────────────────────────────────────────────────────────
PRIMARY  = "0A192F"
HDR_SEC  = "172A45"
HDR_GRAY = "334155"
SN_BG    = "D1FAE5"; SN_FG = "065F46"
NE_BG    = "FEF9C3"; NE_FG = "854D0E"
C_BG     = "FEE2E2"; C_FG  = "991B1B"
PD_BG    = "F1F5F9"; PD_FG = "475569"
WHITE    = "FFFFFF"
GRAY1    = "F8FAFC"
PURPLE   = "7C3AED"
PURPLED  = "5B21B6"
GREEN    = "10B981"

STATUS_MAP = {
    "SN": (SN_BG, SN_FG, "Sem Necessidade"),
    "NE": (NE_BG, NE_FG, "Número Errado"),
    "C":  (C_BG,  C_FG,  "Correto"),
    None: (PD_BG, PD_FG, "Pendente"),
}

def _fill(h): return PatternFill("solid", fgColor=h)
def _font(bold=False, color="1E293B", size=10, italic=False):
    return Font(name="Arial", bold=bold, color=color, size=size, italic=italic)
def _border():
    s = Side(style="thin", color="CBD5E1")
    return Border(left=s, right=s, top=s, bottom=s)
def _align(h="left", v="center", wrap=False):
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap)

def _header_row(ws, row, merge_to, text, bg, fg_color, size=13, row_h=30):
    ws.merge_cells(f"B{row}:{merge_to}{row}")
    c = ws[f"B{row}"]
    c.value = text; c.font = _font(True, fg_color, size)
    c.fill = _fill(bg); c.alignment = _align("center")
    ws.row_dimensions[row].height = row_h

def _col_headers(ws, row, cols, bg=HDR_GRAY, fg=WHITE, h=18):
    for ci, label in enumerate(cols, start=2):
        col = get_column_letter(ci)
        cell = ws[f"{col}{row}"]
        cell.value = label
        cell.font = _font(True, fg, 9)
        cell.fill = _fill(bg)
        cell.alignment = _align("center")
        cell.border = _border()
    ws.row_dimensions[row].height = h

def _set_widths(ws, widths):
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _serie_key(turma_nome: str):
    """Extrai a chave de série da turma: número do ano (escola) ou número do GT (creche)."""
    m_gt = re.match(r'^GT\s*(\d+)', turma_nome, re.IGNORECASE)
    if m_gt:
        return f"GT{m_gt.group(1)}"
    m_ano = re.match(r'^(\d+)', turma_nome)
    if m_ano:
        return m_ano.group(1)
    return turma_nome.split()[0] if turma_nome else "?"


def _serie_label(serie_key: str):
    if serie_key.startswith("GT"):
        return f"GT {serie_key[2:]}"
    if serie_key.isdigit():
        return f"{serie_key}º ANO"
    return serie_key


def gerar_relatorio_salas_xlsx(escola: str, turmas: list, marks: dict) -> io.BytesIO:
    """
    Gera o relatório Excel de conferência de salas.

    Parâmetros:
        escola  – nome da escola
        turmas  – lista de dicts: [{turma, sala, turno}, ...]
        marks   – dict indexado por str(i): {status, sala_real, obs}
                  (o frontend envia índices como string)

    Retorna:
        BytesIO com o arquivo .xlsx pronto para send_file
    """
    # normaliza chaves para int
    marks_int = {int(k): v for k, v in marks.items() if v}

    total = len(turmas)
    sn_ct = sum(1 for m in marks_int.values() if m.get("status") == "SN")
    ne_ct = sum(1 for m in marks_int.values() if m.get("status") == "NE")
    c_ct  = sum(1 for m in marks_int.values() if m.get("status") == "C")
    pend  = total - sn_ct - ne_ct - c_ct
    done  = sn_ct + ne_ct + c_ct
    pct   = round(done / total * 100) if total else 0
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    series = sorted(
        set(_serie_key(d["turma"]) for d in turmas),
        key=lambda s: int(s[2:]) if s.startswith("GT") else int(s) if s.isdigit() else 999
    )

    wb = Workbook()

    # ═══════════════════════════════════════════════════════════════
    # ABA 1 — RESUMO
    # ═══════════════════════════════════════════════════════════════
    ws = wb.active
    ws.title = "Resumo"
    ws.sheet_view.showGridLines = False
    _set_widths(ws, {"A":3,"B":28,"C":16,"D":16,"E":16,"F":20,"G":3})

    _header_row(ws, 2, "F", "RELATÓRIO DE CONFERÊNCIA DE SALAS", PRIMARY, WHITE, 14, 32)
    _header_row(ws, 3, "F", f"{escola}  |  Ano Letivo {datetime.now().year}  |  Gerado em {now}",
                HDR_SEC, WHITE, 9, 18)
    ws.row_dimensions[4].height = 10

    # Cards
    cards = [
        ("B", "Total de Turmas",       total,  PRIMARY, WHITE),
        ("C", "SN — Sem Necessidade",  sn_ct,  SN_BG,  SN_FG),
        ("D", "NE — Número Errado",    ne_ct,  NE_BG,  NE_FG),
        ("E", "C — Correto",           c_ct,   C_BG,   C_FG),
        ("F", "Pendentes",             pend,   PD_BG,  PD_FG),
    ]
    for col, label, val, bg, fg in cards:
        for r, (v, sz, it) in enumerate(
            [(label, 9, False), (val, 22, False),
             (f"{round(val/total*100) if total else 0}% do total", 8, True)],
            start=5
        ):
            c = ws[f"{col}{r}"]
            c.value = v; c.fill = _fill(bg)
            c.font = _font(r==6, fg, sz, it)
            c.alignment = _align("center"); c.border = _border()
        ws.row_dimensions[5].height = 18
        ws.row_dimensions[6].height = 30
        ws.row_dimensions[7].height = 16

    ws.row_dimensions[8].height = 8

    # Progresso
    ws.merge_cells("B9:F9")
    ws["B9"].value = f"Progresso: {done} de {total} turmas verificadas ({pct}%)"
    ws["B9"].font = _font(True, WHITE, 10)
    ws["B9"].fill = _fill(PRIMARY)
    ws["B9"].alignment = _align("center")
    ws.row_dimensions[9].height = 20
    ws.row_dimensions[10].height = 8

    # Tabela por série
    _header_row(ws, 11, "F", "Distribuição por Série", PRIMARY, WHITE, 11, 22)
    _col_headers(ws, 12, ["Série","Total","SN","NE","C","Pendente"])

    for ri, serie in enumerate(series, start=13):
        idx = [i for i, d in enumerate(turmas) if _serie_key(d["turma"]) == serie]
        t  = len(idx)
        sn = sum(1 for i in idx if marks_int.get(i, {}).get("status") == "SN")
        ne = sum(1 for i in idx if marks_int.get(i, {}).get("status") == "NE")
        cc = sum(1 for i in idx if marks_int.get(i, {}).get("status") == "C")
        pp = t - sn - ne - cc
        bg = GRAY1 if ri % 2 == 0 else WHITE
        for ci, v in enumerate([_serie_label(serie), t, sn, ne, cc, pp], start=2):
            cl = ws[f"{get_column_letter(ci)}{ri}"]
            cl.value = v; cl.fill = _fill(bg)
            cl.font = _font(ci==2, size=9)
            cl.alignment = _align("center" if ci>2 else "left")
            cl.border = _border()
        ws.row_dimensions[ri].height = 16

    tr = 12 + len(series) + 1
    for ci, v in enumerate(["TOTAL", total, sn_ct, ne_ct, c_ct, pend], start=2):
        cl = ws[f"{get_column_letter(ci)}{tr}"]
        cl.value = v; cl.fill = _fill(PRIMARY)
        cl.font = _font(True, WHITE, 9)
        cl.alignment = _align("center" if ci>2 else "left")
        cl.border = _border()
    ws.row_dimensions[tr].height = 18

    # ═══════════════════════════════════════════════════════════════
    # ABA 2 — DETALHAMENTO COMPLETO
    # ═══════════════════════════════════════════════════════════════
    wd = wb.create_sheet("Detalhamento Completo")
    wd.sheet_view.showGridLines = False
    _set_widths(wd, {"A":3,"B":5,"C":26,"D":10,"E":12,"F":14,"G":22,"H":16,"I":30,"J":3})

    _header_row(wd, 2, "I", "DETALHAMENTO — CONFERÊNCIA DE SALAS POR TURMA", PRIMARY, WHITE, 13, 30)
    _header_row(wd, 3, "I", f"{escola}  |  {now}", HDR_SEC, WHITE, 9, 16)
    wd.row_dimensions[4].height = 8

    _col_headers(wd, 5, ["#","Turma","Turno","Série","Sala (sistema)","Status","Sala Real","Observação"])
    wd.freeze_panes = "B6"
    wd.auto_filter.ref = f"B5:I{5+total}"

    for ri, d in enumerate(turmas):
        row = ri + 6
        m = marks_int.get(ri, {})
        status = m.get("status")
        bg, fg, label = STATUS_MAP.get(status, STATUS_MAP[None])
        serie = _serie_label(_serie_key(d["turma"]))
        row_bg = bg if status else (GRAY1 if ri % 2 == 0 else WHITE)

        vals = [ri+1, d["turma"], d["turno"], serie, d["sala"],
                label, m.get("sala_real","") or "—", m.get("obs","") or "—"]
        for ci, v in enumerate(vals, start=2):
            col = get_column_letter(ci)
            cell = wd[f"{col}{row}"]
            cell.value = v; cell.border = _border()
            cell.alignment = _align("center" if ci in [2,4,5,6,7] else "left", wrap=(ci==9))
            if ci == 7:  # status
                cell.font = _font(True, fg, 9)
                cell.fill = _fill(bg)
            else:
                cell.font = _font(size=9)
                cell.fill = _fill(row_bg)
        wd.row_dimensions[row].height = 16

    # ═══════════════════════════════════════════════════════════════
    # ABA 3 — OCORRÊNCIAS (NE e C)
    # ═══════════════════════════════════════════════════════════════
    wo = wb.create_sheet("Ocorrências")
    wo.sheet_view.showGridLines = False
    _set_widths(wo, {"A":3,"B":5,"C":26,"D":10,"E":12,"F":14,"G":22,"H":16,"I":30,"J":3})

    _header_row(wo, 2, "I", "OCORRÊNCIAS — NE (Número Errado) e C (Correto)", PURPLE, WHITE, 13, 30)
    _header_row(wo, 3, "I", f"{escola}  |  {now}", PURPLED, WHITE, 9, 16)
    wo.row_dimensions[4].height = 8
    _col_headers(wo, 5, ["#","Turma","Turno","Série","Sala (sistema)","Status","Sala Real","Observação"])

    ocorrencias = [(i,d) for i,d in enumerate(turmas) if marks_int.get(i,{}).get("status") in ("NE","C")]

    if ocorrencias:
        for ri, (i, d) in enumerate(ocorrencias):
            row = ri + 6
            m = marks_int[i]
            status = m["status"]
            bg, fg, label = STATUS_MAP[status]
            serie = _serie_label(_serie_key(d["turma"]))
            vals = [ri+1, d["turma"], d["turno"], serie, d["sala"],
                    label, m.get("sala_real","") or "—", m.get("obs","") or "—"]
            for ci, v in enumerate(vals, start=2):
                col = get_column_letter(ci)
                cell = wo[f"{col}{row}"]
                cell.value = v; cell.border = _border()
                cell.alignment = _align("center" if ci in [2,4,5,6,7] else "left")
                if ci == 7:
                    cell.font = _font(True, fg, 9); cell.fill = _fill(bg)
                else:
                    cell.font = _font(size=9)
                    cell.fill = _fill(NE_BG if status == "NE" else C_BG)
            wo.row_dimensions[row].height = 16
    else:
        wo.merge_cells("B6:I6")
        wo["B6"].value = "Nenhuma ocorrência registrada."
        wo["B6"].font = _font(italic=True, color="94A3B8")
        wo["B6"].alignment = _align("center")

    # ═══════════════════════════════════════════════════════════════
    # ABA 4 — GRÁFICO
    # ═══════════════════════════════════════════════════════════════
    wg = wb.create_sheet("Gráfico")
    wg.sheet_view.showGridLines = False
    _set_widths(wg, {"A":3,"B":12,"C":10,"D":10,"E":10,"F":10})

    _col_headers(wg, 2, ["Série","SN","NE","C","Pendente"])
    for ri, serie in enumerate(series, start=3):
        idx = [i for i,d in enumerate(turmas) if _serie_key(d["turma"]) == serie]
        sn = sum(1 for i in idx if marks_int.get(i,{}).get("status")=="SN")
        ne = sum(1 for i in idx if marks_int.get(i,{}).get("status")=="NE")
        cc = sum(1 for i in idx if marks_int.get(i,{}).get("status")=="C")
        pp = len(idx)-sn-ne-cc
        wg[f"B{ri}"] = _serie_label(serie)
        wg[f"C{ri}"] = sn; wg[f"D{ri}"] = ne
        wg[f"E{ri}"] = cc; wg[f"F{ri}"] = pp
        wg.row_dimensions[ri].height = 14

    last_r = 2 + len(series)
    chart = BarChart()
    chart.type = "col"; chart.title = "Status por Série"
    chart.style = 10; chart.grouping = "clustered"
    chart.y_axis.title = "Turmas"; chart.x_axis.title = "Série"
    chart.width = 22; chart.height = 14
    data_ref = Reference(wg, min_col=3, max_col=6, min_row=2, max_row=last_r)
    cats_ref = Reference(wg, min_col=2, min_row=3, max_row=last_r)
    chart.add_data(data_ref, titles_from_data=True)
    chart.set_categories(cats_ref)
    chart.series[0].graphicalProperties.solidFill = GREEN.replace("#","")
    chart.series[1].graphicalProperties.solidFill = "F59E0B"
    chart.series[2].graphicalProperties.solidFill = "EF4444"
    chart.series[3].graphicalProperties.solidFill = "94A3B8"
    wg.add_chart(chart, "B9")

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
