# Dados de metas por região

As metas regionais utilizadas no indicador de vendas ficam aqui. O Budget Anual da empresa é descrito em [dadoBudget.md](dadoBudget.md).

**Confirmado pelo usuário:** utilizar `comercial_marts.metas_comerciais` do Supabase como fonte de metas.

**Conferido no banco em 09/09/2026:** a tabela contém metas por mês e região, com time associado. Não contém código de vendedor.

**Confirmado pelo usuário em 14/09/2026:** a meta deve ser considerada por região. Normalmente há um vendedor por região, mas podem aparecer dois no mesmo mês; nesse caso, manter a meta regional integral e consolidar as vendas da região. Não dividir a meta entre vendedores nem duplicá-la por haver dois nomes no período.

## Origem e organização

- Origem e acesso: leitura da tabela `comercial_marts.metas_comerciais` no Supabase/PostgreSQL.
- Manutenção: cadastro de metas no projeto Gestão Comercial; não foi localizado modelo dbt dessa tabela no dataflow. Responsável e frequência efetiva a confirmar.
- Grão: mês + região. Chave primária confirmada: `(data, regiao)`; `time` é atributo, não parte da chave.
- Periodicidade: mensal. O Gestão Comercial normaliza `data` para o primeiro dia do mês.
- Unidade: valor monetário usado pelo Gestão Comercial na comparação com vendas. **Base do realizado confirmada pelo usuário em 14/09/2026:** valor bruto dos pedidos. Usar `valor_bruto_total` da fonte de vendas e conferir a compatibilidade de moeda e composição com o cadastro da meta.
- Disponibilidade observada em 09/09/2026: 502 linhas, de 01/01/2025 a 01/09/2026, sendo 80 com meta zero.
- Para setembro de 2026: 24 linhas, sendo 4 zeradas. Não existem registros de outubro a dezembro de 2026 nessa consulta. O usuário indicou posteriormente 01/09/2026 como início do recorte da campanha.
- **Disponibilidade confirmada pelo usuário em 14/09/2026:** a meta de outubro só será conhecida em outubro. Durante setembro, comparar as vendas de setembro com a meta de setembro, distribuída pelos dias úteis para obter a meta parcial. Metas de meses futuros não são exigidas para esse acompanhamento e não devem ser estimadas ou preenchidas como zero.

## Dicionário de colunas

| Nome real da coluna | O que significa | Tipo/formato | Exemplo fictício | Pode ficar vazio? |
| --- | --- | --- | --- | --- |
| `data` | Competência mensal | date | `2026-09-01` | Não |
| `regiao` | Região comercial da meta | text | `Região fictícia A` | Não |
| `time` | Time associado à região | text | `Time fictício` | Não |
| `meta` | Valor da meta | numeric(14, 2), conforme DDL do Gestão Comercial | `100000.00` | Não; aceita zero |
| `atualizado_em` | Data/hora da última gravação | timestamp with time zone | `2026-09-01T12:00:00+00:00` | Não |

## Informações necessárias ao entendimento

