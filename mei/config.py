"""
Parâmetros do sistema. Edite este arquivo com os dados do seu MEI.
Os valores fiscais já estão calculados para 2026 (salário mínimo R$ 1.621).
Quando o salário mínimo mudar, basta atualizar SALARIO_MINIMO e rodar
recalcular_das() — todo o resto se ajusta sozinho.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Caminho da planilha (o "banco de dados"). Fica na mesma pasta do projeto.
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
PLANILHA = BASE_DIR / "dados_mei.xlsx"

# ---------------------------------------------------------------------------
# Dados do seu MEI  (preencha aqui)
# ---------------------------------------------------------------------------
EMPRESA = {
    "razao_social": "7safe",
    "cnpj": "55.747.955/0001-07",
    "atividade": "servicos",   # comercio_industria | servicos | comercio_servicos
    "municipio": "Belo Horizonte",
    "uf": "MG",
    "abertura": "2024-01-01",  # data de abertura do CNPJ (AAAA-MM-DD)
}

# ---------------------------------------------------------------------------
# Parâmetros fiscais — referência 2026
# ---------------------------------------------------------------------------
SALARIO_MINIMO = 1621.00          # vigente em 2026
INSS_ALIQUOTA = 0.05              # MEI recolhe 5% do salário mínimo
ICMS_FIXO = 1.00                  # comércio / indústria
ISS_FIXO = 5.00                   # serviços

LIMITE_ANUAL = 81_000.00          # teto de faturamento do MEI
LIMITE_MENSAL_PROPORCIONAL = 6_750.00   # para CNPJ aberto durante o ano
DIA_VENCIMENTO_DAS = 20           # DAS vence todo dia 20


def _inss():
    return round(SALARIO_MINIMO * INSS_ALIQUOTA, 2)


def recalcular_das():
    """Retorna o valor do DAS por tipo de atividade, conforme o salário mínimo atual."""
    inss = _inss()
    return {
        "comercio_industria": round(inss + ICMS_FIXO, 2),
        "servicos": round(inss + ISS_FIXO, 2),
        "comercio_servicos": round(inss + ICMS_FIXO + ISS_FIXO, 2),
    }


DAS_VALORES = recalcular_das()


def valor_das_atual():
    """DAS do mês para a atividade configurada da empresa."""
    return DAS_VALORES.get(EMPRESA["atividade"], DAS_VALORES["servicos"])


# ---------------------------------------------------------------------------
# Integração fiscal (NF-e / NFS-e). Preencha quando contratar um provedor.
# Deixe PROVEDOR = "mock" para testar sem chave (gera nota fictícia local).
# ---------------------------------------------------------------------------
PROVEDOR_NFE = "mock"             # "mock" | "focusnfe" | "nfeio" | "plugnotas"
FOCUS_NFE_TOKEN = ""              # token da API (quando usar focusnfe)
FOCUS_NFE_AMBIENTE = "homologacao"  # "homologacao" para testes, "producao" para valer
