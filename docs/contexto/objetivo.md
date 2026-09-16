# Objetivo do painel

**Confirmado pelo usuário:** desenvolver um painel em Streamlit para visualizar o atingimento da campanha XP Polar. A implementação contém visão geral, análise individual por região, Venda no Quadrimestre, adiantamento e páginas de clientes novos, clientes reativados e mix de produtos para toda a campanha.

## Público e decisões

- Acesso já definido e ampliado em 16/09/2026: usuários válidos cadastrados no Supabase Authentication podem consultar as telas; `lais.vendrasco@ambar.tech`, `leonardo.watanabe@ambar.tech`, `jorge.castro@ambar.tech`, `anyelle.santos@ambar.tech` e `luis.oliveira@ambar.tech` podem preencher e salvar o adiantamento.
- Qual decisão o painel deve ajudar a tomar: **confirmado pelo usuário em 14/09/2026**, acompanhar se as vendas de cada região estão no ritmo necessário para atingir sua meta mensal, considerando os dias úteis decorridos e restantes.
- Visibilidade já definida: a tabela de adiantamento mostra todas as regiões aos usuários autenticados. Acompanhamento de vendas e XP deve preservar o resumo por região; restrições adicionais por usuário ainda não foram solicitadas.

## Perguntas que o painel precisa responder

Marque as necessárias e acrescente outras.

- [x] Quanto a região vendeu no mês e quanto falta para sua meta mensal?
- [x] Quantos dias úteis restam até o fim do mês?
- [x] Qual é a meta planejada de vendas por dia útil?
- [x] Quanto a região deveria ter vendido no quadrimestre até hoje e qual é seu atingimento acumulado?
- [x] Quantos XP de vendas são calculados pelo atingimento acumulado da região?
- [x] Quantos XP tenho em cada indicador?
- [x] Em qual nível estou?
- [ ] Qual é meu prêmio estimado conforme o Budget da empresa?
- [x] Como está o ranking das regiões participantes?
- [ ] Quais clientes e vendas geraram meus pontos?
- [x] Quais fases de adiantamento foram confirmadas para cada região no mês?
- [ ] Como meu resultado evoluiu durante a campanha?
- Regra histórica confirmada em 14/09/2026: pedidos bloqueados e não faturados são ignorados no histórico que determina cliente novo, reativado e primeira compra de mix. Somente a parte faturada entra; após quitação, a parte liberada retorna pela data original e pode reclassificar eventos posteriores.

## Visualizações e filtros