- Vendedor: não existe nesta tabela. Usar o cadastro `comercial_marts.app_vendedor_regiao_time`, que contém `vendedor_id`, `nome_vendedor`, `regiao`, `time` e `ativo`, para relacionar a região a `fct_pedido_item.vendedor_metricas_id`. O usuário confirmou em 14/09/2026 que não haverá mudança de região dos vendedores durante a campanha.
- Segmento/equipe/regional: `time` e `regiao`. Equivalência confirmada pelo usuário: Time Norte e Time Sul → Construção; Canais → Canais. Mapeamento em [timesSegmentos.csv](timesSegmentos.csv); outros times permanecem pendentes.
- Participação, **confirmada pelo usuário em 14/09/2026**: a própria meta define as regiões elegíveis em cada competência. Selecionar `meta > 0` para os times `Canais`, `Time Norte` e `Time Sul`. Os vendedores vinculados a essas regiões participam dos indicadores individuais. Região sem linha ou com meta zero não entra até que uma meta positiva seja publicada; não estimar valor nem reutilizar a competência anterior.
- Admitidos e desligados, **confirmados pelo usuário em 14/09/2026**: a meta permanece integral na região e não é proporcionalizada pela quantidade de vendedores ou pelos meses de atuação de cada um. Somar normalmente as vendas atribuídas à região. Nos indicadores individuais, cada vendedor acumula somente os eventos elegíveis que tiver, com os mesmos tetos da campanha.
- Período: extrair ano e mês de `data`.
- Valor: `meta`.
- Acompanhamento durante o quadrimestre: somar meta e realizado integrais dos meses encerrados com a meta parcial e o realizado do mês atual. Ao mudar de competência, usar sua própria meta assim que estiver disponível; não repetir a meta anterior como estimativa.
- Fechamento do quadrimestre conforme o PDF: somar as competências de setembro a dezembro do ano confirmado, por região, depois de conferir presença dos quatro meses. A falta de metas futuras não impede o acompanhamento mensal; a falta de uma meta necessária ao fechamento deve ser sinalizada. Meta ausente não deve ser assumida como zero.
- Revisão: o Gestão Comercial atualiza a linha pela chave `(data, regiao)` e modifica `atualizado_em`. Esse timestamp não constitui histórico de versões.
- Regiões sem vendas: manter as regiões participantes com meta positiva cadastrada mesmo quando não houver vendas válidas no período, apresentando realizado zero se a carga estiver válida. A lista de participantes é derivada dessas metas, não de um cadastro separado.
- Metas zeradas: existem. O Gestão Comercial pode criar o mês atual copiando as regiões do mês anterior com `meta = 0`, sem sobrescrever registros; zero pode ser cadastro ainda não preenchido.
- Mais de um vendedor na região: na consulta de 09/09/2026, 20 combinações de região/time tinham mais de um vendedor ativo no cadastro. **Regra confirmada em 14/09/2026:** apurar uma única meta e um único atingimento por região e competência, independentemente da quantidade de vendedores que apareçam nesse mês. Os nomes servem para detalhamento das vendas e conferência dos vínculos.

## Como relacionar com vendas

Para comparação regional, identificar a região de cada venda na competência e agregar as vendas por mês e região, reunindo os valores dos vendedores que atuaram nela. Somente depois relacionar o resultado com a meta na chave `data` + `regiao`. O campo `time` é atributo da meta, não uma chave adicional para duplicar o valor. Juntar metas diretamente a cada item ou vendedor e somar `meta` multiplicaria a meta indevidamente.

**Data confirmada pelo usuário em 14/09/2026:** emissão do pedido = implantação do pedido. Derivar a competência da venda de `fct_pedido_item.data_emissao` e considerar os pedidos elegíveis desse mês implantados até a data de referência para o realizado acumulado. Exemplo: um pedido elegível implantado em 30/09 e faturado em outubro integra o realizado de setembro.

**Vínculo fixo confirmado pelo usuário em 14/09/2026:** não haverá mudança de região dos vendedores durante a campanha. Portanto, usar `fct_pedido_item.vendedor_metricas_id` → `app_vendedor_regiao_time.vendedor_id` → `regiao` para todas as competências da campanha. O cenário de transferência não exige uma fonte de vínculos históricos nesta apuração. Isso não altera a possibilidade já informada de dois vendedores aparecerem na mesma região no mês.

Antes de agregar, conferir que cada vendedor tenha um vínculo regional identificado e sem ambiguidade; inconsistências de cadastro permanecem pendentes, sem multiplicar vendas por duplicidades na relação. Manter competências com meta e sem vendas na comparação e sinalizar vendas sem correspondência de região/meta. A confirmação se refere à campanha de 2026, sem inferir como eram os vínculos anteriores ao período.

