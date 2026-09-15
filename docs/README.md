# Documentação para preparar o painel XP Polar

Estes arquivos são roteiros para você descrever a campanha e as bases antes de desenvolver o painel em Streamlit.

**Implementação atualizada em 15/09/2026:** o painel disponível em [app.py](../app.py) contém visão geral, clientes novos, clientes reativados, mix de produtos e preenchimento manual de adiantamento. Todos os usuários autenticados consultam; somente `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech` alteram o adiantamento. O acesso usa Supabase Auth e Data API, sem senha PostgreSQL no Streamlit. Instruções no [README do projeto](../README.md).

## Como preencher

- Substitua `[PREENCHER]` pelas suas respostas. Pode escrever em linguagem simples.
- Se algo ainda não estiver definido, escreva `A definir` e, se possível, quem poderá esclarecer.
- Os trechos marcados **Conforme PDF** foram extraídos de [RegrasPolar.pdf](contexto/RegrasPolar.pdf).
- Os trechos marcados **Confirmado pelo usuário** já foram esclarecidos nesta conversa.
- As perguntas e tabelas de campos são roteiros: não exigem alterar suas planilhas atuais.
- Nas descrições de dados, use os nomes reais das colunas e inclua de 3 a 5 linhas fictícias ou anonimizadas.

## Ordem sugerida

| Ordem | Arquivo | O que explicar |
| --- | --- | --- |
| 1 | [Contexto da Polar](contexto/contextoPolar.md) | Empresa, equipes, participantes e termos usados |
| 2 | [Objetivo do painel](contexto/objetivo.md) | Quem usará, perguntas que o painel deve responder e visualizações |
| 3 | [Regras da campanha](regras/regrasCampanha.md) | Período, XP, níveis, prêmios e pontos pendentes do regulamento |
| 4 | [Regras de negócio](regras/regraNegocio.md) | Como interpretar vendas, clientes, mix e exceções na prática |
| 5 | [Dados de vendas](dados/dadoVenda.md) | Origem, colunas e exemplos da base de vendas |
| 6 | [Dados de metas](dados/dadoMeta.md) | Meta e atingimento por região, dias úteis, XP de vendas e vínculo fixo dos vendedores |
| 7 | [Dados de antecipação](dados/dadoAdiantamento.md) | Fases, datas, percentuais e resultados da antecipação |
| 8 | [Dados de clientes](dados/dadoCliente.md) | Histórico de compras, segmento, KA e produtos já comprados |
| 9 | [Dados do Budget](dados/dadoBudget.md) | Meta anual e realizado da empresa para validar os prêmios |
| 10 | [Estrutura e operação](arquitetura/estrutura.md) | Entrada dos dados, atualização, acesso e identidade visual |
| 11 | [Enquadramento dos pedidos](dados/dadoEnquadramento.md) | Proposta de tabela derivada para clientes novos, reativados e mix |
| 12 | [Grupos KA](dados/dadoKA.md) | Lista fornecida pelo usuário, códigos do Supabase e exclusão do mix |
| 13 | [Prévia de mix com pedidos reais](dados/previaMix.md) | Consulta somente leitura e resultado após conferir o segmento e o mínimo |
| 14 | [Prévia de novos e reativados](dados/previaClientes.md) | Histórico de 323 pedidos, candidatos e pendências de grupo/segmento |
| 15 | [Calendário da campanha](dados/calendarioCampanha.md) | Dias úteis de segunda a sexta, feriados nacionais e data de referência |
| 16 | [Elegibilidade de vendas](dados/elegibilidadeVendas.md) | Cancelamentos, inadimplência por grupo, exceções SMART PODS/MRV e parte faturada |
| 17 | [Visão de clientes novos](dados/visaoClientesNovos.md) | Página, filtros, consulta autenticada, XP bruto e limites atuais |
| 18 | [Visão de clientes reativados](dados/visaoClientesReativados.md) | Retorno após inatividade, última compra, atribuição e XP bruto |
| 19 | [Visão de mix de produtos](dados/visaoMixProdutos.md) | Primeira compra da família, mínimos, KA, pendências e XP |

Clientes e Budget podem estar nas mesmas fontes de vendas e metas. Se for o caso, basta indicar isso nos respectivos documentos; não é necessário criar novas bases.

## Pendências centrais

