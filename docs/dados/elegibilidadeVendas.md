# Elegibilidade: cancelamentos, inadimplência e faturamento

## Regras confirmadas

**Confirmado pelo usuário em 14/09/2026:** cancelar um pedido equivale a excluí-lo integralmente. Ele deixa de ser uma venda válida e deve sair do realizado, do histórico de compras elegíveis e de todos os XP. Quando o cancelamento ocorre após uma apuração, recalcular os resultados e os pedidos posteriores afetados como se esse pedido nunca tivesse participado. Pedidos de clientes inadimplentes não devem ser considerados, exceto quando já faturados.

**Detalhamento confirmado pelo usuário:** seguir o bloqueio por grupo comercial do Gestão Comercial, com exceções para **SMART PODS (SMARTPODS)** e **MRV**. Para os demais clientes bloqueados, considerar **somente a parte já faturada** quando o pedido tiver faturamento parcial. O saldo em aberto permanece excluído.

**Quitação confirmada pelo usuário em 14/09/2026:** quando o cliente deixa de estar inadimplente durante a campanha, seus pedidos em aberto voltam a ser considerados com a **data original de implantação**. A quitação não muda a competência do pedido. Recalcular o realizado e os XP afetados, inclusive competências anteriores da campanha.

**Efeito no histórico confirmado pelo usuário em 14/09/2026:** enquanto estiver bloqueado por inadimplência, o pedido não faturado também deve ser ignorado como compra anterior para classificar cliente novo, reativado e expansão de mix. Em faturamento parcial, somente os itens e quantidades faturados compõem o histórico. Após a quitação, a parte em aberto retorna com sua data original e pode reclassificar o próprio evento e pedidos posteriores.

**Devoluções confirmadas pelo usuário em 14/09/2026:** todas as devoluções entram no abatimento, independentemente do setor responsável, motivo, submotivo, tipo ou outra classificação. Abater somente o valor efetivamente devolvido da competência original de implantação do pedido e recalcular os XP afetados. A data da devolução serve para rastreabilidade; não transfere o abatimento para o mês em que a devolução ocorreu.

A data da venda continua sendo a implantação do pedido (`data_emissao`). O faturamento determina a exceção à inadimplência; a competência da venda continua sendo a de implantação. O realizado usa o valor bruto e as alocações regionais do dataflow/Gestão Comercial, conforme [Dados de vendas](dadoVenda.md).

**Operações não comerciais confirmadas pelo usuário em 14/09/2026:** bonificações, remessas e transferências de mercadoria ficam fora da base de compras elegíveis. Não entram no realizado, não iniciam ou interrompem histórico para novos e reativados, não caracterizam primeira compra de mix e não geram XP. Exigir `is_venda_comercial = true` e excluir registros com `is_bonificacao = true`, `is_remessa = true` ou `is_transferencia = true`. Se as flags forem contraditórias, manter o registro pendente para correção cadastral, sem crédito provisório.

**Estorno de nota fiscal confirmado pelo usuário em 14/09/2026:** o estorno isolado da nota não invalida um pedido que permaneça ativo para refaturamento. Manter a venda, o histórico e os XP pela `data_emissao` original do pedido. Ao refaturar, substituir a evidência fiscal estornada pela nota válida, sem criar outra compra, outra competência ou outro crédito. Se o cliente estiver bloqueado por inadimplência, remover a parcela da nota estornada do faturamento válido; até o refaturamento, somente outras parcelas efetivamente faturadas podem participar.

**Situação atual confirmada pelo usuário em 14/09/2026:** não congelar a apuração depois de um fechamento. A cada atualização, reconstruir o resultado com os estados mais recentes de pedidos, notas, devoluções e inadimplência. Aplicar o efeito na competência original e recalcular os eventos e XP dependentes. Fotografias anteriores podem ser preservadas para auditoria, com data/hora e versão das regras, mas o resultado oficial exibido é sempre o mais recente.

