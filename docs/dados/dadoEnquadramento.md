# Enquadramento dos pedidos na campanha

## Objetivo e situação

**Solicitado pelo usuário em 10/09/2026:** utilizar o histórico de `comercial_marts.fct_pedido_item`, disponível desde 2022, para derivar uma nova tabela que sinalize clientes novos, reativados e enquadramento no mix nos pedidos a partir de 01/09/2026.

Nome proposto: `comercial_marts.fct_campanha_polar_item`. Este documento especifica a proposta; a tabela ainda não foi criada no Supabase. As regras de XP estão em [regrasCampanha.md](../regras/regrasCampanha.md).

A [primeira prévia de mix](previaMix.md) foi executada em 10/09/2026 por consulta somente leitura. Ela contém pedidos reais para conferir histórico e KA, sem materialização de tabelas ou cálculo definitivo de XP.

A [prévia de novos e reativados](previaClientes.md), também somente leitura, conferiu 323 pedidos e identificou 7 grupos novos no histórico, 6 candidatos à reativação e pendências de cadastro. Os resultados não constituem concessão de XP.

**Confirmado pelo usuário:** a identidade para classificar novo/reativado é o grupo comercial. **Detalhamento de 14/09/2026:** pedidos do mesmo grupo na mesma data formam um único evento diário e têm seus valores elegíveis somados; o mínimo de mix deve ser atingido nesse evento. Para novidade do mix, a proposta também considera o histórico do grupo comercial, mantendo a mesma unidade de análise.

Adotar como recorte proposto `data_emissao >= DATE '2026-09-01' AND data_emissao < DATE '2027-01-01'`, incluindo o dia inicial e dezembro inteiro. A referência a 01/09/2026 foi informada pelo usuário; o término segue o quadrimestre do regulamento. **Confirmado pelo usuário em 14/09/2026:** data de emissão = data de implantação do pedido; `data_emissao` é a referência para a data de compra na campanha e no histórico consultado. A regra da data está definida, enquanto as demais condições de elegibilidade e fechamento seguem seus registros próprios.

**Participação confirmada pelo usuário em 14/09/2026:** gerar eventos da campanha somente para vendedores vinculados a regiões de Canais ou Construção que tenham `metas_comerciais.meta > 0` na competência do pedido. Compras anteriores continuam sendo consultadas para formar o histórico, mas não geram XP da campanha quando pertencem a região/competência sem meta válida. Se uma meta for publicada ou corrigida depois, reconstruir a apuração conforme a situação atual.

**Admitidos e desligados confirmados pelo usuário em 14/09/2026:** enquadrar normalmente os eventos elegíveis atribuídos a esses vendedores. Não exigir participação nos quatro meses, não proporcionalizar XP ou tetos e não apagar eventos quando `ativo` passar a `false`. O tempo menor de participação não cria compensação nem projeção; apenas pode impedir que o vendedor alcance os máximos pelo volume real obtido.

## Estrutura proposta

Manter uma linha por item e alocação comercial, como na fonte, com `campanha_id` + `pedido_item_id` como chave candidata. Validar sua unicidade no recorte de itens válidos antes da materialização. A referência de pedido continua sendo `filial_id` + `pedido_id`.

O detalhe por item permite identificar produtos elegíveis dentro de pedidos com vários produtos. A classificação do cliente é calculada por evento diário do grupo comercial e associada aos itens e pedidos que o compõem. Uma visão resumida poderá mostrar os indicadores consolidados, sem somar flags repetidas por item ou pedido.

| Coluna proposta | Significado |
| --- | --- |
| `campanha_id` | Identificador da campanha e seu período |
| `pedido_item_id`, `filial_id`, `pedido_id`, `item_pedido` | Rastreabilidade até o pedido original |
| `cliente_id`, `loja_cliente_id`, `grupo_comercial_id` | Cliente/loja de origem e grupo comercial usado para analisar o histórico |
| `produto_id`, `vendedor_metricas_id`, `tipo_alocacao_comercial` | Produto e responsável pela alocação |
| `is_triangulacao`, `representante_id`, `executivo_id` | Evidências da operação e dos dois participantes para o rateio de XP |
| `data_emissao`, `valor_bruto_total` | Data de emissão/implantação do pedido e valor alocado da fonte |
| `is_bloqueado_inadimplencia`, `fonte_situacao_financeira`, `data_referencia_financeira` | Bloqueio por grupo com exceções SMART PODS/MRV e evidência da situação financeira atual usada na apuração; a quitação reintegra pedidos pela implantação original |
| `valor_bruto_elegivel`, `situacao_elegibilidade_credito` | Valor e situação para crédito após cancelamento/inadimplência; cliente bloqueado participa somente pela parte faturada, preservando as alocações regionais |
| `valor_devolvido_alocado`, `valor_liquido_elegivel` | Devolução vinculada à nota/pedido original e saldo após o abatimento na competência de implantação |
| `segmento_campanha` | Time Norte e Time Sul → Construção; Canais → Canais, conforme mapeamento confirmado pelo usuário |
| `data_primeira_compra_observada` | Primeira compra encontrada até o evento analisado |
| `data_ultima_compra_anterior` | Última compra estritamente anterior ao evento analisado |
| `dias_sem_compra`, `meses_inatividade_exigidos` | Evidência do intervalo e prazo de 12 ou 6 meses |
| `classificacao_cliente` | `novo_no_historico`, `reativado`, `ativo` ou `pendente` |
| `is_cliente_novo`, `is_cliente_reativado` | Enquadramento segundo a regra de histórico adotada; nulo quando inconclusivo |
| `grupo_mix`, `is_produto_mix` | Grupo do regulamento ao qual o item pertence e participação na lista |
| `data_primeira_compra_grupo_observada`, `is_mix_novo_no_historico` | Evidência de novidade do grupo de mix para o grupo comercial |
| `is_ka` | Pertencimento à lista de grupos KA fornecida pelo usuário, por `grupo_comercial_id`; nulo se o grupo não puder ser identificado |
| `pedidos_evento`, `quantidade_pedidos_evento` | Pedidos físicos consolidados no evento do grupo comercial e da data; preservar filial e pedido para auditoria |
| `vendedores_evento`, `quantidade_vendedores`, `tem_vendedor_ausente` | Participantes distintos usados para atribuir 100% a um vendedor, 50% a cada um de dois vendedores ou deixar o caso pendente |
| `valor_mix_evento_dia`, `valor_minimo_mix`, `atingiu_minimo_mix` | Soma dos valores elegíveis da linha no evento diário, antes do rateio de XP, e comparação com o mínimo |
| `is_mix_elegivel` | Produto/grupo novo, mínimo atingido, segmento aplicável e cliente não KA |
| `enquadra_regra`, `status_enquadramento` | Resultado geral: `elegivel`, `nao_elegivel` ou `pendente` |
| `motivos_enquadramento` | Lista de motivos, permitindo mais de um indicador no mesmo pedido |
| `inicio_historico_consultado`, `versao_regra`, `calculado_em` | Cobertura do histórico e rastreabilidade do processamento |

