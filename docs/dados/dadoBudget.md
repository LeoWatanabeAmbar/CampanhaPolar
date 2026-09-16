# Dados do Budget Anual da empresa

**Conforme PDF:** o atingimento do Budget Anual determina se os prêmios são pagos integralmente, parcialmente ou não são pagos. As faixas estão em [regrasCampanha.md](../regras/regrasCampanha.md). **Valor confirmado pelo usuário em 16/09/2026:** R$ 119.000.000 para 2026.

## Origem e abrangência

- Sistema e consulta do realizado: `comercial_marts.fct_pedido_item`, complementada por faturamento, inadimplência e devoluções conforme as regras da campanha.
- Caminho de acesso: função autenticada `public.campanha_polar_carregar_budget_anual()`, criada por `sql/budget_anual.sql`.
- Meta anual: constante de R$ 119.000.000 no painel; não depende das metas mensais regionais.
- Abrangência implementada: vendas comerciais elegíveis da empresa em 2026, sem restringir às regiões participantes da campanha.
- Ano de referência: 2026.
- Atualização: situação atual das fontes até a data local de São Paulo.

## Dicionário de colunas

| Nome real da coluna | O que significa | Tipo/formato | Exemplo fictício |
| --- | --- | --- | --- |
| `data_referencia` | Data até a qual o realizado foi apurado | date | `2026-09-16` |
| `realizado` | Venda bruta elegível de 2026, líquida das devoluções | numeric | `59500000.00` |

## Cálculo e uso no painel

- A fonte fornece o realizado; a meta anual fica configurada no aplicativo.
- Denominador: R$ 119.000.000.
- Numerador implementado: pedidos de 2026 pela implantação, usando as mesmas exclusões comerciais, regras de inadimplência, parcela faturada e devoluções do indicador de vendas.
- Fórmula: `100 * realizado_2026 / 119000000`.
- Escala exibida: percentual em que `50` significa 50%.
- Durante a campanha: mostrar o realizado atual, sem projeção.
- Quem valida o percentual usado nos prêmios: [PREENCHER]
- Se a consulta estiver indisponível ou desatualizada, mostrar o erro da Data API e não apresentar um percentual estimado.

## Exemplo para conferência

- Data de referência: [PREENCHER]
- Meta anual: R$ 119.000.000.
- Realizado considerado: [PREENCHER]
- Percentual esperado: [PREENCHER]
- Situação esperada da campanha: [PREENCHER]