Na proposta, manter uma fotografia de acompanhamento por `campanha_id` + `regiao` + `competencia` + `data_referencia`. Meta diária, meta parcial, atingimento e XP de vendas calculado pertencem à região nessa fotografia. Se houver filtro por vendedor para detalhar pedidos, preservar o resumo regional identificado como tal, sem comparar apenas as vendas filtradas de um vendedor com a meta regional inteira como se fosse o atingimento da região.

**Titularidade confirmada pelo usuário em 14/09/2026:** os XP de atingimento de vendas ficam vinculados à própria região, inclusive quando dois vendedores aparecem na competência. Registrar uma única pontuação regional, sem distribuir esses XP aos totais individuais. O rateio já confirmado para triangulações se aplica aos eventos de novos, reativados e mix.

## Meta diária, meta parcial e XP durante o mês

**Confirmado pelo usuário em 14/09/2026:** acompanhar os dias úteis até o fim do mês, a meta de venda por dia útil e o percentual do realizado em relação à meta parcial até hoje. Esse percentual também deve definir os XP de vendas durante o mês. Contar segunda a sexta, descontando feriados nacionais, conforme [Calendário da campanha](calendarioCampanha.md).

**Implementado em 15/09/2026:** a página Venda no Quadrimestre carrega as regiões com meta positiva nas competências decorridas desde setembro. Os meses encerrados entram integralmente; no mês atual, consolida o realizado elegível até a data local de São Paulo e proporcionaliza a meta pelos dias úteis. A consulta autenticada está em `sql/vendas_quadrimestre.sql`; os cálculos acumulados, de calendário e das faixas de XP estão em `polar/vendas.py`.

Usar a mesma região, competência e data de referência no realizado e na meta. O realizado é o acumulado regional do início do mês até a data de referência, reunindo as vendas atribuídas à região nesse período, mesmo que dois vendedores apareçam nela. Não usar apenas a venda do dia nem dividir a meta pelo número de vendedores.

**Valor e rateio confirmados pelo usuário em 14/09/2026:** o realizado comparado à meta é o valor bruto dos pedidos, seguindo as alocações do dataflow e do Gestão Comercial. Agregar `fct_pedido_item.valor_bruto_total` dos itens elegíveis pela região do respectivo vendedor e pelo mês de `data_emissao`, até a referência. Nas triangulações, cada parcela monetária já vem dividida na fonte; não aplicar uma nova divisão. A regra de atribuição regional está definida.

**Elegibilidade confirmada em 14/09/2026:** excluir integralmente os pedidos cancelados do realizado, pois deixam de ser vendas válidas, e recalcular o atingimento e os XP afetados. Para clientes bloqueados por inadimplência segundo o grupo comercial, substituir o total do pedido somente pela parte bruta efetivamente faturada; o saldo em aberto fica fora. SMART PODS e MRV são exceções ao bloqueio e seguem a consideração do pedido pelas demais regras. Após a quitação, reintegrar o saldo em aberto elegível pela data original de implantação, recalculando inclusive uma competência anterior. O mapeamento para `fct_faturamento_item.valor_bruto_item`, também já rateado, está em [Elegibilidade de vendas](elegibilidadeVendas.md).

**Operações excluídas confirmadas em 14/09/2026:** bonificações, remessas e transferências de mercadoria não compõem o realizado regional usado contra a meta. Também não produzem XP de atingimento. Agregar somente vendas comerciais elegíveis após os filtros descritos em [Dados de vendas](dadoVenda.md).

**Estorno fiscal confirmado em 14/09/2026:** pedido ativo continua no realizado regional de sua competência original mesmo que uma nota seja estornada para refaturamento. Não lançar o refaturamento como venda nova. Para cliente bloqueado por inadimplência, considerar no realizado somente o valor coberto por notas válidas na data de referência; durante o intervalo entre estorno e refaturamento, a parcela sem nota válida fica fora.