`enquadra_regra` será verdadeiro quando ao menos um dos três indicadores estiver confirmado, falso quando todos forem negativos e nulo quando não houver positivo e existir pendência. Os resultados individuais continuam visíveis mesmo quando o resultado geral for positivo. Esse campo cobre novos, reativados e mix; antecipação e atingimento de metas são apurações distintas.

**Filtro de crédito confirmado pelo usuário em 14/09/2026:** aplicar também a [elegibilidade por cancelamento e inadimplência](elegibilidadeVendas.md). Pedido cancelado é integralmente excluído como venda inválida: sai do realizado, da sequência histórica de compras e de todos os XP, e provoca o recálculo dos eventos posteriores afetados. Para cliente bloqueado por inadimplência do grupo, somente a parte já faturada pode participar; SMART PODS e MRV são exceções ao bloqueio. As flags históricas de novidade não concedem XP sozinhas: exigir elegibilidade do pedido/parcela, mínimo aplicável, atribuição e teto. Preservar separadamente o diagnóstico histórico e o motivo de exclusão ou pendência de crédito.

**Quitação confirmada pelo usuário em 14/09/2026:** quando o grupo deixa de estar inadimplente durante a campanha, reintegrar o saldo em aberto elegível pela `data_emissao` original. Recalcular a competência original, os XP regionais de vendas, os eventos de novos/reativados/mix e os pedidos posteriores afetados. Não criar um evento novo na data da quitação nem pontuar novamente a parte já faturada.

**Estorno de nota confirmado pelo usuário em 14/09/2026:** quando o pedido permanece ativo para refaturamento, preservar o evento de compra e seus enquadramentos na data original de implantação. O refaturamento apenas substitui a evidência fiscal e não gera novo evento ou XP. Para grupos bloqueados por inadimplência, recalcular temporariamente a parcela elegível usando somente notas ainda válidas e reintegrar a parcela refaturada na posição original do pedido, sem duplicidade.

**Histórico financeiro confirmado pelo usuário em 14/09/2026:** pedido bloqueado por inadimplência e não faturado não entra na sequência de compras usada para definir primeira compra, última compra anterior ou primeira compra de linha de mix. Se houver faturamento parcial, somente os itens/quantidades faturados entram nessa sequência. Após quitação, incluir a parte liberada na posição de sua `data_emissao` original e recalcular os eventos seguintes. SMART PODS/MRV seguem a sequência normal por serem exceções ao bloqueio.

**Devoluções confirmadas pelo usuário em 14/09/2026:** considerar todas as devoluções, independentemente do setor responsável, motivo, submotivo, tipo ou classificação. Abater o valor devolvido do pedido original na competência de `data_emissao` e recalcular eventos e XP. Em devolução total, remover a compra da sequência histórica elegível e reavaliar pedidos posteriores; em devolução parcial, preservar somente o saldo e os itens não devolvidos. Para mix, recalcular o mínimo da linha com seu valor líquido. A fonte atual de devolução não traz produto/item, portanto não concluir a linha afetada sem evidência adicional.

## Sequência de cálculo

1. Ler todo o histórico disponível de pedidos comerciais válidos (`is_item_valido_metricas = true` e `is_venda_comercial = true`), preservando o período anterior à campanha. Excluir bonificações, remessas e transferências de mercadoria pelas flags `is_bonificacao`, `is_remessa` e `is_transferencia`; essas operações não contam como compra anterior nem geram eventos ou XP. **Confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar clientes novos e primeiras compras das linhas de mix. A primeira data observada na fonte é 03/01/2022; não exigir consulta a períodos anteriores a 2022. A apuração usa os produtos e operações elegíveis presentes nessa fonte.
2. Usar `grupo_comercial_id` como identidade para o histórico, reunindo compras de todos os clientes/lojas do grupo. Preservar cliente e loja para auditoria. **Confirmado pelo usuário em 14/09/2026:** grupo ausente ou código sem correspondência no cadastro deve aguardar correção cadastral. Não agrupar registros sem grupo nem substituir o grupo por cliente, CPF ou CNPJ. Manter pendentes os enquadramentos que dependem dessa identificação, sem conceder XP de novos, reativados ou mix enquanto ela não estiver resolvida.
3. Construir eventos de compra sem repetir o mesmo pedido por item ou alocação. Para presença de compra, contar o pedido físico uma vez. Para valores, preservar o rateio de triangulação descrito em [dadoVenda.md](dadoVenda.md).
4. Para cada evento, localizar compras anteriores do grupo comercial e de qualquer código do grupo de mix dentro desse grupo comercial. Não usar compras futuras nem outros itens do próprio pedido como histórico anterior.
5. Aplicar as regras de cliente e mix, mantendo os motivos e pendências.
6. Selecionar os pedidos do período da campanha e associar os resultados aos itens e alocações.
7. Derivar a visão por pedido e, em uma apuração separada, os eventos que geram XP por cliente/participante/indicador.