| Situação | Efeito da regra confirmada |
| --- | --- |
| Pedido cancelado | Excluir integralmente do realizado, do histórico elegível e dos XP; preservar somente para auditoria e recalcular os efeitos posteriores |
| Bonificação, remessa ou transferência de mercadoria | Excluir do realizado, do histórico elegível e de todos os XP |
| Nota fiscal estornada, pedido ainda ativo | Manter o pedido como venda válida pela implantação original; substituir a evidência fiscal quando houver refaturamento, sem duplicar a venda |
| Devolução parcial | Abater somente o valor devolvido da região e da competência original do pedido; manter o saldo líquido elegível |
| Devolução total | Zerar o valor elegível do pedido original e reavaliar seus eventos e o histórico posterior |
| Cliente bloqueado por inadimplência e pedido sem faturamento | Não considerar o pedido no realizado nem nos créditos de XP dele derivados |
| Cliente bloqueado por inadimplência e pedido integralmente faturado | Considerar a parte faturada, que corresponde ao pedido integralmente faturado; aplicar as demais condições de elegibilidade |
| Cliente bloqueado por inadimplência e pedido parcialmente faturado | Considerar somente o valor e os itens/quantidades já faturados; o saldo em aberto não participa |
| SMART PODS ou MRV, mesmo com inadimplência | Exceção ao bloqueio por inadimplência; considerar o pedido pelas regras gerais, sem exigir faturamento por esse motivo |
| Cliente quita a dívida durante a campanha | Retirar o bloqueio financeiro dos pedidos em aberto e reintegrá-los pela data original de implantação; recalcular os resultados afetados |
| Cliente sem inadimplência identificada em uma fonte válida e completa | A regra de inadimplência não impede a consideração; aplicar as demais condições |
| Informação de inadimplência ou faturamento insuficiente para decidir | Manter a elegibilidade pendente, sem tratar dado ausente como autorização |

A exceção de faturamento afasta apenas a exclusão por inadimplência. Ela não restabelece um pedido cancelado, mesmo que já tenha sido faturado, nem dispensa outras condições da campanha.

Para o histórico, “não considerar” significa que um pedido bloqueado e totalmente em aberto não impede um pedido posterior de ser classificado como primeira compra ou retorno após inatividade. Uma parcela faturada válida já constitui compra anterior dos itens correspondentes. Para mix, somente linhas e quantidades faturadas participam e precisam cumprir o mínimo aplicável. Quando a quitação reintegrar a parte em aberto, recalcular cronologicamente pela implantação original, pois a primeira compra ou a última compra anterior pode mudar.

## Valor elegível e faturamento parcial

Após validar os demais critérios, a apuração usa:

- Pedido cancelado: registro inelegível por inteiro, com valor zero e sem presença no histórico de compras; recalcular os XP e as classificações posteriores afetadas.
- Cliente bloqueado por inadimplência: somente o valor bruto efetivamente faturado e válido até a referência.
- Cliente não bloqueado, incluindo SMART PODS e MRV: valor bruto do pedido elegível, pela data de implantação.

A situação financeira é reavaliada conforme o estado atual disponível. Enquanto o grupo está bloqueado, somente a parte faturada entra. Após a quitação, o saldo em aberto elegível volta a participar; o total do pedido passa a seguir a regra normal desde sua competência original. Exemplo: pedido de R$ 10.000 implantado em setembro, com R$ 4.000 faturados enquanto o grupo estava inadimplente, contabiliza R$ 4.000. Se o grupo quitar a dívida em outubro, os R$ 6.000 restantes retornam ao realizado de setembro, que passa a R$ 10.000, e os XP de setembro são recalculados.

