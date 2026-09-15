# Conferência de grupos novos e reativados

Consulta somente leitura executada no Supabase em 10/09/2026 às 16:16, horário de São Paulo. Foram analisados os pedidos emitidos desde 01/09/2026 até a consulta, usando todo o histórico disponível de itens comerciais válidos de `comercial_marts.fct_pedido_item`. Não restringir essa análise aos produtos do mix.

**Limite atualizado em 14/09/2026:** esta prévia não aplica a regra de inadimplência com exceções SMART PODS/MRV nem restringe clientes bloqueados à parte faturada. Os resultados salvos não comprovam a elegibilidade de crédito definida posteriormente. Ver [Elegibilidade de vendas](elegibilidadeVendas.md); não houve recálculo ou nova consulta nesta atualização documental.

A prévia também não abate devoluções posteriores. Uma devolução total pode remover uma compra da sequência histórica e alterar clientes novos ou reativados; os CSVs permanecem como fotografia anterior à definição, sem concessão de XP.

A tabela definitiva não foi criada e nenhum XP foi concedido. A classificação da consulta é **novo no histórico observado**. **Confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar clientes novos na campanha. Assim, os 7 grupos encontrados atendem ao critério histórico de novidade, sem exigir consulta a compras anteriores a 2022; o crédito de XP segue sujeito às demais regras, incluindo atribuição. Os CSVs e o resumo JSON preservam os rótulos e resultados da consulta original.

## Resultado

| Resultado por pedido/grupo | Quantidade |
| --- | ---: |
| Ativo, com compra recente | 230 |
| Sem grupo comercial identificado | 76 |
| Novo no histórico | 8 pedidos de 7 grupos |
| Candidato à reativação | 6 pedidos de 6 grupos |
| Segmento pendente | 3 |
| Total | 323 |

As 323 combinações correspondem a 323 pedidos distintos. As contagens de grupos por categoria não devem ser somadas como grupos únicos da campanha: um grupo pode ter sua primeira compra ou reativação e posteriormente aparecer como ativo.

## Grupos novos no histórico

| Grupo comercial | Pedido(s) da primeira data | Data | Vendedor alocado | Time atual |
| --- | --- | --- | --- | --- |
| `F213` — FIPAL CONSTRUTORA | `058349` | 01/09/2026 | `000172` | Time Sul |
| `F203` — NOVO HORIZONTE | `058382` | 02/09/2026 | `000125` | Time Norte |
| `F209` — CASA PADIM | `058383` | 02/09/2026 | `000125` | Time Norte |
| `F180` — SOLUCOES IMOBILIARIAS MGF LTDA | `058642` | 08/09/2026 | `000186` | Time Sul |
| `F230` — CL2 CONSTRUTORA | `058680` | 09/09/2026 | `000125` | Time Norte |
| `F226` — IRMAOS MALHEIROS CONSTRUTORA | `058687` | 10/09/2026 | `000125` | Time Norte |
| `F224` — PLANO INCORPORACOES LTDA | `058691`, `058697` | 10/09/2026 | `000170` | Time Norte |

`F224` tem dois pedidos na primeira data observada. **Regra confirmada pelo usuário em 14/09/2026:** tratá-los como um único evento diário do grupo, somando os valores elegíveis e gerando no máximo uma pontuação de cliente novo. Ambos estão alocados ao mesmo vendedor na fotografia consultada. Preservar os dois números de pedido como evidência; não é necessário escolher um deles como primeiro.

O grupo CL2 CONSTRUTORA atende ao critério histórico de cliente novo aceito pelo usuário, mesmo que seu pedido não tenha atingido o mínimo de mix na [prévia anterior](previaMix.md). Os indicadores têm critérios distintos.

## Candidatos à reativação

| Grupo comercial | Pedido | Compra atual | Última compra em data anterior | Segmento | Vendedor |
| --- | --- | --- | --- | --- | --- |
| `E672` — GELLAR | `058476` | 02/09/2026 | 07/10/2025 | Canais | `000183` |
| `CB2` — URBEN PARTICIPACOES | `058578` | 04/09/2026 | 08/05/2025 | Construção | `000164` |
| `C5E` — CONSTRUTORA SINARCO | `058597` | 04/09/2026 | 31/07/2025 | Construção | `000113` |
| `CMK` — CARRERA E RORIZ | `058654` | 08/09/2026 | 12/12/2025 | Canais | `000187` |
| `CSO` — FRIGEMAR | `058674` | 09/09/2026 | 19/02/2026 | Canais | `000183` |
| `E555` — FERCRIL DISTRIBUIDORA | `058704` | 10/09/2026 | 23/02/2026 | Canais | `000183` |