Na etapa de crédito e na montagem do histórico elegível, para cliente bloqueado, usar os itens/quantidades efetivamente faturados e seu valor bruto elegível, com referência proposta em `fct_faturamento_item`, já rateado. Para o mínimo de mix, reunir as alocações completas da parte faturada da mesma linha no pedido; não liberar itens ainda não faturados nem repetir créditos por novas notas. Pedidos totalmente em aberto permanecem fora da sequência histórica enquanto houver bloqueio. Quitações durante a campanha exigem reconstruir essa sequência pela implantação original.

O histórico anterior inclui compras já realizadas durante a campanha. Por exemplo, após uma compra válida em 05/09, a compra de 20/09 deve considerar 05/09 como última compra; não pode continuar sendo uma primeira compra ou uma reativação calculada apenas contra agosto.

Isso vale mesmo que os dois pedidos pertençam a clientes ou CNPJs diferentes do mesmo grupo comercial. Um novo cadastro de cliente dentro de um grupo que já compra não cria um grupo novo. O `grupo_comercial_id` do fato vem do cadastro usado no processamento do dataflow; mudanças de grupo podem reclassificar o histórico. A necessidade de vínculo histórico ou fotografia do cadastro deve ser definida para o fechamento.

O usuário esclareceu que muitos clientes com grupo pendente são compradores pessoa física do Mercado Livre e não representam um grupo. Não inferir esse canal apenas pela ausência de grupo. Na proposta, registrar a pendência de identificação e aguardar a correção; quando ela estiver refletida na fonte, recalcular o histórico afetado conforme a seção de atualização. As regras de vendas elegíveis continuam determinando o tratamento do valor desses pedidos.

A fonte possui data, sem horário de emissão. **Confirmado pelo usuário em 14/09/2026:** vários pedidos do mesmo grupo comercial no dia formam um único evento, portanto não é necessário ordenar os pedidos nem escolher um deles como pontuador. Preservar todos os números de filial/pedido como evidência do evento consolidado.

## Clientes novos e reativados

**Novo no histórico, aceito como novo para a campanha:** nenhum evento de compra anterior encontrado para o grupo comercial no histórico disponível desde janeiro de 2022. **Confirmado pelo usuário em 14/09/2026:** essa janela é suficiente; não é necessário obter histórico anterior a 2022. Na proposta, manter `classificacao_cliente = 'novo_no_historico'` para rastrear o critério utilizado e usar `is_cliente_novo = true` quando o grupo estiver identificado e os dados permitirem concluir que não houve compra anterior. Não manter esse indicador pendente apenas pela ausência de histórico anterior a 2022. Cadastro ou datas históricas ausentes continuam como pendências; todos os pedidos da mesma primeira data pertencem a um único evento e não exigem desempate entre si.

**Reativado:** existe compra anterior e o intervalo até o novo pedido atende ao segmento: pelo menos 12 meses para Construção ou 6 meses para Canais. **Confirmado pelo usuário em 14/09/2026:** o dia em que se completa o prazo já é elegível à reativação. Aplicar comparação inclusiva: `data_ultima_compra_anterior <= data_emissao - intervalo_exigido`, usando a emissão/implantação do pedido, também confirmada pelo usuário como referência da apuração. Usar meses/anos de calendário, não aproximar por 180 ou 365 dias. Sem segmento ou sem cobertura confiável da janela de inatividade, manter pendente; a igualdade ao limite não é mais motivo de pendência.

**Mapeamento de segmento confirmado:** Time Norte e Time Sul são Construção; Canais é Canais. Usar [timesSegmentos.csv](timesSegmentos.csv) sobre o time do cadastro de vendedor. **Confirmado pelo usuário em 14/09/2026:** os dois vendedores de uma triangulação pertencem sempre ao mesmo segmento; aplicar os prazos de reativação e mínimos de mix desse segmento comum. Validar a igualdade após mapear os times, sem exigir nomes de time idênticos: Time Norte e Time Sul correspondem ambos a Construção. Times desconhecidos ou ausentes permanecem pendentes. Se uma triangulação apresentar segmentos diferentes na fonte, sinalizar inconsistência cadastral e manter pendente o enquadramento que depende do segmento até a conferência; a regra de segmento comum já está definida. O cadastro consultado é atual; esse mapeamento não cria histórico de mudanças de time.

**Ativo:** existe compra anterior dentro do prazo de inatividade. Cliente ativo pode enquadrar no mix.

## Expansão de mix

Participar da lista de produtos é uma condição distinta de gerar expansão. O enquadramento exige identificar o grupo de mix, verificar novidade para o grupo comercial, aplicar o mínimo correspondente ao segmento e excluir KA. Clientes novos e existentes podem participar, conforme já confirmado pelo usuário.

**Regra detalhada pelo usuário:** o grupo comercial não pode ter comprado a linha antes no histórico; o primeiro evento diário deve atingir o mínimo pela soma dos pedidos do grupo naquela data. Cada linha nova elegível gera uma expansão e 10 XP. Hydrofix e Suporte de Bancada elegíveis para o mesmo grupo geram dois eventos e 20 XP, inclusive no mesmo dia. “Linha” é o `grupo_mix` do mapeamento da campanha, sem depender do campo físico `linha_produto` que estava nulo nos produtos consultados.

**Janela histórica confirmada pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar a primeira compra de cada linha pelo grupo comercial. Na proposta, `is_mix_novo_no_historico = true` atende ao critério de novidade quando a consulta válida não encontra compra anterior da linha. A elegibilidade continua dependendo do mínimo no pedido, segmento, classificação KA e resolução de outras pendências; não exigir compras anteriores a 2022 para validar a janela.

