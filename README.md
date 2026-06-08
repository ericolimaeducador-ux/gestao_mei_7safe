# Gestão MEI

Webapp local (Python + Flask) para gestão contábil de MEI, usando **planilha Excel**
como banco de dados. Roda 100% na sua máquina.

## O que faz
- **Painel**: faturamento do mês, lucro do ano, limite anual (R$ 81.000) e DAS em aberto.
- **Lançamentos**: livro-caixa de receitas e despesas.
- **DAS**: cálculo automático (valores 2026), lembrete de vencimento (dia 20) e registro de pagamento.
- **Notas fiscais**: emissão via provedor (modo `mock` por padrão; pronto para Focus NFe/NFE.io/PlugNotas).
- **Relatório Mensal das Receitas Brutas**: a obrigação acessória do MEI, pronta para imprimir/guardar.

Todos os dados ficam em `dados_mei.xlsx`, criado na primeira execução. Você pode abrir
essa planilha no Excel a qualquer momento.

## Como rodar

```bash
cd gestao-mei
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra no navegador: **http://127.0.0.1:5000**

## Configuração
Edite `mei/config.py`:
- Dados do seu MEI (`EMPRESA`): CNPJ, atividade (`comercio_industria` / `servicos` / `comercio_servicos`).
- Quando o salário mínimo mudar, atualize `SALARIO_MINIMO` — o DAS é recalculado sozinho.
- Para emitir nota real: `PROVEDOR_NFE = "focusnfe"` e preencha `FOCUS_NFE_TOKEN`
  (depois de contratar o provedor e cadastrar seu certificado A1).

## Importante (limites legais)
- **DAS / imposto**: não existe API pública gratuita para *pagar*. O pagamento é no banco
  (Pix/boleto). O sistema calcula, lembra e registra; a guia é gerada no Portal do
  Empreendedor. (Há a API paga SERPRO Integra Contador / PGMEI para gerar a guia.)
- **Nota fiscal**: MEI de serviço usa **NFS-e Nacional** (obrigatório); produto usa
  **NF-e/NFC-e** (exige Certificado Digital A1 `.pfx`/`.p12`). O provedor cuida da
  assinatura e do envio à SEFAZ/Ambiente Nacional.
- Este software organiza sua gestão, mas não substitui um contador para casos específicos
  (desenquadramento, contratação de funcionário, DASN-SIMEI anual etc.).

## Valores fiscais embutidos (2026)
| Atividade               | DAS mensal |
|-------------------------|-----------|
| Comércio/Indústria      | R$ 82,05  |
| Serviços                | R$ 86,05  |
| Comércio + Serviços     | R$ 87,05  |

(INSS R$ 81,05 = 5% do salário mínimo de R$ 1.621 + ICMS R$ 1 e/ou ISS R$ 5.)