O valor faturado substitui o valor total do pedido no caso bloqueado; não somar os dois valores. Exemplo: pedido de R$ 10.000, com R$ 4.000 faturados, gera R$ 4.000 de realizado elegível e deixa R$ 6.000 fora. Em uma triangulação entre duas regiões, cada região recebe R$ 2.000 dos R$ 4.000 faturados. As parcelas já divididas na fonte não são divididas novamente. Para SMART PODS e MRV, esse mesmo pedido pode contar R$ 10.000, observadas as demais condições.

Para os XP derivados do pedido bloqueado, avaliar somente os itens e quantidades faturados. No mix, a parcela elegível faturada da linha deve satisfazer seu mínimo no próprio pedido, somando as alocações completas antes do rateio de XP. Uma nota de outra linha não libera produtos ainda não faturados. Manter o crédito por evento, sem conceder novamente por novas notas ou versões da apuração. O adiantamento segue sua confirmação manual.

**Mapeamento técnico proposto após leitura do código:** usar `comercial_marts.fct_faturamento_item.valor_bruto_item` para a parcela bruta faturada. Esse fato, também usado no Gestão Comercial, já divide os valores por dois em triangulações e identifica cada alocação por `faturamento_item_id` e `vendedor_metricas_id`. Consolidar notas válidas até a referência por pedido/produto/alocação antes de relacioná-las à implantação e à região. O vínculo deve incluir filial e preservar cliente/loja; produtos repetidos em vários itens exigem conferência de correspondência para não multiplicar valores.

Não inferir o faturamento integral pelo status `faturado`. Também não tratar automaticamente `valor_bruto_total - valor_bruto_nao_faturado` como valor comprovado de notas: o saldo aberto do código é estimado a partir de quantidades do pedido. Conferir faturamento efetivo e eventuais diferenças de composição de valor na integração.

## Devoluções

Calcular `valor_liquido_elegivel = valor_bruto_elegivel - devolucoes_vinculadas`, sem permitir valor abaixo de zero. A população inclui todas as devoluções encontradas, sem filtrar por `setor_responsavel`, motivo, submotivo, tipo ou classificação. Esses atributos podem ser exibidos para auditoria, mas não decidem a dedução da campanha. Somar várias devoluções da mesma nota/pedido antes do abatimento e sinalizar qualquer valor devolvido superior à venda elegível. Em triangulações, usar `valor_devolucao_alocado`, já distribuído entre os participantes da nota original, e atribuir cada parcela à região do respectivo vendedor. Não dividir novamente nem abater o valor integral em cada região.

Exemplo: pedido de R$ 10.000 implantado em setembro e dividido igualmente entre duas regiões recebe devolução parcial de R$ 4.000 em outubro. O realizado de setembro é recalculado para R$ 6.000: R$ 3.000 em cada região. Outubro não recebe uma venda negativa por essa devolução.

Recalcular os indicadores derivados do pedido:

- Vendas: atualizar realizado, atingimento e faixa regional de XP da competência original.
- Clientes novos e reativados: manter o evento se restar uma compra elegível; em devolução total do pedido, remover o evento e reavaliar qual compra passa a ser a primeira ou a última anterior.
- Mix: usar o valor líquido elegível da linha. Se a devolução reduzir a primeira compra abaixo do mínimo, retirar os 10 XP dessa expansão e recalcular o histórico posterior da linha.
- Tetos: consolidar novamente os eventos por vendedor/regra depois dos ajustes. O adiantamento manual não é alterado automaticamente.

**Mapeamento técnico identificado em 14/09/2026:** `comercial_marts.fct_nota_devolucao` expõe `data_devolucao`, `nota_fiscal_original_id`, `nota_fiscal_devolucao_id`, `valor_devolucao`, `valor_devolucao_alocado`, `tipo_alocacao_comercial` e `vendedor_metricas_id`. O dataflow associa a devolução às alocações de `fct_faturamento_item` pela nota original e divide o valor pela quantidade de alocações. Para encontrar a competência original, relacionar a nota a `fct_faturamento_item` para obter o pedido e, depois, ao pedido implantado por filial/pedido para obter `data_emissao`.

