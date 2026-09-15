# Dados de vendas

**Confirmado pelo usuário:** utilizar `comercial_marts.fct_pedido_item` do Supabase como fonte de vendas.

O modelo SQL do dataflow foi examinado e a estrutura foi conferida diretamente no Supabase, em consulta somente leitura em 09/09/2026. O mapeamento abaixo documenta a fonte para o futuro painel; as regras específicas de XP ainda dependem das definições em [regraNegocio.md](../regras/regraNegocio.md).

## Origem e disponibilidade

- Sistema de origem: pedidos do Protheus, tratados pelo dataflow e publicados no Supabase/PostgreSQL.
- Forma de acesso: leitura de `comercial_marts.fct_pedido_item`.
- Formato: tabela relacional; datas do tipo `date`, identificadores `text` e valores `numeric`.
- Responsável e frequência de atualização: carga pelo dataflow; responsável e agendamento efetivo a confirmar.
- Histórico observado em 09/09/2026: 125.056 linhas, com `data_emissao` entre 03/01/2022 e 09/09/2026, antes dos filtros de vendas válidas. Esse intervalo não comprova completude do histórico.
- **Critério da campanha confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar clientes novos e primeiras compras das linhas de mix, sem exigir períodos anteriores a 2022. Essa definição de uso não altera a fotografia da consulta acima; inconsistências de cadastro ou datas continuam sendo tratadas como pendências.
- Grão: item de pedido por alocação comercial. A chave `pedido_item_id` concatena filial, pedido, item, produto, nota e tipo de alocação.
- Atualização: modelo dbt materializado como `table`, reconstruído nas execuções; não é um histórico de versões da venda.
- Fontes complementares identificadas no código em 14/09/2026: `vw_clientes_inadimplentes` para o bloqueio financeiro, `fct_faturamento_item` para o valor bruto efetivamente faturado e `fct_nota_devolucao` para o valor devolvido alocado. A disponibilidade atual e os vínculos ainda devem ser validados no banco; detalhes em [Elegibilidade de vendas](elegibilidadeVendas.md).

## Dicionário de colunas

Campos relevantes para a campanha. A tabela no banco permite nulos nesses campos; os testes dbt exigem unicidade de `pedido_item_id` no recorte `is_item_valido_metricas`. Isso não substitui a conferência dos dados na carga do painel.

| Nome real da coluna | O que significa | Tipo/formato | Exemplo fictício | Pode ficar vazio? |
| --- | --- | --- | --- | --- |
| `pedido_item_id` | Chave da linha, incluindo alocação | text | `01101-900001-01-PX0001-sem_nota-representante` | Sim no schema |
| `filial_id`, `pedido_id`, `item_pedido` | Identificadores do pedido e item | text | `01101`, `900001`, `01` | Sim no schema |
| `data_emissao` | Data de emissão = data de implantação do pedido; referência confirmada para a campanha | date | `2026-09-01` | Sim no schema |
| `data_faturamento_operacional`, `data_entrega` | Datas operacionais de faturamento e entrega | date | `2026-09-02` | Sim |
| `cliente_id`, `loja_cliente_id` | Chave composta de cliente e loja | text | `900001`, `01` | Sim no schema |
| `vendedor_metricas_id` | Vendedor da alocação comercial da linha | text | `900001` | Sim |
| `representante_id`, `executivo_id`, `vendedor_interno_id` | Responsáveis presentes no pedido | text | `900001` | Sim |
| `tipo_alocacao_comercial` | Papel ao qual a linha está atribuída | text | `representante` ou `executivo` | Sim no schema |
| `produto_id`, `descricao_produto_pedido` | Código e descrição do produto no pedido | text | `PX0001`, `Produto fictício` | Sim no schema |
| `linha_produto`, `subfamilia` | Agrupamentos comerciais do produto | text | `Linha fictícia`, `Família fictícia` | Sim |
| `quantidade_vendida`, `quantidade_entregue`, `quantidade_nao_faturada` | Quantidades ajustadas pelo dataflow | numeric | `10` | Sim no schema |
| `valor_bruto_total` | Venda bruta comercial, referência para o realizado comparado à meta; metade do valor original em triangulações | numeric | `1500.00` | Sim no schema |
| `valor_operacional`, `valor_frete_item`, `valor_ipi_item`, `valor_icms_st` | Componentes ajustados do valor comercial | numeric | `100.00` | Sim no schema |
| `valor_bruto_nao_faturado` | Saldo bruto em aberto | numeric | `500.00` | Sim no schema |
| `status_item_pedido` | Estado do item | text | `excluido`, `bloqueado`, `faturado`, `em_aberto` | Sim no schema |
| `is_item_valido_metricas`, `is_venda_comercial` | Elegibilidade técnica e classificação como venda | boolean | `true` | Sim no schema |
| `is_triangulacao`, `is_remessa`, `is_devolucao`, `is_transferencia`, `is_bonificacao` | Indicadores da operação | boolean | `false` | Sim no schema |
| `nota_fiscal_id`, `cfop_classificacao`, `classe_operacao` | Nota e classificação fiscal/comercial | text | `900001`, `5102`, `VENDA` | Sim no schema |
| `data_disponivel_faturamento`, `classificacao_programado_carteira` | Disponibilidade e classificação de programação | date / text | `2026-10-01`, `Programado` | Sim no schema |

