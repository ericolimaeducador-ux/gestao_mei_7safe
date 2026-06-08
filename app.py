"""
Servidor web local. Rode com:  python app.py
Depois abra no navegador:  http://127.0.0.1:5000
"""

from datetime import date

from flask import Flask, render_template, request, redirect, url_for, flash

from mei import config, planilha, contabil, fiscal

app = Flask(__name__)
app.secret_key = "troque-isto-por-qualquer-texto"

# garante a planilha na primeira execução
planilha.garantir_planilha()


def brl(valor):
    """Formata número como moeda brasileira: 1234.5 -> 'R$ 1.234,50'."""
    try:
        return "R$ " + f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


app.jinja_env.filters["brl"] = brl


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
@app.route("/")
def dashboard():
    resumo = contabil.resumo_dashboard()
    return render_template("dashboard.html", r=resumo, empresa=config.EMPRESA, hoje=date.today())


# ---------------------------------------------------------------------------
# Lançamentos (livro-caixa)
# ---------------------------------------------------------------------------
@app.route("/lancamentos")
def lancamentos():
    itens = sorted(planilha.listar_lancamentos(), key=lambda x: str(x["data"]), reverse=True)
    return render_template("lancamentos.html", itens=itens)


@app.route("/lancamentos/novo", methods=["POST"])
def novo_lancamento():
    f = request.form
    planilha.adicionar_lancamento(
        data=f.get("data") or date.today().isoformat(),
        tipo=f.get("tipo", "receita"),
        descricao=f.get("descricao", ""),
        categoria=f.get("categoria", ""),
        valor=f.get("valor", 0) or 0,
        nota_id=f.get("nota_id", ""),
    )
    flash("Lançamento registrado.")
    return redirect(url_for("lancamentos"))


@app.route("/lancamentos/<int:lanc_id>/remover", methods=["POST"])
def excluir_lancamento(lanc_id):
    planilha.remover_lancamento(lanc_id)
    flash("Lançamento removido.")
    return redirect(url_for("lancamentos"))


# ---------------------------------------------------------------------------
# DAS
# ---------------------------------------------------------------------------
@app.route("/das")
def das():
    hoje = date.today()
    # garante DAS dos últimos meses do ano corrente
    for m in range(1, hoje.month + 1):
        contabil.gerar_das_competencia(hoje.year, m)
    itens = sorted(planilha.listar_das(), key=lambda x: str(x["competencia"]), reverse=True)
    return render_template("das.html", itens=itens, valor=config.valor_das_atual(),
                           atividade=config.EMPRESA["atividade"])


@app.route("/das/<competencia>/pagar", methods=["POST"])
def pagar_das(competencia):
    d = {x["competencia"]: x for x in planilha.listar_das()}.get(competencia)
    if d:
        planilha.registrar_das(competencia, d["valor"], d["vencimento"],
                               status="pago", data_pagamento=date.today().isoformat())
        flash(f"DAS {competencia} marcado como pago.")
    return redirect(url_for("das"))


# ---------------------------------------------------------------------------
# Notas fiscais
# ---------------------------------------------------------------------------
@app.route("/notas")
def notas():
    itens = sorted(planilha.listar_notas(), key=lambda x: str(x["data"]), reverse=True)
    return render_template("notas.html", itens=itens, provedor=config.PROVEDOR_NFE)


@app.route("/notas/emitir", methods=["POST"])
def emitir_nota():
    f = request.form
    res = fiscal.emitir_nota(
        tomador=f.get("tomador", ""),
        cnpj_cpf=f.get("cnpj_cpf", ""),
        descricao=f.get("descricao", ""),
        valor=f.get("valor", 0) or 0,
        tipo=f.get("tipo", "servico"),
    )
    # opcional: já lançar a receita vinculada à nota
    if res.get("status") in ("autorizado", "processando") and f.get("lancar_receita"):
        planilha.adicionar_lancamento(
            data=date.today().isoformat(), tipo="receita",
            descricao=f"NF {res.get('nota_id')}: {f.get('descricao','')}",
            categoria="venda", valor=f.get("valor", 0) or 0,
            nota_id=str(res.get("nota_id", "")),
        )
    flash(f"Nota: {res.get('status')} — {res.get('mensagem','')}")
    return redirect(url_for("notas"))


# ---------------------------------------------------------------------------
# Relatório Mensal das Receitas Brutas (obrigação do MEI)
# ---------------------------------------------------------------------------
@app.route("/relatorio")
def relatorio():
    hoje = date.today()
    ano = int(request.args.get("ano", hoje.year))
    mes = int(request.args.get("mes", hoje.month))
    rel = contabil.relatorio_mensal(ano, mes)
    return render_template("relatorio.html", rel=rel, ano=ano, mes=mes,
                           meses=contabil.MESES)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