- Corrigir o cadastro dos clientes com grupo comercial pendente: a [prévia de clientes](dados/previaClientes.md) encontrou 75 pedidos sem grupo e 1 com código `00` sem correspondência no cadastro. O tratamento foi confirmado pelo usuário em 14/09/2026: aguardar a correção, sem avaliar esses clientes individualmente em substituição ao grupo. Também restam 3 pedidos com segmento pendente.
- Confirmar a data operacional da apuração final; o período do PDF e do recorte atual vai de 01/09/2026 a 31/12/2026.
- Configurar os dois secrets públicos do Supabase e aplicar os SQLs das páginas de adiantamento, clientes novos, clientes reativados e mix. As três fases mensais, as duas contas autorizadas e os XP por região já foram definidos: cada check `true` vale 10 XP, até 30 XP por mês e 120 XP na campanha. Não é necessário definir datas exatas das semanas nem validar os percentuais pelas vendas; a integração do XP ao total completo da campanha está descrita em [Dados de adiantamento](dados/dadoAdiantamento.md).
- Definir o tratamento de atendimentos compartilhados com responsáveis incompletos ou com quantidade diferente de dois vendedores. Para um evento diário consolidado com exatamente dois vendedores identificados, o rateio já foi confirmado em 50% dos XP para cada um, mesmo quando os vendedores vierem de pedidos distintos do mesmo grupo e data. Pedidos com um vendedor atribuem 100% a ele. O histórico desde janeiro de 2022, os códigos de mix, os mínimos por evento diário e a lista KA também já foram definidos.
- Validar o vínculo das notas faturadas e devolvidas aos pedidos e a representação dos cancelamentos e estornos na fonte. Cancelamentos, inadimplência, quitação, abatimento de todas as devoluções na competência original, exclusão de bonificações/remessas/transferências de mercadoria, estorno de nota com pedido ativo e recálculo após fechamentos anteriores já foram confirmados. Para recalcular mix, ainda é necessária uma fonte de devolução por produto/item. Fontes e limites em [Elegibilidade de vendas](dados/elegibilidadeVendas.md).
- Acompanhar o cadastro das metas quando cada competência estiver disponível. O usuário confirmou que a meta de outubro só será conhecida em outubro; a ausência de metas futuras não impede o acompanhamento de setembro. Conferir as quatro metas no fechamento do quadrimestre.

**Já confirmado:** expansão de mix contempla clientes novos e existentes que comprem produto novo. A exclusão de KA consta no PDF.

**Titularidade do XP de vendas, confirmada em 14/09/2026:** o XP do atingimento fica registrado na região. Essa decisão resolve a pendência de atribuí-lo aos vendedores quando dois nomes aparecem na mesma competência.

**Titularidade do XP de adiantamento, confirmada em 14/09/2026:** os XP das fases também ficam na região: 10 XP por fase confirmada, até 30 XP por mês e 120 XP na campanha. Dois vendedores na região não dividem nem duplicam a pontuação. A confirmação substitui a definição anterior de teto individual da antecipação; esses XP não entram nos totais dos vendedores.

**Meta por região, confirmado pelo usuário em 14/09/2026:** normalmente há um vendedor por região, mas podem aparecer dois no mesmo mês. Considerar uma única meta integral da região e consolidar suas vendas no período. Meta diária, meta parcial, atingimento e XP de vendas calculado são regionais. O exemplo em [Dados de metas](dados/dadoMeta.md) mostra dois vendedores compondo o mesmo realizado regional, sem dividir nem duplicar a meta.

**Participação confirmada em 14/09/2026:** a lista é formada pelas regiões de Canais e Construção com meta positiva na competência. Na fonte, isso corresponde a `Canais`, `Time Norte` e `Time Sul` em `metas_comerciais`. Vendedores vinculados a essas regiões participam dos indicadores individuais. Região sem meta ou com meta zero não entra até a publicação de uma meta válida; a tela de adiantamento segue a mesma lista.

**Admitidos e desligados confirmados em 14/09/2026:** calcular normalmente as vendas e os XP elegíveis de cada vendedor no período em que participar. Manter os mesmos tetos integrais da campanha, sem proporcionalidade ou projeção pelos meses ausentes. O desligamento não remove os XP históricos, e o campo de vendedor ativo não deve excluir suas vendas anteriores.

**Vendedores sem mudança de região, confirmado em 14/09/2026:** não haverá transferência entre regiões durante a campanha. Usar o vínculo fixo de `app_vendedor_regiao_time` para relacionar as vendas à região em todas as competências. A pendência sobre uma fonte histórica para transferências fica resolvida para este período; dois vendedores na mesma região continuam sendo uma possibilidade prevista.