## Onde encontrar cada informação

Informe a coluna, outra base de origem ou `Não disponível`.

| Informação | Coluna ou origem |
| --- | --- |
| Identificador único da venda e do item | `pedido_item_id`; pedido identificado por `filial_id` + `pedido_id` |
| Data do pedido e do faturamento | `data_emissao` representa a implantação do pedido e determina sua data de apuração na campanha, conforme confirmado pelo usuário; `data_faturamento_operacional` registra o faturamento |
| Código e nome do vendedor | `vendedor_metricas_id`; nome em `dim_vendedor` ou `app_vendedor_regiao_time`, por `vendedor_id` |
| Código do cliente / CNPJ | `cliente_id` + `loja_cliente_id`; documento em `dim_cliente.documento_cliente`, usando as duas chaves |
| Segmento: Construção ou Canais | `app_vendedor_regiao_time.time`, ligado por vendedor: Time Norte e Time Sul → Construção; Canais → Canais, conforme confirmado pelo usuário. Mapeamento em [timesSegmentos.csv](timesSegmentos.csv). |
| Código, nome e família do produto | `produto_id`, `descricao_produto_pedido`, `linha_produto`, `subfamilia`; cadastro em `dim_produto` |
| Quantidade e valor da venda | `quantidade_vendida` e `valor_bruto_total` |
| Inadimplência e exceções | `vw_clientes_inadimplentes.cliente_loja_id`, relacionado por cliente/loja; propaga o bloqueio ao grupo e exclui SMART PODS/MRV, conforme regra confirmada |
| Parte faturada elegível de cliente bloqueado | Fonte complementar proposta: `fct_faturamento_item.valor_bruto_item`, já rateado por alocação. Vincular por pedido/produto e filial, preservando cliente/loja e as notas válidas |
| Status, cancelamento e devolução | `status_item_pedido` e flags de exclusão/bloqueio; devoluções posteriores em `fct_nota_devolucao`, relacionadas pela nota fiscal original |

