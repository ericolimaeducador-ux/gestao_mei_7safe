"""
Integração fiscal — emissão de nota.

Estratégia: o software fala com um PROVEDOR (definido em config.PROVEDOR_NFE).
  - "mock"     -> não chama ninguém; gera uma nota fictícia local (para testar tudo).
  - "focusnfe" -> chama a API REST da Focus NFe (precisa de token + certificado A1
                  cadastrado no painel deles). É só um exemplo; o mesmo padrão vale
                  para NFE.io, PlugNotas, WebmaniaBR etc.

IMPORTANTE sobre o MEI:
  - Serviço  -> NFS-e no padrão NACIONAL (obrigatório para MEI).
  - Produto  -> NF-e / NFC-e (exige Certificado Digital A1 .pfx/.p12).
  - O provedor cuida da assinatura digital e do envio à SEFAZ/Ambiente Nacional.

Sobre o DAS (imposto): NÃO há API pública gratuita para PAGAR. O pagamento é no
banco (boleto/Pix). A função gerar_guia_das() abaixo deixa o ponto de integração
pronto para o SERPRO Integra Contador (PGMEI), caso você contrate.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

from . import config, planilha


# ---------------------------------------------------------------------------
# Função pública usada pelo app
# ---------------------------------------------------------------------------
def emitir_nota(tomador, cnpj_cpf, descricao, valor, tipo="servico"):
    """
    Emite a nota pelo provedor configurado e registra na planilha.
    Retorna um dict com status e (se houver) link do PDF/portal.
    """
    valor = float(valor)
    if config.PROVEDOR_NFE == "focusnfe":
        resultado = _emitir_focusnfe(tomador, cnpj_cpf, descricao, valor, tipo)
    else:
        resultado = _emitir_mock(tomador, cnpj_cpf, descricao, valor, tipo)

    nota_id = planilha.adicionar_nota(
        data=datetime.now().date().isoformat(),
        tomador=tomador,
        cnpj_cpf=cnpj_cpf,
        descricao=descricao,
        valor=valor,
        tipo=tipo,
        status=resultado["status"],
        link=resultado.get("link", ""),
    )
    resultado["nota_id"] = nota_id
    return resultado


# ---------------------------------------------------------------------------
# Provedor MOCK (para testar sem chave nem certificado)
# ---------------------------------------------------------------------------
def _emitir_mock(tomador, cnpj_cpf, descricao, valor, tipo):
    ref = "MOCK-" + datetime.now().strftime("%Y%m%d%H%M%S")
    return {
        "status": "autorizado",
        "referencia": ref,
        "link": "",
        "mensagem": "Nota fictícia gerada localmente (modo mock). "
                    "Configure um provedor real em config.PROVEDOR_NFE.",
    }


# ---------------------------------------------------------------------------
# Provedor Focus NFe (exemplo real — NFS-e Nacional)
# Doc: https://focusnfe.com.br  | precisa de token e certificado cadastrado.
# ---------------------------------------------------------------------------
def _emitir_focusnfe(tomador, cnpj_cpf, descricao, valor, tipo):
    if not config.FOCUS_NFE_TOKEN:
        return {"status": "erro", "mensagem": "FOCUS_NFE_TOKEN não configurado em config.py"}

    base = ("https://homologacao.focusnfe.com.br"
            if config.FOCUS_NFE_AMBIENTE == "homologacao"
            else "https://api.focusnfe.com.br")
    ref = datetime.now().strftime("%Y%m%d%H%M%S")
    url = f"{base}/v2/nfsen?ref={ref}"   # endpoint da NFS-e Nacional

    payload = {
        "data_emissao": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "prestador": {"cnpj": config.EMPRESA["cnpj"].replace(".", "").replace("/", "").replace("-", "")},
        "tomador": {"cpf_cnpj": cnpj_cpf, "razao_social": tomador},
        "servico": {"discriminacao": descricao, "valor_servicos": valor},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    # autenticação básica: token como usuário, senha vazia
    import base64
    token = base64.b64encode(f"{config.FOCUS_NFE_TOKEN}:".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            corpo = json.loads(resp.read().decode("utf-8"))
        return {
            "status": corpo.get("status", "processando"),
            "referencia": ref,
            "link": corpo.get("url") or corpo.get("caminho_xml_nota_fiscal", ""),
            "mensagem": "Enviado à Focus NFe.",
        }
    except urllib.error.HTTPError as e:
        return {"status": "erro", "mensagem": f"HTTP {e.code}: {e.read().decode('utf-8')[:300]}"}
    except Exception as e:  # noqa: BLE001
        return {"status": "erro", "mensagem": str(e)}


# ---------------------------------------------------------------------------
# DAS — ponto de integração com o SERPRO Integra Contador (opcional/pago)
# ---------------------------------------------------------------------------
def gerar_guia_das(competencia):
    """
    Placeholder. Para gerar a guia (boleto/Pix) automaticamente seria necessário
    contratar o SERPRO Integra Contador (módulo PGMEI) e usar certificado e-CNPJ.
    Por ora, retornamos a orientação manual.
    """
    return {
        "competencia": competencia,
        "valor": config.valor_das_atual(),
        "como_pagar": "Gere o DAS no Portal do Empreendedor / app MEI (CNPJ -> "
                      "Emitir Guia de Pagamento) e pague via Pix (QR Code) ou boleto.",
        "api_disponivel": False,
    }