A fonte de devolução observada contém valor no nível da nota, sem produto ou item. Isso é suficiente para o abatimento regional total, mas não identifica diretamente qual linha de mix foi devolvida quando a nota original contém vários produtos. No mix, reavaliar somente o evento que contenha o pedido associado à nota fiscal devolvida; devoluções de outros pedidos do mesmo grupo comercial não interferem. Enquanto faltar o produto devolvido, manter apenas esse evento como pendente, sem ratear arbitrariamente o valor entre linhas.

## Recálculo após cancelamento

- Retirar o pedido inteiro da base elegível, como se nunca tivesse sido uma venda válida. Manter seus dados apenas na trilha de auditoria com o motivo `cancelado`/`excluido`.
- Atualizar o realizado da região e da competência de implantação do pedido. Em triangulações, retirar todas as parcelas regionais correspondentes, sem estornar o valor integral em cada região nem dividi-lo novamente.
- Recalcular o atingimento e sua faixa de XP regional. O ajuste de XP não é uma subtração fixa proporcional ao valor cancelado.
- Remover o pedido da sequência histórica usada para novos, reativados e mix. Reavaliar os créditos e pedidos posteriores que dependiam dessa compra, consolidar novamente as parcelas e aplicar os tetos individuais; preservar os motivos e os valores para conferência.
- Fazer o mesmo quando uma quitação reintegrar pedidos anteriormente bloqueados: restaurar a parte em aberto pela implantação original e reavaliar os eventos e pedidos posteriores afetados.
- Nas devoluções, retirar somente o valor devolvido da competência original e reavaliar o saldo do pedido, os eventos e a sequência histórica. Uma devolução total pode mudar a primeira compra ou a última compra anterior de pedidos posteriores.
- O adiantamento permanece baseado nos checks manuais das cinco contas editoras autorizadas. O recálculo de vendas não altera esses checks automaticamente.
- As confirmações cobrem cancelamentos, quitações, todas as devoluções, a exclusão de bonificações/remessas/transferências de mercadoria, o estorno de nota com pedido ativo e correções após fechamentos anteriores. A apuração corrente sempre é recalculada pela situação atual.

## Evidências encontradas no código local

Conferência somente leitura em 14/09/2026. As definições abaixo foram lidas no código dos projetos vizinhos; não foi consultado o estado atual do Supabase nem aplicada uma migração nesta etapa.