**Devoluções confirmadas em 14/09/2026:** incluir todas as devoluções no abatimento, sem filtro por setor responsável, motivo, submotivo, tipo ou classificação. Abater somente `valor_devolucao_alocado` do realizado da região e competência de implantação do pedido original. Somar devoluções distintas sem repetir seus identificadores e limitar o realizado líquido ao valor elegível da venda. A data e as classificações da devolução servem para auditoria. Após o abatimento, recalcular meta atingida e XP regional da competência original; uma devolução ocorrida em outubro pode alterar setembro sem gerar uma venda negativa em outubro.

Exemplo de triangulação: pedido de R$ 10.000 com vendedor A da região A e vendedor B da região B gera R$ 5.000 de realizado em cada região. Se ambos pertencerem à região A, as duas alocações totalizam R$ 10.000 somente nessa região. Em ambos os casos, cada região mantém sua meta integral e calcula seus próprios XP de vendas pelo atingimento, sem ratear esses XP entre os vendedores.

| Indicador proposto | Cálculo ou significado |
| --- | --- |
| `regiao`, `competencia`, `data_referencia` | Identificação da região, do mês e da fotografia de acompanhamento |
| `meta_mes` | Meta integral cadastrada para a região e competência selecionadas |
| `realizado_mes_ate_data` | Soma do valor bruto elegível por região e mês de implantação, líquida das devoluções vinculadas aos pedidos originais: excluir cancelados, bonificações, remessas e transferências de mercadoria; para bloqueados por inadimplência, usar somente a parte faturada válida. SMART PODS/MRV são exceções ao bloqueio |
| `dias_uteis_mes` | Total de dias úteis do mês |
| `dias_uteis_decorridos` | Dias úteis até a referência, incluindo esse dia quando útil |
| `dias_uteis_restantes` | Dias úteis após a referência até o fim do mês |
| `meta_diaria_planejada` | `meta_mes / dias_uteis_mes` |
| `meta_parcial_ate_data` | `meta_mes * dias_uteis_decorridos / dias_uteis_mes` |
| `metas_publicadas` | Soma das metas integrais de setembro até o mês atual |
| `meta_acumulada_ate_data` | Soma das metas integrais dos meses encerrados com `meta_parcial_ate_data` do mês atual |
| `realizado_acumulado` | Soma do realizado elegível de setembro até a data de referência |
| `atingimento_acumulado_pct` | `100 * realizado_acumulado / meta_acumulada_ate_data` |
| `xp_vendas_atual` | XP da região calculado uma vez pela faixa do percentual acumulado exato |
| `saldo_metas_publicadas` | `max(metas_publicadas - realizado_acumulado, 0)` |
| `venda_necessaria_por_dia_restante` | `saldo_metas_publicadas / dias_uteis_restantes`, para mostrar o ritmo necessário até o fim do mês atual |

A meta diária planejada distribui a meta atual entre todos os dias úteis do mês. O valor necessário por dia restante distribui o saldo acumulado das metas publicadas entre os dias futuros do mês atual. A meta acumulada cresce conforme o calendário, mantendo o percentual exato, sem arredondar os valores intermediários para enquadrar XP. Valores arredondados servem somente à exibição.

O XP atual é uma fotografia acumulada recalculada a cada referência. Pode aumentar ou diminuir conforme o realizado, o avanço da meta parcial e mudanças na situação dos pedidos. Em outubro, usar a meta própria de outubro na parcela do mês e somá-la à meta integral de setembro; não reutilizar a meta de setembro como estimativa para outubro. Se a meta do novo mês ainda não estiver cadastrada, sinalizar `Meta do mês não disponível` e encerrar o acumulado no último mês publicado. Não somar fotografias diárias nem os XP mensais: calcular uma única faixa sobre o atingimento acumulado. Esse resultado também continua sendo recalculado depois de fechamentos anteriores quando cancelamentos, devoluções, quitações, estornos ou outras correções mudarem as fontes. Os tetos de novos e reativados permanecem acumulados na campanha por vendedor; o de antecipação permanece acumulado por região, conforme [Dados de adiantamento](dadoAdiantamento.md).