Manter uma correspondência explícita de `produto_id` para `grupo_mix`, com vigência e fonte da classificação. Nomes como Hydrofix ou CPP 009 não devem ser convertidos automaticamente em códigos por semelhança textual. A novidade é avaliada pelo grupo de mix do regulamento. Conforme esclarecimento do usuário, trocar Suporte 300 por Suporte 500 não conta como expansão. O cálculo consulta a combinação de grupo comercial e grupo de mix; código, medida ou versão diferentes dentro do mesmo grupo de mix não criam novidade.

**Hydrofix informado pelo usuário:** `002920` (HYDROFIX AF) e `002921` (HYDROFIX AQ), ambos conferidos em `dim_produto` em 10/09/2026. A correspondência está em [produtosMix.csv](produtosMix.csv); preservar códigos como texto. `linha_produto` e `subfamilia` estão nulos para os dois códigos, portanto usar a lista explícita. Ambos compõem o grupo Hydrofix para somar o valor no mesmo pedido, sem exigir a presença das duas variantes. A novidade histórica considera o grupo Hydrofix, reunindo AF e AQ.

**CPP 009 informado pelo usuário:** `000010` (CAIXA DE PASSAGEM POLAR SPLIT CPP 009) e `002736` (CAIXA DE PASSAGEM POLAR SPLIT CPP 009 RV (M10)), conferidos em `dim_produto` em 10/09/2026 e registrados em [produtosMix.csv](produtosMix.csv). Ambos são elegíveis para análise na dimensão, mas não têm `linha_produto` nem `subfamilia` preenchidas. Somar os valores desses códigos no mesmo pedido para o mínimo de CPP 009 em Canais, sem exigir as duas variantes. A novidade histórica considera o grupo CPP 009, reunindo suas variantes.

| Segmento | Grupo de mix | Valor mínimo conforme regulamento |
| --- | --- | ---: |
| Construção | Hydrofix | R$ 3.000,00 |
| Construção | Grelha + Porta Grelha | R$ 6.000,00 |
| Construção | Suporte de Bancada | R$ 9.000,00 |
| Canais | Suporte de Bancada | R$ 1.000,00 |
| Canais | Grelha e Porta grelha | R$ 1.000,00 |
| Canais | CPP 009 | R$ 2.200,00 |

**Grelha + Porta Grelha informado pelo usuário:** `002968` (KIT GRELHA E PORTA GRELHA DN100) e `002969` (KIT GRELHA E PORTA GRELHA DN150), conferidos em `dim_produto` em 10/09/2026 e registrados em [produtosMix.csv](produtosMix.csv). Ambos têm `is_produto_elegivel_analise = true`, com `linha_produto` e `subfamilia` nulos. Somar os valores dos dois códigos no mesmo pedido para o mínimo do segmento, sem exigir ambas as medidas. Cada código já corresponde ao kit de grelha e porta-grelha; não há produtos avulsos mapeados. A novidade histórica considera o grupo Grelha + Porta Grelha, reunindo DN100 e DN150.

**Suporte de Bancada informado pelo usuário:** 17 códigos registrados em [produtosMix.csv](produtosMix.csv) e detalhados em [dadoCliente.md](dadoCliente.md), todos encontrados em `dim_produto` em 10/09/2026, com `is_produto_elegivel_analise = true` e `linha_produto`/`subfamilia` nulos. Somar seus valores no mesmo pedido para o mínimo do segmento. Não exigir várias medidas/versões juntas nem ajustar o valor pelo texto `PAR`. Códigos com descrições iguais continuam distintos na correspondência; a novidade histórica considera o grupo Suporte de Bancada, reunindo os 17 códigos.

**Mapeamento dos produtos concluído:** 23 códigos únicos nos quatro grupos de mix fornecidos pelo usuário. Para códigos de produto identificados e válidos, a ausência na lista significa `is_produto_mix = false` nesta versão. Código ausente ou inválido permanece pendente. A novidade histórica é calculada por grupo de mix no histórico desde 2022, aceito pelo usuário; verificar mínimo, segmento, KA e eventuais dados ausentes para concluir a elegibilidade.

**Mínimo por evento diário, confirmado pelo usuário em 14/09/2026:** somar somente os itens elegíveis do mesmo grupo de mix em todos os pedidos do grupo comercial na mesma `data_emissao`, respeitando o segmento. Não somar produtos de outra linha nem pedidos de datas diferentes. Dois pedidos de Hydrofix de R$ 1.500,00 no mesmo dia atingem juntos o mínimo de Construção de R$ 3.000,00; se forem de dias diferentes, não se acumulam.

O histórico de novidade continua sendo anterior ao pedido e inclui compras anteriores à campanha e compras já realizadas durante ela. Qualquer compra anterior de um código da linha pelo grupo comercial impede a novidade, mesmo abaixo do mínimo. Se a primeira compra da linha ficar abaixo do mínimo, o evento não gera XP; uma compra posterior acima do mínimo também não gera expansão porque já existe compra anterior. Não procurar a primeira compra acima do mínimo ignorando compras menores anteriores.

`valor_mix_evento_dia` é uma medida por grupo comercial/data/grupo de mix/segmento: se for repetida nos itens ou pedidos de origem, não poderá ser somada novamente na visão. O mesmo vale para mínimos e indicadores repetidos. **Confirmado pelo usuário em 14/09/2026:** somar os pedidos do mesmo grupo e dia e, nas triangulações, considerar o total da linha antes da divisão de XP entre vendedores. Exemplo: R$ 3.000 de Hydrofix em Construção atende ao mínimo mesmo que cada vendedor tenha R$ 1.500 alocados. Cumpridas as demais condições, o evento gera 10 XP e cada vendedor recebe 5 XP.