| Origem | Evidência e limite de uso |
| --- | --- |
| [fct_pedido_item.sql](../../../dataflow/models/marts/comercial/fct_pedido_item.sql) | `status_item_pedido = 'excluido'` quando há exclusão lógica do pedido ou item. `is_item_valido_metricas` rejeita exclusões e bloqueios. O texto `cancelado` não aparece como um status próprio desse fato; conferir a representação do cancelamento na origem |
| Mesmo fato | `status_item_pedido = 'faturado'` é derivado da presença de `nota_fiscal_id` no item, depois de verificar exclusão e bloqueio. Não comprova faturamento integral de todos os itens do pedido |
| Mesmo fato | O código expõe `quantidade_faturada`, `quantidade_vendida`, `quantidade_nao_faturada` e `valor_bruto_nao_faturado`. A disponibilidade e a compatibilidade dessas medidas, inclusive seu grão e rateio, devem ser validadas antes de calcular uma parcela faturada |
| [fct_faturamento_item.sql](../../../dataflow/models/marts/comercial/fct_faturamento_item.sql) e [preparação no Gestão Comercial](../../../gestao_comercial/Gestao_Comercial/modulos_app/20_dataflow.py) | O Gestão Comercial usa `valor_bruto_item` desse fato como valor bruto faturado. O fato preserva pedido, produto, nota, data e alocação; `valor_bruto_item` e `quantidade_faturada` já são ajustados em triangulações |
| [int_venda_valor_bruto.sql](../../../dataflow/models/intermediate/comercial/int_venda_valor_bruto.sql) | `valor_bruto_nao_faturado` é proporcional à diferença entre quantidade vendida e entregue no pedido. O fato de pedidos também associa uma quantidade de nota sem o mesmo ajuste das quantidades comerciais; não misturar medidas de grãos/rateios distintos |
| [vw_pedidos_venda_faturados.sql](../../../dataflow/models/marts/comercial/vw_pedidos_venda_faturados.sql) | Consolida faturamento por nota, pedido e produto desde 2026, com referência nos itens de nota. É uma possível evidência complementar; a associação ao fato deve evitar repetição por notas e alocações |
| [vw_clientes_inadimplentes.sql](../../../dataflow/models/marts/comercial/vw_clientes_inadimplentes.sql) | Retorna `cliente_loja_id` e `situacao = 'Vencido'`; propaga a inadimplência ao grupo comercial e exclui SMART PODS e MRV do conjunto de bloqueados |
| [vw_inadimplencia.sql](../../../dataflow/models/marts/comercial/vw_inadimplencia.sql) | Título em aberto com vencimento anterior a `current_date` é classificado como `Vencido`. A situação atual é adequada à regra confirmada de bloqueio e liberação após quitação; a view não permite reconstruir sozinha como o painel aparecia em datas anteriores |
| [Gestão Comercial: inadimplência](../../../gestao_comercial/Gestao_Comercial/README.md) e [view de clientes](../../../gestao_comercial/Gestao_Comercial/sql/vw_clientes_inadimplentes.sql) | Documentam o bloqueio por grupo e as exceções SMART PODS/MRV; clientes sem grupo são tratados pela própria combinação cliente/loja nessa regra de bloqueio |
| [fct_nota_devolucao.sql](../../../dataflow/models/marts/comercial/fct_nota_devolucao.sql) | Relaciona a nota devolvida à nota original, herda as alocações comerciais do faturamento e calcula `valor_devolucao_alocado`. Não expõe filial, pedido, produto ou item na saída observada |
| [preparação de devoluções no Gestão Comercial](../../../gestao_comercial/Gestao_Comercial/modulos_app/20_dataflow.py) | Usa `valor_devolucao_alocado` e consolida papéis comerciais repetidos quando pertencem ao mesmo vendedor, preservando a soma |
| [performance mensal do Gestão Comercial](../../../gestao_comercial/Gestao_Comercial/modulos_app/40_performance_mes.py) | Possui um filtro de devoluções com setor responsável `COMERCIAL` para um indicador daquele painel. Esse filtro não se aplica à Campanha Polar: por decisão confirmada, a campanha abate todas as devoluções |

O uso de cliente/loja no bloqueio financeiro da fonte não muda a regra já confirmada para novos, reativados e mix: grupo comercial pendente continua aguardando correção cadastral.

## Definições necessárias à implementação

O bloqueio por grupo, as exceções SMART PODS/MRV, o uso exclusivo da parte faturada, seu efeito no histórico e a reintegração pela data original após quitação estão confirmados. Restam:

1. Conferir a representação do cancelamento na origem e o vínculo das evidências de faturamento ao pedido. Não usar status de uma tela de solicitações de implantação como se fosse o status do pedido comercial.
2. Identificar uma fonte de devolução por produto/item, ou definir como atribuir devoluções de notas com vários produtos, para recalcular mínimos e histórico de cada linha de mix sem rateio arbitrário.
3. Validar tecnicamente a reconstrução completa e o versionamento das fotografias após correções retroativas. A regra de negócio já está confirmada: o resultado corrente não fica congelado.

As prévias SQL existentes de novos, reativados e mix não incorporam ainda o filtro de inadimplência. Seus resultados salvos continuam sendo diagnósticos históricos, sem concessão de XP. A integração depende das definições acima e da validação das fontes.