- Formato das datas e separadores decimais: datas e números nativos do banco; exemplos textuais usam `YYYY-MM-DD` e ponto decimal.
- Data da venda, **confirmada pelo usuário em 14/09/2026**: emissão do pedido = implantação do pedido. Usar `data_emissao` para incluir pedidos no período da campanha, agrupar por mês e apurar o realizado até a data de referência. Exemplo: um pedido elegível implantado em 30/09 e faturado em outubro compõe setembro. As condições de status, cancelamento e valor continuam nas suas definições próprias.
- Valor do realizado, **confirmado pelo usuário em 14/09/2026**: usar o valor bruto dos pedidos na comparação com a meta. Mapear para `valor_bruto_total` na fonte e agregar os itens elegíveis por região e competência de `data_emissao`. Manter a composição fornecida pelo dataflow, conferindo impostos, frete e descontos na origem antes de propor ajustes. O rateio monetário segue o dataflow e o Gestão Comercial, conforme confirmação abaixo.
- Zeros à esquerda: preservar identificadores como texto, inclusive filial, pedido, item, cliente, loja, vendedor e produto.
- Vínculo com metas: **confirmado pelo usuário em 14/09/2026**, consolidar vendas por região e competência antes de relacionar com a única meta regional em `metas_comerciais`, mesmo que dois vendedores apareçam na região no mês. Não dividir ou duplicar a meta. Como não haverá mudança de região dos vendedores durante a campanha, usar o vínculo fixo entre `vendedor_metricas_id` e `app_vendedor_regiao_time.vendedor_id` para obter `regiao`; conferir vínculos ausentes ou ambíguos antes de consolidar. Ver [dadoMeta.md](dadoMeta.md).
- Admissão e desligamento, **confirmados pelo usuário em 14/09/2026**: não filtrar vendas históricas apenas por `app_vendedor_regiao_time.ativo = true`. Incluir as vendas elegíveis atribuídas ao vendedor admitido ou desligado e preservar seus resultados após a inativação. O campo `ativo` serve para indicar a situação atual; não altera a data ou a autoria de uma venda já realizada.
- Vínculo com antecipações: confirmação manual por região/mês, conforme [Dados de adiantamento](dadoAdiantamento.md). Cancelamentos e mudanças na elegibilidade de vendas não alteram automaticamente os checks.
- Filtros já aplicados no modelo: `tipo_pedido = 'N'` e produtos elegíveis de seis caracteres com prefixos `PX`, `PI`, `2M` ou `00`.
- Filtros de venda comercial usados no dataflow: `is_item_valido_metricas = true` e `is_venda_comercial = true`. Itens bloqueados/excluídos continuam presentes na tabela e precisam ser filtrados.
- **Operações não comerciais — confirmado pelo usuário em 14/09/2026:** bonificações, remessas e transferências de mercadoria não entram no realizado, no histórico de compras elegíveis nem em qualquer XP. Além de exigir `is_venda_comercial = true`, excluir registros com `is_bonificacao`, `is_remessa` ou `is_transferencia` igual a `true`. Usar `classe_operacao` e `cfop_classificacao` para auditoria. Se uma linha estiver simultaneamente marcada como venda comercial e uma dessas operações excluídas, mantê-la pendente para correção em vez de incluí-la.
- Cancelamentos, **confirmados pelo usuário em 14/09/2026**: tratar o pedido cancelado como integralmente excluído e, portanto, como uma venda inválida. Nenhum item ou alocação desse pedido entra no realizado, no histórico de compras elegíveis ou nos XP, mesmo que exista faturamento. Os campos `is_item_excluido_logicamente`, `is_pedido_excluido_logicamente`, `status_item_pedido = 'excluido'` e `is_item_valido_metricas = false` evidenciam exclusões no código; conferir a representação do cancelamento na origem, sem inventar um status `cancelado` no fato. Preservar o pedido fora da base elegível somente para auditoria e recalcular os eventos posteriores afetados.
- Estorno de nota fiscal, **confirmado pelo usuário em 14/09/2026**: se o pedido permanecer ativo, continuar considerando `fct_pedido_item` pela sua `data_emissao` original. Não usar a data do refaturamento como nova venda e deduplicar notas pelo pedido/item para impedir novo valor ou XP. Para cliente bloqueado por inadimplência, `fct_faturamento_item` deve conter apenas notas válidas: retirar a nota estornada da soma faturada e voltar a considerar sua parcela somente quando uma nova nota válida comprovar o refaturamento. A disponibilidade de uma marca explícita de estorno no fato final precisa ser validada; a staging de cabeçalho fiscal expõe exclusão lógica, enquanto os itens fiscais excluídos não aparecem na staging observada.
- **Atualização contínua — confirmada pelo usuário em 14/09/2026:** usar o estado atual de cada pedido e nota em toda reconstrução. Alterações posteriores devem atualizar a competência original e os eventos dependentes, sem congelar registros por já terem aparecido em um fechamento. Preservar identificadores, data/hora de processamento e motivos de entrada ou saída para comparar fotografias sucessivas.
- Inadimplência, **confirmada pelo usuário em 14/09/2026**: para clientes bloqueados pelo critério de grupo do Gestão Comercial, considerar somente o valor bruto efetivamente faturado, mantendo o saldo em aberto excluído. SMART PODS e MRV são exceções ao bloqueio. O valor elegível faturado substitui o total do pedido nesse caso, preserva a competência de implantação e os rateios regionais, sem somar total e faturado. Se o grupo quitar a dívida durante a campanha, reintegrar o saldo em aberto pela implantação original e recalcular os resultados afetados; usar o estado financeiro atual para a elegibilidade corrente.
- Devoluções, **confirmadas pelo usuário em 14/09/2026**: incluir todas as devoluções, sem filtrar por setor responsável, motivo, submotivo, tipo ou outra classificação. Somar `fct_nota_devolucao.valor_devolucao_alocado` por nota original e alocação e abater somente esse valor da região e competência de implantação do pedido. Não usar `data_devolucao` como competência do abatimento. A fonte já divide a devolução entre as alocações da nota; não dividir novamente. Relacionar a nota original ao faturamento e ao pedido para recuperar `data_emissao`. Como a saída observada não possui produto/item, devoluções de notas com produtos de várias linhas exigem detalhe adicional antes de recalcular o mix.
- Particularidade das alocações: `int_venda_valor_bruto` divide por dois os valores e as quantidades ajustadas em triangulações. O fato gera uma linha de representante e, havendo executivo informado, outra de executivo, cada uma com metade do valor original. Nesse caso, a soma das duas alocações recompõe o valor original; deduplicar por item ou dividir novamente reduziria o total indevidamente.
- **Rateio monetário confirmado pelo usuário em 14/09/2026:** seguir o dataflow e o Gestão Comercial. Cada parcela de `valor_bruto_total` compõe o realizado da região do respectivo `vendedor_metricas_id`. Em uma triangulação de R$ 10.000 entre vendedores de regiões diferentes, cada região contabiliza R$ 5.000. Se os dois vendedores pertencem à mesma região, as duas parcelas somam R$ 10.000 nessa região. Consumir os valores já rateados, sem dividi-los novamente nem atribuir o total integral a cada região. Manter a única meta regional e calcular os XP de vendas pelo atingimento resultante.
- **XP em triangulações — confirmado pelo usuário em 14/09/2026:** dividir igualmente os XP dos eventos elegíveis entre os dois vendedores. Na proposta, identificar a operação por `is_triangulacao` e os participantes por `vendedor_metricas_id` nas alocações de representante e executivo, conferindo `representante_id` e `executivo_id`. Calcular o XP do evento físico uma vez e atribuir 50% a cada vendedor: 5 XP por novo, 4 por reativado e 5 por linha de mix elegível. Aplicar os tetos após somar as parcelas por vendedor e indicador. Os valores monetários já rateados na fonte não devem ser novamente divididos por causa dessa regra de XP.
- **Mínimo de mix em triangulações — confirmado pelo usuário em 14/09/2026:** usar o valor total da linha no pedido antes do rateio entre vendedores. Na proposta, somar `valor_bruto_total` dos itens dessa linha e das alocações válidas e completas de representante e executivo, sem dividir novamente nem eliminar uma das alocações como duplicata. Exemplo confirmado: R$ 1.500 em cada alocação recompõe R$ 3.000 de Hydrofix, atingindo o mínimo de Construção; os XP dependem também das demais condições de mix.
- Triangulação sem executivo: o SQL mantém apenas a alocação de representante, já com metade do valor original. A soma incompleta não comprova o total da linha para o mínimo de mix; manter a conferência de valor e atribuição pendente até validar as alocações ou obter evidência do valor completo. A soma também precisa dessa conferência antes de ser usada como total físico de vendas.
- Contagem de pedidos, clientes e produtos: as alocações não representam novas compras físicas. Preservar o pedido físico por filial + pedido para auditoria e valores, mas consolidar a classificação de novos, reativados e mix em um evento por `grupo_comercial_id` + `data_emissao`. Somar os valores elegíveis dos pedidos desse evento por linha de mix. Pedidos em datas diferentes continuam separados.
- Devoluções: `is_devolucao` classifica a própria operação do item e não comprova o abatimento posterior. Usar `fct_nota_devolucao` para todas as notas de devolução vinculadas à nota original e preservar os identificadores para impedir abatimento duplicado. Classificações complementares servem para auditoria e não devem filtrar o abatimento da campanha.
- Faturamento: o status `faturado` é derivado da presença de nota no item; não garante que a quantidade total foi faturada. Para a regra de inadimplência, usar evidências e valor efetivamente faturado, conforme [Elegibilidade de vendas](elegibilidadeVendas.md), sem liberar todo o pedido pelo status de um item.