Na proposta, somar `valor_bruto_total` dos itens da mesma linha e das alocações válidas e completas de representante/executivo para recompor o total anterior ao rateio. Não somar produtos de outras linhas, não comparar cada metade com o mínimo integral e não dividir novamente os valores já rateados da fonte. Se faltar uma alocação ou houver valores ausentes ou inconsistentes, a soma disponível não comprova o total; manter a conferência pendente até validar as alocações ou obter evidência do valor completo. O mínimo é validado no evento antes de distribuir seus XP.

Os [16 grupos KA](dadoKA.md) foram informados pelo usuário e tiveram seus códigos conferidos no Supabase em 10/09/2026. Usar essa lista como referência da campanha: grupo listado implica `is_ka = true` e `is_mix_elegivel = false`, com motivo `grupo_comercial_ka`. Grupo identificado e válido fora da lista recebe `is_ka = false`; grupo ausente ou desconhecido permanece pendente.

Os códigos informados de grelha e porta-grelha já são kits; o mapeamento não exige juntar produtos avulsos. Os mínimos se aplicam à primeira compra de linha por grupos novos ou existentes. **Confirmado pelo usuário em 14/09/2026:** a lista KA permanece fixa durante toda a campanha; não haverá mudança de classificação. A exclusão KA se limita ao mix, sem desqualificar automaticamente os outros indicadores.

## Enquadramento e pontuação

**Confirmado pelo usuário em 14/09/2026:** um evento diário pode gerar XP de indicadores diferentes, que serão somados após aplicar os critérios e limites de cada indicador. Guardar separadamente os enquadramentos e eventos de cada regra. Exemplo confirmado: grupo novo com uma expansão de linha elegível gera 10 XP de novo + 10 XP de mix = 20 XP; se o teto de novos já estiver atingido para o vendedor responsável, o acréscimo contabilizado será de 10 XP de mix. A mesma permissão permite somar reativação e mix quando ambos forem elegíveis; a titularidade continua sujeita às regras próprias.

Enquadramento não autoriza somar XP por registro de item ou pedido. Novos têm 10 XP por evento diário com teto individual de 100; reativados, 8 XP por evento diário com teto individual de 80; mix, 10 XP por primeira compra diária elegível de linha pelo grupo comercial, sem teto. **Confirmado pelo usuário em 14/09/2026:** nas triangulações e nos eventos diários consolidados com exatamente dois vendedores identificados, dividir o XP do evento em 50% para cada um antes de aplicar os tetos. Com um único vendedor identificado, atribuir 100% a ele. O valor monetário continua associado aos pedidos e alocações originais.

A classificação usará o grupo comercial conforme confirmado. Para mix, a identidade do evento é `campanha_id` + `grupo_comercial_id` + `grupo_mix`, com evidência da primeira compra histórica daquela linha. Cada combinação pontua uma única vez; linhas diferentes do mesmo grupo comercial geram eventos independentes. Não multiplicar pelos CNPJs, códigos de produto, itens ou alocações que compõem o evento. Em triangulações e em eventos diários com pedidos de dois vendedores identificados, manter um evento e duas atribuições de 50%. Não incluir vendedor na chave histórica de novidade, impedindo que uma troca de responsável crie outra expansão para o mesmo grupo e linha.

Na proposta de apuração de mix, guardar um registro por grupo comercial, data e linha, com a lista dos pedidos de origem, primeira data observada, valor somado da linha, mínimo do segmento e motivo do resultado. A visão por pedido pode repetir apenas a referência do evento, sem tornar o XP somável por linha de item. Duas linhas elegíveis no mesmo evento resultam em 2 expansões e 20 XP. Em triangulações, os 20 XP dessas duas linhas são atribuídos em 10 XP para cada vendedor. No resumo individual, somar as parcelas de XP atribuídas no indicador `expansao_mix`; a contagem de eventos vinculados ao vendedor não deve ser multiplicada automaticamente por 10.

### Atribuição individual de XP

**Regra confirmada pelo usuário em 14/09/2026:** metade dos XP para cada um dos dois vendedores quando a venda for de triangulação ou quando pedidos distintos do mesmo grupo e data formarem um evento diário com exatamente dois vendedores identificados. Na proposta, identificar a triangulação por `is_triangulacao` e validar as alocações de representante e executivo, usando `vendedor_metricas_id`, `tipo_alocacao_comercial`, `representante_id` e `executivo_id`. Para o segundo caso, obter os participantes distintos de todos os pedidos elegíveis que compõem o evento. Registros repetidos por item não criam participantes adicionais. Responsável ausente, alocações inconsistentes ou quantidade diferente de um ou dois participantes deixa a atribuição pendente; a quantidade de vendedores sozinha não comprova triangulação.

Guardar separadamente o evento e suas atribuições, com os seguintes campos propostos:

| Campo na atribuição | Finalidade |
| --- | --- |
| `evento_id`, `vendedor_id` | Chave única da parcela individual; o evento identifica a campanha e a regra |
| `filial_id`, `pedido_id`, `tipo_alocacao_comercial`, `is_triangulacao` | Evidências do pedido e da participação |
| `xp_evento` | Pontuação integral do evento antes de distribuir aos participantes; referência não somável entre atribuições |
| `percentual_atribuicao` | `0.5` para cada um dos dois vendedores identificados; `1` quando o evento estiver validado como integralmente atribuído a um único vendedor |
| `xp_atribuido` | `xp_evento * percentual_atribuicao`, antes do teto individual |
| `versao_regra`, `calculado_em` | Rastreabilidade da regra e do processamento |

Cada triangulação ou evento diário consolidado com dois vendedores identificados deve ter duas parcelas de 50%, cuja soma recompõe o XP integral do evento antes dos tetos. Por participante, novos geram 5 XP, reativados geram 4 XP e cada linha de mix elegível gera 5 XP. Primeiro dividir o XP, depois somar por vendedor e regra e aplicar os respectivos tetos. Se um vendedor atingir seu teto, sua parcela excedente permanece registrada para ele, sem redistribuição ao outro.

