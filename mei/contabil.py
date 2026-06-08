"""
Regras contábeis do MEI.
Tudo o que o MEI precisa, sem complicar:
  - faturamento por ano e por mês
  - acompanhamento do limite anual (R$ 81.000)
  - geração/lembrete do DAS
  - Relatório Mensal das Receitas Brutas (obrigação legal do MEI)
"""

from calendar import monthrange
from datetime import date, datetime

from . import config, planilha

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]


def _ano_mes(data_str):
    """Aceita 'AAAA-MM-DD' e devolve (ano, mes)."""
    d = datetime.fromisoformat(str(data_str)[:10])
    return d.year, d.month


# ---------------------------------------------------------------------------
# Faturamento
# ---------------------------------------------------------------------------
def faturamento_ano(ano=None):
    ano = ano or date.today().year
    total = 0.0
    for l in planilha.listar_lancamentos():
        if l["tipo"] == "receita" and _ano_mes(l["data"])[0] == ano:
            total += float(l["valor"] or 0)
    return round(total, 2)


def faturamento_mes(ano, mes):
    total = 0.0
    for l in planilha.listar_lancamentos():
        if l["tipo"] != "receita":
            continue
        a, m = _ano_mes(l["data"])
        if a == ano and m == mes:
            total += float(l["valor"] or 0)
    return round(total, 2)


def despesas_ano(ano=None):
    ano = ano or date.today().year
    total = 0.0
    for l in planilha.listar_lancamentos():
        if l["tipo"] == "despesa" and _ano_mes(l["data"])[0] == ano:
            total += float(l["valor"] or 0)
    return round(total, 2)


# ---------------------------------------------------------------------------
# Limite anual
# ---------------------------------------------------------------------------
def status_limite(ano=None):
    """Quanto já faturou x teto do MEI, com alerta de proximidade."""
    ano = ano or date.today().year
    faturado = faturamento_ano(ano)
    limite = config.LIMITE_ANUAL
    pct = round(faturado / limite * 100, 1) if limite else 0
    if pct >= 100:
        nivel = "estouro"      # passou do limite — risco de desenquadramento
    elif pct >= 80:
        nivel = "atencao"
    else:
        nivel = "ok"
    return {
        "ano": ano,
        "faturado": faturado,
        "limite": limite,
        "restante": round(limite - faturado, 2),
        "percentual": pct,
        "nivel": nivel,
    }


# ---------------------------------------------------------------------------
# DAS
# ---------------------------------------------------------------------------
def vencimento_das(ano, mes):
    """O DAS de uma competência vence no dia 20 do mês seguinte."""
    venc_mes = mes + 1
    venc_ano = ano
    if venc_mes > 12:
        venc_mes, venc_ano = 1, ano + 1
    dia = min(config.DIA_VENCIMENTO_DAS, monthrange(venc_ano, venc_mes)[1])
    return date(venc_ano, venc_mes, dia).isoformat()


def gerar_das_competencia(ano, mes):
    """Registra (ou atualiza) o DAS de uma competência com o valor correto."""
    valor = config.valor_das_atual()
    venc = vencimento_das(ano, mes)
    competencia = f"{ano:04d}-{mes:02d}"
    existentes = {d["competencia"]: d for d in planilha.listar_das()}
    status = existentes.get(competencia, {}).get("status", "aberto")
    pago = existentes.get(competencia, {}).get("data_pagamento", "")
    planilha.registrar_das(competencia, valor, venc, status, pago)
    return {"competencia": competencia, "valor": valor, "vencimento": venc, "status": status}


def das_em_aberto():
    """Lista DAS não pagos cujo vencimento já passou ou está próximo."""
    hoje = date.today()
    abertos = []
    for d in planilha.listar_das():
        if d["status"] == "pago":
            continue
        venc = datetime.fromisoformat(str(d["vencimento"])[:10]).date()
        dias = (venc - hoje).days
        abertos.append({**d, "dias_para_vencer": dias, "atrasado": dias < 0})
    return sorted(abertos, key=lambda x: x["vencimento"])


# ---------------------------------------------------------------------------
# Relatório Mensal das Receitas Brutas (obrigação do MEI)
# ---------------------------------------------------------------------------
def relatorio_mensal(ano, mes):
    receitas_com_nf = 0.0
    receitas_sem_nf = 0.0
    for l in planilha.listar_lancamentos():
        if l["tipo"] != "receita":
            continue
        a, m = _ano_mes(l["data"])
        if a == ano and m == mes:
            valor = float(l["valor"] or 0)
            if l.get("nota_id"):
                receitas_com_nf += valor
            else:
                receitas_sem_nf += valor
    return {
        "empresa": config.EMPRESA,
        "competencia": f"{MESES[mes]} de {ano}",
        "receita_com_nota": round(receitas_com_nf, 2),
        "receita_sem_nota": round(receitas_sem_nf, 2),
        "receita_total": round(receitas_com_nf + receitas_sem_nf, 2),
    }


# ---------------------------------------------------------------------------
# Resumo para o painel
# ---------------------------------------------------------------------------
def resumo_dashboard():
    hoje = date.today()
    gerar_das_competencia(hoje.year, hoje.month if hoje.month > 1 else 1)
    return {
        "limite": status_limite(hoje.year),
        "faturamento_mes": faturamento_mes(hoje.year, hoje.month),
        "despesas_ano": despesas_ano(hoje.year),
        "lucro_ano": round(faturamento_ano(hoje.year) - despesas_ano(hoje.year), 2),
        "das_abertos": das_em_aberto(),
        "valor_das": config.valor_das_atual(),
    }
