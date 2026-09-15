# Contexto da Polar

## Empresa e operação comercial

- Escopo conhecido da operação: pedidos comerciais de produtos atendidos pelos times Construção e Canais. Para a campanha, há regras específicas para Hydrofix, CPP 009, kits Grelha + Porta Grelha e Suporte de Bancada. A descrição completa do portfólio e do fluxo comercial não é necessária para calcular as regras já confirmadas.
- Segmento Construção: reúne Time Norte e Time Sul, conforme confirmado pelo usuário.
- Segmento Canais: corresponde ao time Canais, conforme confirmado pelo usuário.

O mapeamento está em [timesSegmentos.csv](../dados/timesSegmentos.csv). Times ausentes ou diferentes desses três permanecem pendentes de classificação; não inferir segmento pelo nome do cliente ou da região.
- Regiões comerciais: **confirmado pelo usuário em 14/09/2026**, normalmente há um vendedor por região, mas podem aparecer dois no mesmo mês. A meta e o atingimento de vendas devem ser considerados por região, mantendo uma única meta regional integral nesse caso.

## Participantes e responsabilidades

- Quem participa da campanha: **confirmado pelo usuário em 14/09/2026**, regiões dos segmentos Canais e Construção que possuam meta válida cadastrada na competência. Os vendedores vinculados a essas regiões participam dos indicadores individuais conforme as demais regras.
- Quem fica fora da campanha: regiões sem meta válida na competência e regiões de outros segmentos. Metas ausentes ou zeradas não são estimadas; a região passa a participar quando uma meta positiva for publicada, e a apuração é atualizada pela situação corrente.
- Admitidos e desligados: participam normalmente pelas vendas elegíveis que lhes forem atribuídas. Não há proporcionalidade de pontos ou tetos pelo número de meses; o desligamento não apaga os XP históricos.
- Como vendedores, representantes e gestores se relacionam: as vendas usam `vendedor_metricas_id`; triangulações possuem alocações de representante e executivo, com metade do valor e dos XP de eventos para cada participante. Quando pedidos distintos do mesmo grupo e data formarem um evento diário com dois vendedores identificados, dividir somente os XP do evento em 50% para cada um e manter os valores monetários nos pedidos e alocações originais. Gestores e demais relações hierárquicas ainda precisam de definição se forem usados como filtros.
- Quem valida os dados e resolve divergências: Laís Vendrasco e Leonardo Watanabe podem registrar e corrigir o adiantamento manual. Responsáveis pelas divergências das fontes e pelo fechamento final ainda precisam ser informados.
- Quem aprova o resultado final: [PREENCHER]

## Termos usados pela empresa

| Termo | Significado na operação |
| --- | --- |
| Data de emissão / implantação do pedido | São a mesma data, conforme confirmado pelo usuário em 14/09/2026. O campo `data_emissao` determina a data do pedido para apuração da campanha |
| KA / Key Account | Grupo comercial presente na lista fixa de 16 grupos fornecida para toda a campanha. Não haverá mudança de classificação entre setembro e dezembro. A condição exclui somente o XP de expansão de mix |
| Carteira de clientes | Pedidos implantados ainda em aberto/não faturados. Para grupo bloqueado por inadimplência, essa parte fica fora até a quitação; SMART PODS e MRV são exceções |
| Devolução | Valor devolvido que reduz a venda na competência original de implantação do pedido. Todas as devoluções são consideradas, sem filtro por setor responsável, motivo, tipo ou classificação. Devolução parcial abate apenas sua parcela; a apuração e os XP afetados são recalculados |
| Operação não comercial | Bonificação, remessa ou transferência de mercadoria. Fica fora do realizado, do histórico de compras elegíveis e de todos os XP. A transferência aqui é uma classificação da operação, sem relação com mudança de região do vendedor |
| Pedido cancelado | Pedido integralmente excluído da base elegível, como se nunca tivesse sido uma venda válida. Fica fora do realizado, do histórico de compras e de todos os XP; permanece visível somente para auditoria |
| Estorno de nota fiscal | Anulação de uma nota sem cancelamento do pedido. Se o pedido permanecer ativo para refaturamento, a venda continua válida pela implantação original; o refaturamento substitui a evidência fiscal sem criar nova venda ou XP |
| Situação atual | Estado mais recente disponível de pedidos, notas, devoluções e inadimplência. É a base do resultado oficial, que continua sendo recalculado mesmo depois de fotografias ou fechamentos anteriores |
| Evento diário de compra | Consolidação de todos os pedidos elegíveis do mesmo grupo comercial na mesma data. Gera uma única avaliação de novo ou reativado e soma os valores por linha para o mínimo de mix |
| Cliente novo | Grupo comercial sem compra anterior na empresa no histórico aceito desde janeiro de 2022; não reinicia por vendedor, região, segmento, CNPJ ou loja |
| Mix | Uma das quatro linhas da campanha: Hydrofix, CPP 009, Grelha + Porta Grelha ou Suporte de Bancada. Os 23 códigos estão mapeados em `produtosMix.csv` |
| Antecipação / adiantamento | Indicador com três checks manuais `true`/`false` por região e mês para as referências de 32%, 56% e 80%. O usuário autorizado decide o atingimento; o sistema não calcula prazos ou percentuais. XP regional: 10 por fase marcada, até 30 no mês e 120 na campanha |
| Budget Anual | Atingimento anual da empresa que condiciona o pagamento dos prêmios conforme o regulamento; fonte e cálculo do percentual ainda precisam ser definidos |

## Materiais complementares

- Regulamento disponível: [RegrasPolar.pdf](RegrasPolar.pdf).
- Regulamento da campanha e antecipação: [RegrasPolar.pdf](RegrasPolar.pdf), complementado pelas confirmações registradas em [Regras da campanha](../regras/regrasCampanha.md).
- Materiais operacionais consultados: modelos locais do dataflow e do Gestão Comercial, usados para mapear pedidos, faturamento, metas, triangulações e inadimplência. As regras confirmadas prevalecem sobre interpretações técnicas das fontes.