A regra distribui os XP dos eventos de novos, reativados e mix. Antecipação e venda no quadrimestre continuam com suas apurações próprias. O mínimo de mix nas triangulações usa o valor total da linha no pedido, conforme confirmado pelo usuário. **Base e rateio monetário confirmados pelo usuário em 14/09/2026:** valor bruto dos pedidos, com referência em `valor_bruto_total`, seguindo o dataflow e o Gestão Comercial. Atribuir cada parcela monetária à região do respectivo vendedor, sem dividir novamente os valores já rateados na fonte. Em um pedido de R$ 10.000 entre duas regiões, cada uma contabiliza R$ 5.000; se os dois vendedores forem da mesma região, ela contabiliza R$ 10.000. O XP de vendas é calculado pelo atingimento de cada região e permanece regional.

### Apuração por vendedor e regra

**Atingimento regional confirmado pelo usuário em 14/09/2026:** calcular meta, realizado, meta parcial e XP de vendas por região e competência, mesmo que dois vendedores apareçam na região no mês. A fotografia regional fica na chave `campanha_id` + `regiao` + `competencia` + `data_referencia`, conforme [Dados de metas](dadoMeta.md). **O XP de atingimento permanece registrado na região**, sem atribuição aos vendedores nem inclusão nos totais individuais. Os eventos de novos, reativados e mix continuam seguindo a atribuição individual já confirmada.

**Vínculo fixo confirmado pelo usuário em 14/09/2026:** os vendedores não mudarão de região durante a campanha. Relacionar `vendedor_metricas_id` a `app_vendedor_regiao_time.vendedor_id` para obter a região em todas as competências, verificando ausência ou ambiguidade do vínculo antes de agregar. Não é necessário tratar transferências regionais neste período; a presença simultânea de dois vendedores na mesma região continua permitida.

**Adiantamento regional confirmado pelo usuário em 14/09/2026:** os XP de antecipação também pertencem à região. Cada check `true` informado pelo usuário autorizado, uma única vez por região/mês/fase, gera 10 XP, até 30 XP no mês e 120 XP por região na campanha. Consolidar na chave `campanha_id` + `regiao` + `tipo_regra`, a partir da versão atual salva descrita em [Dados de adiantamento](dadoAdiantamento.md), sem calcular prazo ou percentual pelas vendas. A quantidade de vendedores e as versões de edição não multiplicam os créditos; não distribuir esses XP aos vendedores.

**Reforçado pelo usuário, para novos, reativados e mix:** aplicar os limites de XP por vendedor e por tipo de regra. A tabela de enquadramento preserva os pedidos e suas evidências; a apuração deve consolidar as parcelas dos eventos pontuáveis na chave `campanha_id` + `vendedor_id` + `tipo_regra`. Nas triangulações e nos eventos diários consolidados com dois vendedores identificados, usar o rateio de 50% descrito acima. Casos com identificação incompleta ou quantidade diferente de um ou dois vendedores exigem resolução antes do crédito.

O fluxo proposto é: identificar enquadramentos, resolver titularidade e repetição dos eventos, calcular o XP integral de cada evento, atribuir 100% ao único vendedor ou distribuir 50% para cada um dos dois vendedores identificados, somar o XP atribuído por vendedor/regra e então aplicar o teto de cada regra no acumulado individual da campanha. Só depois somar os resultados das regras para obter o total do vendedor. Não aplicar um teto global à soma bruta de todos os indicadores.

| Campo proposto na apuração | Finalidade |
| --- | --- |
| `campanha_id`, `vendedor_id`, `tipo_regra` | Chave do acumulado ao qual o limite se aplica |
| `quantidade_eventos_pontuaveis` | Eventos distintos vinculados ao vendedor após validação; eventos compartilhados aparecem para ambos, sem duplicar a contagem física global |
| `xp_gerado` | Para novos, reativados e mix, soma de `xp_atribuido` ao vendedor antes do teto, já com o rateio de triangulações. Os XP de antecipação e de atingimento de vendas pertencem à apuração regional e não integram este acumulado individual |
| `situacao_limite` | `com_limite`, `sem_limite` ou `pendente`, conforme regra documentada |
| `limite_xp` | Teto numérico quando a situação for `com_limite` |
| `xp_contabilizado` | Menor entre XP gerado e teto; igual ao gerado apenas quando `sem_limite` estiver confirmado; nulo quando pendente |
| `xp_excedente` | Diferença entre gerado e contabilizado, quando o cálculo estiver definido |
| `limite_atingido` | Indica alcance do teto, sem modificar o enquadramento dos pedidos |
| `versao_regra`, `calculado_em` | Rastreabilidade da apuração |

Os [limites documentados](../regras/regrasCampanha.md) são 100 XP em novos e 80 XP em reativados por vendedor na campanha. A antecipação tem teto de 120 XP por região na campanha, com até 30 XP regionais por mês, e fica em sua apuração regional. **Confirmado pelo usuário:** mix e venda no quadrimestre permanecem sem teto, nas respectivas unidades vendedor e região. Para ambos, usar `situacao_limite = 'sem_limite'`, `limite_xp = null`, `xp_contabilizado = xp_gerado`, `xp_excedente = 0` e `limite_atingido = false`, quando o XP estiver apurado. O valor nulo do teto só representa ausência de limite quando acompanhado da situação explícita `sem_limite`; outras pendências de elegibilidade, atribuição ou cálculo continuam sendo sinalizadas.