- Visão geral simplificada, **confirmada pelo usuário em 16/09/2026**: mostrar um cartão visual de atingimento do budget anual de vendas de R$ 119 milhões e uma tabela regional com XP de clientes novos, clientes reativados, expansão de mix, atingimento de meta, adiantamento, XP total e classificação. Ordenar as regiões pelo XP total decrescente, com desempate alfabético.
- Budget anual ajustado em 16/09/2026: a inadimplência não reduz o realizado anual. O indicador usa os pedidos comerciais válidos de 2026 pelo valor bruto, desconta as devoluções e preserva as exclusões de bonificações, remessas, transferências e itens inválidos para métricas.
- Análise individual solicitada em 16/09/2026: selecionar uma região e mostrar XP total, classificação e a composição pelos cinco indicadores em barras horizontais, sem exibir ranking nessa tela. Disponibilizar, na mesma página, o detalhamento dos clientes novos, clientes reativados, compras de mix, venda contra meta e checks mensais de adiantamento da região.
- Gráficos ou tabelas desejados: proposta de comparação do realizado acumulado com a meta parcial por dia útil, acompanhada de tabela por data para conferência. O formato visual definitivo permanece a definir.
- Tabela de adiantamento atualizada em 16/09/2026: uma linha por região e 12 checks, com as três fases de setembro, outubro, novembro e dezembro lado a lado. As cinco contas editoras autorizadas podem preencher e salvar; os demais usuários autenticados visualizam.
- Visão de clientes novos solicitada e implementada em 15/09/2026: resumo regional com quantidade, lista de clientes e XP; abaixo, filtro de região e detalhe por vendedor. Exibe 10 XP em uma atribuição integral ou duas linhas de 5 XP quando houver dois vendedores, antes do teto individual acumulado de 100 XP.
- Visão de clientes reativados implementada em 15/09/2026: resumo de quantidade, lista e XP por região, seguido de filtro regional e detalhe por vendedor. Mostra a última compra, o retorno, o prazo de 6 ou 12 meses e 8 XP por evento confirmado, divididos em duas linhas de 4 XP quando houver dois vendedores.
- Visão de mix de produtos implementada em 15/09/2026: resumo regional das expansões confirmadas, seguido de filtro regional e detalhe por vendedor. Mostra família, produtos, mínimo, exclusão de KA e 10 XP por expansão, divididos em duas linhas de 5 XP quando houver dois vendedores. Eventos afetados por devolução sem detalhe de produto permanecem pendentes.
- Visão de Venda no Quadrimestre implementada em 15/09/2026 e ajustada após confirmação do usuário: acumula os meses desde setembro. Meses encerrados entram com meta e vendas integrais; o mês atual entra com vendas até a referência e meta proporcional aos dias úteis. Mostra atingimento exato e XP por região, com dias úteis em um indicador no topo. A tabela omite metas publicadas e a meta integral do mês atual. Os vendedores aparecem para identificar a composição das vendas, sem dividir ou duplicar o XP regional.
- XP de adiantamento, confirmado pelo usuário em 14/09/2026: vinculado à região, com 10 XP por fase confirmada, até 30 XP no mês e 120 XP na campanha. Dois vendedores na região não dividem nem duplicam os pontos. O painel calcula o total mensal a partir dos checks salvos e o integra ao XP total da região na Visão geral e na Análise individual.
- Navegação: o filtro global de competência foi removido em 15/09/2026. As telas abrangem a campanha inteira e identificam a competência nas tabelas. A Análise individual filtra uma região por vez; outros filtros permanecem vinculados à necessidade de cada visão.
- Vínculo vendedor–região: **confirmado pelo usuário em 14/09/2026**, os vendedores não mudarão de região durante a campanha. Usar a região cadastrada para todas as competências, mantendo uma única meta e pontuação regional mesmo quando houver dois vendedores.
- Data dos pedidos: **confirmada pelo usuário em 14/09/2026**, emissão = implantação. Usar `data_emissao` para determinar o mês da venda e o realizado acumulado até a referência, observadas as condições de elegibilidade.
- Valor do realizado: **confirmado pelo usuário em 14/09/2026**, comparar o valor bruto dos pedidos com a meta regional, usando `valor_bruto_total` como referência na fonte de vendas.
- Rateio monetário: **confirmado pelo usuário em 14/09/2026**, seguir o dataflow e o Gestão Comercial. Nas triangulações, cada parcela compõe o realizado da região de seu vendedor. Usar os valores já divididos da fonte; se ambos os vendedores forem da mesma região, reunir as duas parcelas nela, mantendo sua meta integral.
- Elegibilidade, **confirmada em 14/09/2026**: tratar pedidos cancelados como integralmente excluídos e inválidos para vendas. Retirá-los do realizado, do histórico de compras elegíveis e de todos os XP e recalcular os eventos posteriores afetados. Aplicar o bloqueio por inadimplência do grupo, com exceções SMART PODS/MRV; para os demais bloqueados, somente a parte faturada entra no realizado. Mostrar o valor elegível e o motivo de exclusão para conferência.
- Quitação durante a campanha, **confirmada em 14/09/2026**: reintegrar os pedidos em aberto pela data original de implantação, inclusive em competência anterior, e recalcular realizado e XP. Não transferir a venda para o mês da quitação.
- Devoluções, **confirmadas em 14/09/2026**: considerar todas, independentemente do setor responsável, motivo, submotivo, tipo ou classificação. Abater somente o valor devolvido da competência original de implantação e recalcular os XP afetados. Exibir o valor bruto, o devolvido e o líquido; a data e as classificações da devolução ficam disponíveis para auditoria.
- Operações não comerciais, **confirmadas em 14/09/2026**: excluir bonificações, remessas e transferências de mercadoria do realizado, do histórico de compras elegíveis e de todos os XP. Exibir a classificação e o CFOP para conferência dos registros excluídos.
- Estorno de nota fiscal, **confirmado em 14/09/2026**: manter o pedido ativo como venda válida pela implantação original. Um refaturamento troca a evidência fiscal sem gerar nova venda, nova competência ou novo XP. Para inadimplentes bloqueados, exibir e considerar somente as parcelas cobertas por notas válidas na data de referência.
- Atualização do resultado, **confirmada em 14/09/2026**: calcular sempre pela situação atual das fontes. Mudanças retroativas atualizam a competência original e recalculam histórico, enquadramentos e XP, mesmo depois de um fechamento anterior. Guardar fotografias para auditoria sem tratá-las como resultado congelado.
- Adiantamento, **confirmado em 14/09/2026**: receber de Laís ou Leonardo três checks `true`/`false` por região e mês. Usar diretamente a versão salva, sem calcular datas de encerramento, conferir percentuais contra vendas ou inferir uma fase a partir de outra.
- Participantes, **confirmados em 14/09/2026**: exibir e apurar somente regiões de Canais e Construção com meta positiva na competência. Relacionar os vendedores dessas regiões aos indicadores individuais; não criar participantes a partir do cadastro de vendedores quando não houver meta válida.
- Admitidos e desligados, **confirmados em 14/09/2026**: manter no painel os resultados das vendas elegíveis de cada vendedor durante sua participação. Aplicar regras e tetos integrais, sem proporcionalidade pelos meses disponíveis, e preservar o histórico após o desligamento.
- Classificação KA, **confirmada em 14/09/2026**: usar a mesma lista de 16 grupos em todas as competências. Não aplicar mudanças de entrada ou saída durante a campanha; sinalizar divergências cadastrais para correção.
- Pedidos no mesmo dia, **confirmados em 14/09/2026**: consolidar os pedidos elegíveis do mesmo grupo comercial e da mesma data em um único evento. Somar os valores por linha de mix e manter os pedidos originais visíveis para auditoria, sem duplicar XP de novo ou reativado.
- Para vendas, acumular desde setembro até a referência: usar meta e realizado integrais dos meses encerrados e somar a meta parcial e o realizado do mês atual. Calcular os XP atuais sobre esse atingimento acumulado, sem somar os XP calculados em cada mês. Identificar o mês e a data de referência; os tetos de novos e reativados continuam no acumulado da campanha por vendedor, e o teto de antecipação no acumulado por região.
- Precisará exportar os dados? Em qual formato: [PREENCHER]
- Há algum painel de referência: [PREENCHER]

## Critérios para considerar a primeira versão pronta

1. Calcular a meta parcial e os XP de vendas por região com o calendário de segunda a sexta, descontando feriados nacionais, usando o percentual exato e uma única meta regional mesmo com dois vendedores no mês.
2. Mostrar o realizado do mês, a meta parcial, os dias úteis restantes e a meta diária, mesmo sem metas cadastradas para meses futuros.
3. Permitir conferir o realizado e seus rateios contra os dados do dataflow/Gestão Comercial, mostrando cancelamento, bloqueio por inadimplência, parte faturada e motivo de pendência sem duplicar itens, notas ou alocações.

- Proposta para uma segunda versão: ranking, evolução histórica, estimativa de prêmio conforme o atingimento do Budget, exportações e detalhamento por gestor.

**Disponibilidade confirmada em 14/09/2026:** em setembro, comparar com a meta de setembro; a meta de outubro só será conhecida em outubro. As fórmulas, o tratamento de dados ausentes e o exemplo estão em [Dados de metas](../dados/dadoMeta.md), com o [calendário de referência](../dados/calendarioCampanha.md).