**Data dos pedidos confirmada em 14/09/2026:** data de emissão = data de implantação do pedido. Usar `fct_pedido_item.data_emissao` para incluir pedidos no período da campanha, determinar sua competência mensal e comparar compras no histórico. O realizado até a referência considera pedidos elegíveis implantados até essa data. Aplicar os critérios de cancelamento e inadimplência abaixo.

**Valor do realizado confirmado em 14/09/2026:** considerar o valor bruto dos pedidos para comparar as vendas com a meta. A referência na fonte é `fct_pedido_item.valor_bruto_total`, agregada por região e competência de implantação.

**Rateio monetário confirmado em 14/09/2026:** seguir o dataflow e o Gestão Comercial. Cada parcela do pedido compõe o realizado da região do respectivo vendedor. Na triangulação de R$ 10.000 entre duas regiões, cada uma contabiliza R$ 5.000; se ambos os vendedores forem da mesma região, ela reúne R$ 10.000. Usar os valores já rateados da fonte, sem nova divisão e sem duplicar a venda. O rateio monetário está definido; cada região mantém sua meta integral e seus XP de vendas calculados pelo atingimento.

**Cancelamentos e inadimplência confirmados em 14/09/2026:** cancelar um pedido equivale a excluí-lo por inteiro. Ele deixa de ser uma venda válida e fica fora do realizado, do histórico de compras elegíveis e de todos os XP; a apuração posterior é reconstruída como se ele nunca tivesse participado. Adotar o bloqueio por grupo do Gestão Comercial, com exceções para SMART PODS e MRV. Para clientes bloqueados, considerar somente a parte já faturada; pedido de R$ 10.000 com R$ 4.000 faturados contabiliza R$ 4.000, com R$ 2.000 por região em uma triangulação entre duas regiões. O saldo aberto fica fora. Os checks de adiantamento continuam manuais.

**Quitação e histórico confirmados em 14/09/2026:** se o cliente quitar a dívida durante a campanha, seus pedidos em aberto voltam a participar com a data original de implantação. Enquanto o bloqueio existir, pedido não faturado também fica fora do histórico de novos, reativados e mix; somente os itens/quantidades faturados contam. O saldo reintegrado retorna à competência e à ordem histórica originais, e o realizado, as classificações e os XP afetados são recalculados; não lançar a venda no mês da quitação.

**Devoluções confirmadas em 14/09/2026:** todas entram no abatimento, independentemente do setor responsável, motivo, submotivo, tipo ou outra classificação. Abater somente o valor devolvido da competência original de implantação e recalcular os XP afetados. Uma devolução parcial mantém o saldo líquido; uma devolução total pode retirar o evento e alterar pedidos posteriores. Usar `fct_nota_devolucao.valor_devolucao_alocado`, já distribuído pelas alocações, sem nova divisão. A fonte observada não informa produto/item, limitação relevante para o mínimo e o histórico de mix.

**Operações não comerciais confirmadas em 14/09/2026:** bonificações, remessas e transferências de mercadoria ficam fora do realizado, do histórico de compras elegíveis e de todos os XP. A fonte possui `is_venda_comercial`, `is_bonificacao`, `is_remessa` e `is_transferencia` para aplicar e auditar essa regra.

**Estorno de nota fiscal confirmado em 14/09/2026:** se o pedido continuar ativo para refaturamento, ele permanece como uma única venda na competência original de implantação. A nova nota substitui a nota estornada e não gera outra venda ou XP. Para cliente bloqueado por inadimplência, somente notas válidas comprovam a parcela faturada em cada data de referência.

**Apuração pela situação atual confirmada em 14/09/2026:** resultados e XP calculados não ficam congelados depois de um fechamento. Toda mudança relevante nas fontes recalcula a competência original, o histórico e os XP afetados. Fotografias anteriores permanecem disponíveis para auditoria; os checks manuais de adiantamento só mudam por edição autorizada.

**Checks de adiantamento confirmados em 14/09/2026:** Laís e Leonardo informam diretamente `true` ou `false` para 32%, 56% e 80% de cada região/mês. O sistema usa a versão atual salva e não precisa definir o encerramento das semanas, calcular o atingimento pelas vendas ou validar uma fase com base nas demais.