Não repetir os limites ou o XP consolidado como valores somáveis por item. As quatro famílias de mix pertencem ao mesmo indicador `expansao_mix`; não conceder um teto independente a cada família. **Confirmado pelo usuário em 14/09/2026:** durante o mês, os XP de vendas vêm do atingimento do realizado regional mensal sobre a meta parcial regional por dias úteis, conforme [Dados de metas](dadoMeta.md). Identificar a região, a competência e a data de referência dessa fotografia, que pode aumentar ou diminuir. O XP final de venda no quadrimestre vem do atingimento regional acumulado previsto no PDF, sem somar as fotografias diárias ou mensais. Na antecipação, somar as fases confirmadas de competências distintas por região, sem somar versões de edição. Os tetos de novos e reativados continuam no acumulado individual da campanha.

Filtros de mês ou produto não reiniciam o limite da campanha. Pedidos do mesmo grupo e data são um único evento, portanto não há desempate entre eles. Para aplicar tetos, ordenar os eventos diários por data; se eventos distintos do mesmo vendedor ocorrerem no mesmo dia junto ao limite, o total contabilizado permanece determinístico, embora a distribuição explicativa do último crédito entre eventos ainda dependa de uma regra de ordenação. Cancelamentos ou correções exigem recalcular o acumulado e o excedente.

## Atualização e conferência

Proposta: reconstruir a tabela derivada após a atualização bem-sucedida do dataflow. O volume observado permite avaliar essa abordagem antes de introduzir carga incremental. Corrigir ou cancelar uma compra histórica pode alterar o enquadramento de compras posteriores; recalcular apenas pedidos novos deixaria classificações antigas incorretas.

**Cancelamento confirmado pelo usuário:** tratar o pedido como excluído por inteiro e reconstruir a apuração como se ele nunca tivesse sido uma venda válida. Retirar suas parcelas do realizado regional na competência de implantação, removê-lo do histórico de novos, reativados e mix, recalcular faixas de vendas e reavaliar eventos, pedidos posteriores afetados e tetos individuais. O adiantamento manual não é alterado automaticamente por esse processamento.

Preservar a versão das regras e fotografias datadas da apuração para auditoria. **Confirmado pelo usuário em 14/09/2026:** fotografias e fechamentos anteriores não congelam o resultado; a situação atual das fontes sempre reconstrói o realizado, a sequência histórica, os enquadramentos, os tetos e os XP afetados. Não incorporar automaticamente regras de outra campanha presentes no Gestão Comercial. Os checks manuais de adiantamento não mudam nesse processamento.

