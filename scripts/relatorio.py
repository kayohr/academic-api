"""
Gera relatório PDF de desempenho acadêmico de um aluno.
Uso: python scripts/relatorio.py <aluno_id> [arquivo_saida.pdf]
"""

import os
import sys
from datetime import date
from dotenv import load_dotenv
import psycopg2
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))
DATABASE_URL = os.environ["DATABASE_URL"]


def conectar():
    return psycopg2.connect(DATABASE_URL)


def buscar_dados(aluno_id: int) -> dict:
    conn = conectar()
    cur = conn.cursor()

    # Dados do aluno e curso
    cur.execute("""
        SELECT a.matricula, a.nome, a.email, a.status, a.semestre_ingresso,
               c.nome AS curso, c.grau
        FROM aluno a
        JOIN curso c ON c.id = a.curso_id
        WHERE a.id = %s AND a.deleted_at IS NULL
    """, (aluno_id,))
    aluno = cur.fetchone()
    if not aluno:
        print(f"Aluno id={aluno_id} não encontrado.", file=sys.stderr)
        sys.exit(1)

    # Histórico
    cur.execute("""
        SELECT d.codigo, d.nome, s.ano, s.periodo,
               h.nota_final, h.frequencia_pct, h.situacao, h.creditos
        FROM historico h
        JOIN disciplina d ON d.id = h.disciplina_id
        JOIN semestre s ON s.id = h.semestre_id
        WHERE h.aluno_id = %s
        ORDER BY s.ano, s.periodo, d.nome
    """, (aluno_id,))
    historico = cur.fetchall()

    # CR
    cur.execute("""
        SELECT COALESCE(
            SUM(h.nota_final * h.creditos) / NULLIF(SUM(h.creditos), 0), NULL
        )
        FROM historico h
        WHERE h.aluno_id = %s AND h.situacao = 'aprovado'
    """, (aluno_id,))
    cr_row = cur.fetchone()
    cr = round(float(cr_row[0]), 2) if cr_row and cr_row[0] else None

    # Matrículas ativas
    cur.execute("""
        SELECT d.codigo, d.nome, t.codigo AS turma, sem.ano, sem.periodo, m.status
        FROM matricula m
        JOIN turma t ON t.id = m.turma_id
        JOIN disciplina d ON d.id = t.disciplina_id
        JOIN semestre sem ON sem.id = t.semestre_id
        WHERE m.aluno_id = %s AND m.status = 'ativa'
        ORDER BY sem.ano DESC, sem.periodo DESC, d.nome
    """, (aluno_id,))
    matriculas_ativas = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "aluno": aluno,
        "historico": historico,
        "cr": cr,
        "matriculas_ativas": matriculas_ativas,
    }


def gerar_pdf(dados: dict, caminho: str):
    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    titulo_style = ParagraphStyle("titulo", parent=styles["Title"], fontSize=16, spaceAfter=4)
    subtitulo_style = ParagraphStyle("sub", parent=styles["Heading2"], fontSize=12, spaceAfter=4)
    normal = styles["Normal"]

    aluno = dados["aluno"]
    matricula_num, nome, email, status, ingresso, curso, grau = aluno

    story = []

    # Cabeçalho
    story.append(Paragraph("Academic API", titulo_style))
    story.append(Paragraph("Relatório de Desempenho Acadêmico", subtitulo_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#2563EB")))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(f"<b>Nome:</b> {nome}", normal))
    story.append(Paragraph(f"<b>Matrícula:</b> {matricula_num} &nbsp;&nbsp; <b>Status:</b> {status}", normal))
    story.append(Paragraph(f"<b>Curso:</b> {curso} ({grau})", normal))
    story.append(Paragraph(f"<b>Ingresso:</b> {ingresso} &nbsp;&nbsp; <b>E-mail:</b> {email}", normal))
    story.append(Paragraph(f"<b>CR Atual:</b> {dados['cr'] if dados['cr'] is not None else 'N/A'}", normal))
    story.append(Paragraph(f"<b>Emitido em:</b> {date.today().strftime('%d/%m/%Y')}", normal))
    story.append(Spacer(1, 0.5*cm))

    # Histórico
    story.append(Paragraph("Histórico Acadêmico", subtitulo_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    story.append(Spacer(1, 0.2*cm))

    if dados["historico"]:
        cabecalho = [["Código", "Disciplina", "Semestre", "Nota", "Freq. %", "Situação", "Créditos"]]
        linhas = []
        for row in dados["historico"]:
            codigo, nome_disc, ano, periodo, nota, freq, situacao, cred = row
            linhas.append([
                codigo,
                nome_disc[:35] + ("…" if len(nome_disc) > 35 else ""),
                f"{ano}/{periodo}",
                f"{float(nota):.1f}" if nota else "—",
                f"{float(freq):.1f}%" if freq else "—",
                situacao,
                str(cred),
            ])

        tabela = Table(cabecalho + linhas, colWidths=[2*cm, 6*cm, 2*cm, 1.5*cm, 2*cm, 2.5*cm, 1.5*cm])
        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",      (1, 1), (1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
            ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            # Colorir situação
            *[("TEXTCOLOR", (5, i+1), (5, i+1),
               colors.HexColor("#16A34A") if linhas[i][5] == "aprovado"
               else colors.HexColor("#DC2626") if linhas[i][5] == "reprovado"
               else colors.HexColor("#CA8A04"))
              for i in range(len(linhas))],
        ]))
        story.append(tabela)
    else:
        story.append(Paragraph("Nenhum histórico disponível.", normal))

    story.append(Spacer(1, 0.5*cm))

    # Matrículas ativas
    if dados["matriculas_ativas"]:
        story.append(Paragraph("Matrículas Ativas (Semestre Corrente)", subtitulo_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
        story.append(Spacer(1, 0.2*cm))

        cab2 = [["Código", "Disciplina", "Turma", "Semestre"]]
        linhas2 = [
            [r[0], r[1][:35], r[2], f"{r[3]}/{r[4]}"]
            for r in dados["matriculas_ativas"]
        ]
        t2 = Table(cab2 + linhas2, colWidths=[2*cm, 7*cm, 2.5*cm, 2*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 8),
            ("ALIGN",      (0, 0), (-1, -1), "CENTER"),
            ("ALIGN",      (1, 1), (1, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F5F9")]),
            ("GRID",       (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t2)

    doc.build(story)
    print(f"Relatório gerado: {caminho}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python relatorio.py <aluno_id> [saida.pdf]", file=sys.stderr)
        sys.exit(1)

    aluno_id = int(sys.argv[1])
    saida = sys.argv[2] if len(sys.argv) > 2 else f"relatorio_aluno_{aluno_id}.pdf"

    print(f"Buscando dados do aluno id={aluno_id}...")
    dados = buscar_dados(aluno_id)
    gerar_pdf(dados, saida)


if __name__ == "__main__":
    main()