**Documentos de regras e contexto atualizados em 14/09/2026:** foram consolidados os conceitos de cliente novo na empresa por grupo comercial, carteira, mix, KA, duplicidade de pedidos, acesso atual, validação contra o dataflow/Gestão Comercial e a regra de quitação. Campos que dependem de decisão de negócio ainda permanecem explícitos para as próximas confirmações.

**Mapeamento técnico em 14/09/2026:** o código local oferece `vw_clientes_inadimplentes` e `fct_faturamento_item.valor_bruto_item` para essa regra; o valor faturado também vem rateado. Não foi feita nova consulta ao Supabase, e as prévias salvas ainda não aplicam inadimplência. Conferência e pendências em [Elegibilidade de vendas](dados/elegibilidadeVendas.md).

**Metas e acompanhamento confirmados pelo usuário em 14/09/2026:** em setembro, usar a meta de setembro e o realizado acumulado no mês. Contar segunda a sexta, descontando feriados nacionais. Calcular `meta_parcial = meta_mes * dias_uteis_decorridos / dias_uteis_mes` e comparar o realizado com essa meta parcial; **esse percentual também define os XP atuais de vendas**. Mostrar dias úteis restantes, meta diária e meta parcial. O exemplo em [Dados de metas](dados/dadoMeta.md) usa 21 dias úteis em setembro, com 9 decorridos e 12 restantes na referência de 14/09/2026 inclusive. O fechamento do quadrimestre permanece conforme o PDF, sem somar fotografias de XP de dias ou meses diferentes.

**Faixas de vendas confirmadas pelo usuário em 14/09/2026:** 550 XP correspondem a **110% até menos de 120%** do percentual usado na apuração: meta parcial mensal durante o acompanhamento e meta acumulada no fechamento do quadrimestre. Usar o percentual exato, sem arredondamento para enquadrar: 109,999% mantém 500 XP e 110% passa a 550 XP. Acima de 130%, acrescentar 50 XP apenas a cada 10 pontos percentuais completos: 135% mantém 650 XP; 140% passa a 700 XP. A tabela e a fórmula em [Regras da campanha](regras/regrasCampanha.md) incorporam essas definições, com limites iniciais inclusivos e finais exclusivos.

**Segmento nas triangulações, confirmado pelo usuário em 14/09/2026:** os dois vendedores sempre pertencem ao mesmo segmento, Construção ou Canais. Usar esse segmento comum para os mínimos de mix e os prazos de reativação. Se o cadastro mostrar segmentos diferentes ou ausentes, manter a conferência pendente por inconsistência dos dados.

**Mínimo de mix em triangulações, confirmado pelo usuário em 14/09/2026:** considerar o valor total da linha no pedido, antes da divisão entre vendedores. Exemplo: R$ 3.000 de Hydrofix em Construção atende ao mínimo mesmo com R$ 1.500 alocados a cada vendedor; cumpridas as demais condições de mix, gera 10 XP no evento e 5 XP para cada participante.

**XP em triangulações, confirmado pelo usuário em 14/09/2026:** dividir os XP dos eventos elegíveis igualmente entre os dois vendedores. Por vendedor: 5 XP por cliente novo, 4 por reativado e 5 por linha de mix elegível. Consolidar essas parcelas por vendedor e indicador antes de aplicar os tetos individuais. A proposta de identificação e rateio está em [Enquadramento dos pedidos](dados/dadoEnquadramento.md).

**Dia limite da reativação, confirmado pelo usuário em 14/09/2026:** o cliente já pode ser considerado reativado no dia em que completa 6 meses sem compras em Canais ou 12 meses em Construção, respeitando as demais condições. Usar meses de calendário e comparação inclusiva com a última compra do grupo comercial. A [consulta de prévia](dados/consultaPreviaClientes.sql) foi atualizada localmente; os resultados salvos permanecem a fotografia de 10/09/2026.

**Soma de XP entre indicadores, confirmada pelo usuário em 14/09/2026:** o mesmo pedido pode pontuar em indicadores diferentes, respeitando os critérios e tetos de cada um. Exemplo confirmado: grupo novo com uma expansão de linha elegível gera 10 XP de novo + 10 XP de mix = 20 XP, com crédito integral se houver saldo no teto de novos e atribuição definida. A regra e os exemplos estão em [Regras da campanha](regras/regrasCampanha.md), [Regras de negócio](regras/regraNegocio.md) e [Enquadramento dos pedidos](dados/dadoEnquadramento.md).