### Condições de cálculo

- Meta ausente, zero ou negativa: manter o percentual e os XP dependentes da meta pendentes, sem dividir por zero nem assumir atingimento zero. A política definitiva para metas zeradas continua a definir.
- Zero dias úteis no mês ou zero dias úteis decorridos: sinalizar que ainda não há base válida para a meta parcial; não calcular seu percentual nem os XP de vendas.
- Zero dias úteis restantes: apresentar o resultado do mês e o saldo, sem calcular a divisão por dias futuros.
- Meta superada: o saldo para chegar a 100% é zero; o atingimento e os XP continuam acima de 100%, conforme as faixas, sem teto neste indicador.
- Dados de vendas desatualizados: mostrar a data/hora da carga junto à referência da meta, sem apresentar valores antigos como vendas atualizadas até hoje.

### Exemplo para conferência

Calendário real de setembro de 2026, referência em **14/09/2026**, incluindo esse dia: **21 dias úteis no mês, 9 decorridos e 12 restantes**. O exemplo representa a **Região fictícia A**. Os valores de meta e vendas abaixo são **inteiramente fictícios**, sem consulta nova ao Supabase.

| Indicador | Resultado do exemplo |
| --- | ---: |
| Meta regional de setembro | R$ 210.000,00 |
| Meta diária planejada: 210.000 / 21 | R$ 10.000,00 |
| Meta parcial até 14/09: 10.000 × 9 | R$ 90.000,00 |
| Realizado do mês até a referência | R$ 99.000,00 |
| Atingimento acumulado: 99.000 / 90.000 × 100 | 110% |
| XP de vendas calculado para a região na referência | 550 XP |
| Saldo para a meta mensal: 210.000 − 99.000 | R$ 111.000,00 |
| Venda necessária por dia restante: 111.000 / 12 | R$ 9.250,00 |

Se o realizado de R$ 99.000 for composto por R$ 60.000 do vendedor A e R$ 39.000 do vendedor B, ambos atribuídos à mesma região no mês, o resultado regional continua o da tabela: meta mensal de R$ 210.000, meta parcial de R$ 90.000, atingimento de 110% e 550 XP registrados na região. A meta não passa a R$ 105.000 por vendedor nem a R$ 420.000 no total. Os 550 XP permanecem na região, conforme confirmado pelo usuário.

## Amostra

Exemplo inteiramente fictício para ilustrar quatro competências. Não indica que esses meses já estejam cadastrados no banco.

```text
data;regiao;time;meta;atualizado_em
2026-09-01;Região fictícia A;Time fictício;100000.00;2026-09-01T12:00:00+00:00
2026-10-01;Região fictícia A;Time fictício;110000.00;2026-09-01T12:00:00+00:00
2026-11-01;Região fictícia A;Time fictício;120000.00;2026-09-01T12:00:00+00:00
2026-12-01;Região fictícia A;Time fictício;130000.00;2026-09-01T12:00:00+00:00
```

## Conferência

- Região fictícia A: metas de 100.000, 110.000, 120.000 e 130.000; total esperado de 460.000.
- Caso com dois vendedores no mesmo mês/região: usar o exemplo de R$ 60.000 + R$ 39.000 acima, mantendo uma única meta e um único resultado regional.
- Vínculo regional durante a campanha: usar `app_vendedor_regiao_time` porque o usuário confirmou que não haverá mudança de região no período. Admitidos e desligados continuam relacionados pela região de suas vendas; não excluir o histórico por `ativo = false`.

## Referências examinadas

- `gestao_comercial/Gestao_Comercial/modulos_app/00_configuracao.py`: schema e mapeamento da tabela.
- `gestao_comercial/Gestao_Comercial/modulos_app/10_repositorios.py`: DDL, leitura, gravação e criação de metas zeradas.
- Schema, chave primária e agregados de disponibilidade consultados no Supabase em 09/09/2026. Nenhuma alteração foi feita no banco.