Todos os seis ultrapassam o prazo aplicável: 12 meses em Construção e 6 em Canais. A execução original usava meses de calendário e separava os casos exatamente no limite. **Confirmado pelo usuário em 14/09/2026:** o dia em que se completam 6 ou 12 meses já vale para reativação. O arquivo SQL foi atualizado localmente para usar comparação inclusiva (`<=`) e deixar de tratar a igualdade como pendência. Nenhum candidato desta fotografia depende de aceitar o dia exato do limite; os resultados salvos continuam referentes à consulta de 10/09/2026, sem nova execução no banco.

## Pendências observadas

- **75 pedidos sem grupo comercial:** aguardar a correção do cadastro, conforme confirmado pelo usuário em 14/09/2026. Manter o enquadramento pendente, sem pontuar novos/reativados e sem avaliar cada cliente individualmente ou criar um grupo fictício.
- **1 pedido com código de grupo `00` sem correspondência na dimensão:** também aguardar a correção do cadastro, com identificação e enquadramento pendentes.
- **2 pedidos do grupo `CQQ` (`058504` e `058505`):** vendedor `000152`, time `Outros`, fora do mapeamento confirmado. A última compra em data anterior é 19/08/2026.
- **1 pedido do grupo `CQ4` (`058655`):** sem vendedor e sem time identificado. A última compra em data anterior é 03/08/2026.

**Esclarecimento do usuário em 14/09/2026:** muitas vezes os clientes com grupo pendente são compradores pessoa física do Mercado Livre e não representam um grupo comercial. A observação não confirma o canal de cada um dos 76 pedidos. A decisão de aguardar correção resolve a regra de tratamento; os cadastros continuam pendentes. Os números acima permanecem a fotografia da consulta de 10/09/2026, sem nova consulta ou reclassificação nesta atualização documental.

Os três pedidos sem segmento têm compras recentes, mas ficaram sinalizados para resolver o cadastro e a participação na campanha. Não presumir que `Outros` seja Construção ou Canais. O segmento dos demais foi obtido do cadastro atual de vendedor com o [mapeamento confirmado](timesSegmentos.csv); isso não constitui histórico de mudanças de time.

## Arquivos e validação

- [previaClientes.csv](previaClientes.csv): 323 registros com histórico, segmento, vendedores e motivos. Ler códigos como texto; o arquivo usa ponto e vírgula e valores numéricos com ponto decimal.
- [previaClientesResumo.json](previaClientesResumo.json): contagens, data/hora e indicadores de pendência.
- [consultaPreviaClientes.sql](consultaPreviaClientes.sql): consulta parametrizada de diagnóstico, atualizada em 14/09/2026 com o limite inclusivo de reativação e a consolidação dos pedidos do mesmo grupo/data em um evento diário. Recebe `times_segmentos` como array JSON dos registros de [timesSegmentos.csv](timesSegmentos.csv), pelo cliente psycopg2. O alias `data_limite_reativacao_proposta` foi preservado por compatibilidade conceitual; os arquivos de resultado existentes continuam anteriores à atualização.

A execução comparou a contagem da saída com uma consulta independente dos pedidos/grupos comerciais válidos do período, confirmou unicidade da chave filial/pedido/grupo e verificou as relações de datas de todos os candidatos. As alocações e itens são consolidados antes de consultar eventos anteriores, impedindo que outro item do próprio pedido se torne uma compra anterior.

O resultado classifica o grupo na data da compra. Pedidos do mesmo grupo nessa data formam um único evento e têm seus valores elegíveis somados. A consulta SQL foi atualizada para essa regra; os CSVs salvos ainda mostram os pedidos separadamente porque foram gerados antes da definição. A suficiência do histórico desde 2022 para clientes novos foi confirmada pelo usuário em 14/09/2026. Os limites de 100 XP em novos e 80 XP em reativados serão aplicados por vendedor após validar eventos, datas e titularidade. A classificação KA não exclui automaticamente esses dois indicadores.

**Rateio confirmado pelo usuário em 14/09/2026:** nas triangulações e nos eventos diários consolidados com exatamente dois vendedores identificados, atribuir 50% dos XP elegíveis a cada um antes dos tetos individuais. Com um vendedor identificado, atribuir 100% a ele. A consulta atualizada expõe `situacao_atribuicao` e `fracao_xp_por_vendedor`; responsável ausente ou quantidade diferente de um ou dois fica pendente. Esses campos diagnosticam os participantes do evento e não validam sozinhos as alocações de uma triangulação. A apuração proposta está em [Enquadramento dos pedidos](dadoEnquadramento.md); os resultados históricos não foram recalculados nem receberam XP nesta atualização.