## Amostra

Exemplo inteiramente fictício, com seleção de colunas reais. As duas últimas linhas ilustram um item original de 4.000, rateado em 2.000 para cada alocação; não representam duas vendas físicas.

```text
filial_id;pedido_id;item_pedido;produto_id;data_emissao;vendedor_metricas_id;tipo_alocacao_comercial;valor_bruto_total
01101;900001;01;PX0001;2026-09-01;900001;representante;1500.00
01101;900002;01;PX0002;2026-09-02;900002;representante;2000.00
01101;900002;01;PX0002;2026-09-02;900003;executivo;2000.00
```

## Conferência

- Relatório ou total de referência para validar as vendas: [PREENCHER]
- Período e valor esperado em um exemplo: [PREENCHER]

## Referências examinadas

- `dataflow/models/marts/comercial/fct_pedido_item.sql`: grão, alocações, filtros e campos finais.
- `dataflow/models/intermediate/comercial/int_venda_valor_bruto.sql`: cálculo reutilizado pelo fato.
- `dataflow/models/marts/comercial/_comercial_marts.yml`: testes declarados.
- `dataflow/docs/08_metricas/metricas_comerciais_iniciais.md`: venda bruta baseada em `valor_bruto_total`.
- Schema real e agregados de disponibilidade consultados no Supabase em 09/09/2026. Nenhuma alteração foi feita no banco.