**Histórico suficiente, confirmado pelo usuário em 14/09/2026:** usar o histórico disponível desde janeiro de 2022 em `comercial_marts.fct_pedido_item` para identificar clientes novos e primeiras compras das linhas de mix pelo grupo comercial. A primeira data observada na fonte foi 03/01/2022. Não é necessário buscar compras anteriores a 2022 para esses critérios da campanha. Pendências de cadastro, dados ausentes e titularidade continuam seguindo suas regras próprias.

**Grupos comerciais pendentes, confirmado em 14/09/2026:** aguardar a correção do cadastro para concluir os enquadramentos que dependem do grupo. O usuário esclareceu que muitas vezes esses clientes são compradores pessoa física do Mercado Livre e não representam um grupo; essa observação não identifica automaticamente os 76 pedidos da prévia como Mercado Livre. A regra está em [Regras de negócio](regras/regraNegocio.md) e [Dados de clientes](dados/dadoCliente.md).

**Pontuação de mix detalhada pelo usuário:** 10 XP por primeira compra elegível de cada linha pelo grupo comercial, atingindo o mínimo no pedido. Hydrofix e Suporte de Bancada elegíveis geram duas expansões e 20 XP, inclusive no mesmo pedido; a mesma linha não pontua novamente. Compra anterior abaixo do mínimo também impede novidade em pedido posterior.

**Limites de XP confirmados na campanha:** por vendedor, novos têm teto de 100 XP e reativados de 80 XP; por região, antecipação tem teto de 120 XP, com até 30 XP por mês. Expansão de mix permanece sem teto por vendedor e venda no quadrimestre sem teto por região, conforme confirmação do usuário.

**Segmentos confirmados:** Time Norte e Time Sul → Construção; Canais → Canais. O mapeamento está em [timesSegmentos.csv](dados/timesSegmentos.csv). Aplicado à fotografia da [prévia de mix](dados/previaMix.md), o único candidato ficou abaixo do mínimo de Construção; nenhuma expansão elegível foi encontrada nos 37 registros analisados.

**Consolidação diária definida em 14/09/2026:** classificação de novo/reativado pelo grupo comercial e data. Todos os pedidos elegíveis do mesmo grupo no mesmo dia formam um evento e têm seus valores somados por linha para o mínimo de mix. Pedidos de dias diferentes não se acumulam. A proposta de [tabela de enquadramento](dados/dadoEnquadramento.md) registra os campos, evidências e regras ainda pendentes.

**XP do evento diário com dois vendedores, confirmado em 14/09/2026:** quando pedidos distintos do mesmo grupo e data reunirem exatamente dois vendedores identificados, dividir igualmente os XP do evento: 5 XP para cada vendedor em novo, 4 XP para cada em reativado e 5 XP para cada linha de mix elegível. O rateio dos XP não muda a atribuição monetária dos pedidos e das regiões. Um único vendedor recebe 100% dos XP; responsável ausente ou quantidade diferente de um ou dois permanece pendente para conferência.

**Lista KA recebida e conferida em 10/09/2026:** 16 grupos, todos encontrados por nome exato no Supabase. Os códigos estão em [Grupos KA](dados/dadoKA.md) e no [CSV de referência](dados/gruposKA.csv).

**Classificação KA fixa, confirmada em 14/09/2026:** usar os mesmos 16 grupos em toda a campanha, sem entrada ou saída entre setembro e dezembro. Divergências em cadastros externos devem aguardar correção e não alteram a lista da campanha.

**Produtos de mix informados e conferidos no Supabase em 10/09/2026:** 2 Hydrofix, 2 CPP 009, 2 kits Grelha + Porta Grelha e 17 Suportes de Bancada, totalizando 23 códigos únicos. A correspondência está em [produtosMix.csv](dados/produtosMix.csv); regras e mínimos por segmento em [Dados de clientes](dados/dadoCliente.md).

**Fontes confirmadas pelo usuário e conferidas no Supabase em 09/09/2026:** `comercial_marts.fct_pedido_item` para vendas e `comercial_marts.metas_comerciais` para metas. O histórico observado e os campos estão em [Dados de vendas](dados/dadoVenda.md) e [Dados de metas](dados/dadoMeta.md). As metas têm grão mensal por região, sem código de vendedor. A consulta histórica ao banco foi somente leitura. A tela de adiantamento usa Supabase Auth e Data API, sem senha PostgreSQL no Streamlit; seu SQL ainda aguarda aplicação no projeto.