| Caso para validar | Resultado esperado |
| --- | --- |
| Grupo identificado faz a primeira compra em setembro, sem compra anterior encontrada no histórico desde janeiro de 2022 e sem datas históricas ausentes | `novo_no_historico` e `is_cliente_novo = true`; janela histórica aceita para a campanha, com crédito de XP sujeito às demais regras |
| Novo CNPJ em grupo comercial com compra recente | Grupo ativo; o novo cadastro não gera novidade de cliente |
| Construção: última compra em 31/08/2025, pedido em 01/09/2026 | Reativado, se histórico e segmento estiverem validados |
| Construção: última compra em 01/09/2025, pedido em 01/09/2026, sem compras intermediárias | Reativado, com dados validados: exatamente 12 meses, limite inclusivo |
| Construção: última compra em 02/09/2025, pedido em 01/09/2026 | Ainda não completa 12 meses |
| Canais: última compra em 01/03/2026, pedido em 01/09/2026, sem compras intermediárias | Reativado, com dados validados: exatamente 6 meses, limite inclusivo |
| Canais: última compra em 02/03/2026, pedido em 01/09/2026 | Ainda não completa seis meses |
| Cliente compra em 05/09/2026 e novamente em 20/09/2026 | Segunda compra considera 05/09; não repete novidade ou reativação |
| Produto na lista, mas já comprado anteriormente pelo cliente | `is_produto_mix = true`, sem novidade de mix |
| Grupo comercial já comprou Suporte 300 (`001628`) e agora compra Suporte 500 (`001626`) | Sem expansão de mix: ambos pertencem a Suporte de Bancada, conforme confirmado pelo usuário |
| Outro cliente do mesmo grupo comercial já comprou qualquer Suporte de Bancada | Sem novidade de Suporte de Bancada para o grupo, mesmo que o novo pedido use outro código |
| Produto comprado anteriormente por outro cliente do mesmo grupo comercial | Sem novidade de mix pela proposta de análise por grupo |
| Construção: dois pedidos de Hydrofix de R$ 1.500,00 cada, em dias diferentes | Nenhum evento diário atinge o mínimo de R$ 3.000,00 |
| Construção: dois pedidos de Hydrofix de R$ 1.500,00 no mesmo dia para o mesmo grupo | Evento diário soma R$ 3.000,00; verificar novidade e KA para concluir elegibilidade |
| Mesmo grupo faz dois pedidos elegíveis no mesmo dia, um com o vendedor A e outro com o vendedor B | Um evento diário; dividir seus XP em 50% para A e 50% para B, mantendo o valor de cada pedido em sua atribuição regional original |
| Pedido sem grupo comercial ou com código sem correspondência no cadastro | Aguardar correção cadastral; sem XP de novos, reativados ou mix enquanto o grupo estiver pendente, sem agrupar registros ou avaliar o cliente individualmente |
| Cliente KA compra grupo novo acima do mínimo | Sem enquadramento no mix |
| KA ou correspondência de produto desconhecidos | Mix pendente |
| Triangulação com vários itens, representante e executivo distintos e identificados, elegível como novo | Um evento físico de compra de 10 XP; duas atribuições de 5 XP, sujeitas aos tetos de cada vendedor; XP não se repete por item |
| Triangulação elegível como reativação, com os dois responsáveis validados | Um evento de 8 XP; 4 XP atribuídos a cada vendedor antes dos tetos |
| Triangulação elegível como novo e uma linha de mix, com os dois responsáveis validados | Cada vendedor recebe 5 XP de novo + 5 XP de mix = 10 XP antes dos tetos |
| Triangulação com duas linhas de mix elegíveis e os dois responsáveis validados | Dois eventos de mix, 20 XP no pedido; 10 XP atribuídos a cada vendedor, com 5 por linha |
| Construção: triangulação com R$ 3.000 de Hydrofix no pedido, R$ 1.500 por vendedor, primeira compra elegível da linha por grupo não KA e alocações completas | Mínimo de Hydrofix atingido pelo total de R$ 3.000; um evento de mix de 10 XP, atribuído em 5 XP para cada vendedor |
| Mesmo cenário, mas o total de Hydrofix no pedido é R$ 2.999,98, com R$ 1.499,99 por vendedor | Mínimo não atingido; nenhum XP de mix para essa linha |
| Triangulação elegível como novo; vendedor A já tem 100 XP de novos e vendedor B tem saldo de pelo menos 5 XP | A recebe 5 XP como excedente; B contabiliza 5 XP; a parcela excedente de A não é transferida |
| Triangulação sem executivo identificado ou com alocações inconsistentes | Atribuição pendente; não conceder automaticamente os XP integrais ao único vendedor conhecido |
| Compra anterior cancelada após o processamento | Excluir integralmente a compra do histórico e recalcular os pedidos posteriores como se ela nunca tivesse sido válida |
| Cliente bloqueado por inadimplência, pedido sem faturamento | Sem valor elegível nem créditos derivados desse pedido |
| Cliente bloqueado, pedido totalmente em aberto antes de outra compra | O pedido bloqueado não constitui compra anterior; classificar a compra posterior com base nos demais eventos históricos elegíveis |
| Cliente bloqueado, pedido parcialmente faturado | Somente os itens e quantidades faturados entram como compra anterior; itens em aberto não impedem novidade até serem liberados |
| Cliente bloqueado por inadimplência, R$ 10.000 pedidos e R$ 4.000 faturados em triangulação entre duas regiões | R$ 4.000 elegíveis: R$ 2.000 para cada região; saldo aberto excluído e sem duplicação por nota/alocação |
| SMART PODS ou MRV com inadimplência | Exceção ao bloqueio financeiro; demais condições de elegibilidade continuam aplicáveis |
| Grupo quita a dívida em outubro; pedido de R$ 10.000 foi implantado em setembro e R$ 4.000 já estavam faturados | Reintegrar os R$ 6.000 restantes em setembro, totalizando R$ 10.000, e recalcular os eventos e XP afetados; não duplicar os R$ 4.000 já considerados |
| Pedido implantado em setembro tem devolução parcial em outubro | Abater somente o valor devolvido de setembro e recalcular o saldo, os eventos e os XP de setembro; preservar `data_devolucao` para auditoria |
| Bonificação, remessa ou transferência de mercadoria | Não incluir no realizado ou na sequência histórica elegível; nenhum XP é gerado |
| Nota fiscal estornada, pedido ativo e posteriormente refaturado | Manter uma única compra na implantação original; trocar a evidência fiscal sem criar nova venda ou XP. Se o grupo estiver bloqueado, considerar somente notas válidas em cada fotografia |
| Mesmo vendedor com 12 grupos novos pontuáveis integralmente atribuídos a ele | 120 XP gerados, 100 contabilizados e 20 excedentes |
| Mesmo vendedor com 11 grupos reativados pontuáveis integralmente atribuídos a ele | 88 XP gerados, 80 contabilizados e 8 excedentes |
| Vendedor com 20 eventos de cliente novo em triangulações, recebendo metade de cada evento | 100 XP gerados e contabilizados, com teto de novos atingido |
| Grupo novo com uma expansão de mix elegível no mesmo pedido, ambos atribuídos ao mesmo vendedor com saldo de pelo menos 10 XP no teto de novos | 10 XP de novo + 10 XP de mix = 20 XP contabilizados; preservar um evento por indicador |
| Grupo reativado com uma expansão de mix elegível no mesmo pedido, ambos atribuídos ao mesmo vendedor com saldo de pelo menos 8 XP no teto de reativados | 8 XP de reativado + 10 XP de mix = 18 XP contabilizados |
| Mesmo pedido elegível como novo e mix, com 100 XP de novos já contabilizados para o vendedor responsável | 10 XP de novo gerados como excedente e 10 XP de mix contabilizados; acréscimo de 10 XP ao total individual |
| Mesmo vendedor com 13 fases de antecipação válidas | 130 XP gerados, 120 contabilizados e 10 excedentes, se as fases forem validadas pela regra vigente |
| Vendedor atinge 100 XP de novos e depois pontua em reativados | Novos permanece limitado a 100; reativados usa seu próprio teto de 80 |
| Outro vendedor registra seu primeiro grupo novo | Seu limite é independente dos limites já atingidos pelos demais vendedores |
| Filtro mensal aplicado ao painel | Não reiniciar o teto individual da campanha |
| Vendedor com 20 eventos de mix efetivamente pontuáveis integralmente atribuídos a ele | 200 XP gerados e contabilizados, sem excedente por teto |
| Grupo não KA de Construção sem histórico de Hydrofix e Suporte; primeira compra com R$ 3.000 e R$ 9.000 dessas linhas no mesmo pedido | 2 expansões, 20 XP de mix; cada mínimo é atendido separadamente |
| Mesmo cenário, mas Hydrofix soma R$ 2.000 e Suporte R$ 10.000 | 1 expansão, 10 XP de Suporte; o excedente de Suporte não completa o mínimo de Hydrofix |
| Primeira compra de Hydrofix em Construção de R$ 2.000; compra posterior de R$ 3.000 | Nenhuma expansão: a primeira não atinge o mínimo e a posterior não é a primeira compra |
| Grupo repete compra de uma linha que já gerou expansão | 0 novas expansões e 0 novos XP de mix para essa linha |

As datas e exemplos desta seção são ilustrativos. A estrutura é uma proposta, sem tabela derivada criada no banco. A lista KA foi complementada com consulta somente leitura ao cadastro de grupos em 10/09/2026.
