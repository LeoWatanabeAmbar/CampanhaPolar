# Primeira conferência de mix com pedidos reais

Consulta somente leitura executada no Supabase em 10/09/2026 às 15:34, horário de São Paulo. Nenhuma tabela ou dado foi alterado no banco. A conferência foi complementada localmente com o mapeamento de times confirmado pelo usuário, sem nova consulta ao banco, criação da tabela definitiva ou apuração completa de XP.

**Limite atualizado em 14/09/2026:** esta prévia não aplica a regra de inadimplência com exceções SMART PODS/MRV nem limita os pedidos bloqueados à parte faturada para avaliar mínimos de mix. Os resultados permanecem a fotografia histórica, sem recálculo ou concessão de XP. Ver [Elegibilidade de vendas](elegibilidadeVendas.md).

A prévia também não abate devoluções. A fonte de devolução observada não identifica produto/item, portanto não permite determinar sozinha qual linha de mix perdeu valor. Não reclassificar o resultado salvo sem essa evidência.

**Consolidação diária definida em 14/09/2026:** pedidos do mesmo grupo comercial e data formam um único evento e têm seus valores elegíveis somados por linha. O arquivo [consultaPreviaMix.sql](consultaPreviaMix.sql) foi atualizado para uma futura execução, mas os CSVs e totais abaixo continuam retratando a consulta original de 10/09/2026.

## Resultado observado

Recorte: emissão de 01/09/2026 até a data da consulta, com término máximo em 31/12/2026. A consulta usa todo o histórico disponível da fonte antes de aplicar esse recorte, apenas em itens comerciais válidos e nos 23 códigos de mix fornecidos pelo usuário.

**Critério histórico confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar primeiras compras das linhas de mix. A confirmação resolve a suficiência da janela usada nesta prévia. O resultado continua sem expansão elegível, pois o único candidato ficou abaixo do mínimo; esta atualização é documental, sem nova consulta ou alteração dos arquivos de resultados.

| Resultado | Combinações de pedido e linha |
| --- | ---: |
| Grupo KA | 21 |
| Linha já comprada anteriormente pelo grupo comercial | 15 |
| Candidato à primeira compra da linha | 1 |
| Total | 37 |

Nesta consulta, as 37 combinações correspondem a 37 pedidos distintos. As categorias são exclusivas e KA tem precedência; isso não significa que os 21 pedidos KA sejam todos primeiras compras. Não houve pendências de identificação ou empate de primeira data nos resultados retornados. O total não representa todos os pedidos comerciais da campanha, apenas os que contêm produtos do mix.

## Candidato encontrado e conferência do mínimo

| Informação | Valor |
| --- | --- |
| Filial / pedido | `01101` / `058680` |
| Emissão | 09/09/2026 |
| Grupo comercial | `F230` — CL2 CONSTRUTORA |
| Linha | Suporte de Bancada |
| Produto | `002917` |
| Vendedor alocado | `000125` |
| Valor da linha no pedido, soma das alocações | R$ 2.975,69, arredondado apenas para exibição |
| Primeira data observada da linha no grupo | 09/09/2026 |
| Grupo KA | Não |
| Triangulação | Não |
| Região no cadastro atual | REG 10 - CO |
| Time no cadastro atual | Time Norte |
| Segmento confirmado | Construção |
| Mínimo da linha nesse segmento | R$ 9.000,00 |
| Resultado após conferir o mínimo | Abaixo do mínimo; não gera expansão de mix |

O usuário confirmou **Time Norte → Construção**, **Time Sul → Construção** e **Canais → Canais**, registrados em [timesSegmentos.csv](timesSegmentos.csv). O vendedor do candidato está no Time Norte no cadastro consultado, portanto aplica-se o mínimo de Construção.

O valor de R$ 2.975,69 fica abaixo de R$ 9.000,00. A comparação foi feita com o valor decimal completo da consulta, sem arredondamento prévio. O pedido `058680` não gera expansão de Suporte de Bancada. Como há compra da linha no histórico, um pedido posterior acima do mínimo não se torna a primeira compra dessa linha para o grupo.

**Resultado dessa fotografia após aplicar o mapeamento:** 21 pedidos/linhas excluídos por KA, 15 por compra anterior da linha e 1 por valor abaixo do mínimo. Nenhuma expansão elegível de mix foi encontrada nos 37 registros analisados. Isso não representa a apuração de clientes novos, reativados, antecipação ou vendas, nem novos pedidos que tenham entrado após a consulta original.

A consulta usou a data de emissão e a soma do valor bruto comercial como referências propostas na época. **Atualização documental em 14/09/2026:** o usuário confirmou que emissão = implantação do pedido e que essa é a data de apuração da campanha; também confirmou o valor bruto dos pedidos como base do realizado comparado à meta e o rateio monetário do dataflow/Gestão Comercial, com cada parcela atribuída à região do respectivo vendedor. O candidato avaliado não tem triangulação nem valor ausente. Estas definições não alteram os resultados salvos da prévia.

**Mínimo e rateio com dois vendedores confirmados pelo usuário em 14/09/2026:** usar o valor total da linha no evento diário antes da divisão dos XP. O campo `valor_linha_evento_soma_alocacoes` da consulta atualizada soma os pedidos e alocações do mesmo grupo, data e linha; em triangulações, essa soma recompõe o total quando as alocações estão completas e válidas. A futura apuração deve conferir alocações incompletas e valores ausentes antes de concluir o mínimo. Se o evento elegível reunir exatamente dois vendedores identificados, cada um recebe 5 XP, inclusive quando vierem de pedidos distintos; com um vendedor, ele recebe os 10 XP. Esta atualização documental não altera os resultados salvos da prévia, cujo único candidato não tem triangulação.

## Arquivos da conferência

- [previaMix.csv](previaMix.csv): os 37 registros, com pedido, grupo, linha, primeira data observada, valor e motivo do resultado. Identificadores devem ser lidos como texto para preservar os zeros à esquerda; valores usam ponto decimal e o arquivo usa ponto e vírgula como separador.
- [previaMixAvaliada.csv](previaMixAvaliada.csv): fotografia original complementada com time, segmento, mínimo e resultado após avaliar o candidato. Registros já excluídos por KA/histórico mantêm seu motivo e não exigiram enriquecimento de segmento nesta conferência.
- [previaMixResumo.json](previaMixResumo.json): contagens e data/hora da consulta original, com a avaliação posterior do mínimo em seção separada.
- [previaMixVinculoVendedor.json](previaMixVinculoVendedor.json): região/time atuais do vendedor do candidato, consultados somente para leitura.
- [consultaPreviaMix.sql](consultaPreviaMix.sql): consulta parametrizada de diagnóstico. Os parâmetros `produtos_mix` e `grupos_ka` são arrays JSON de registros dos CSVs [produtosMix.csv](produtosMix.csv) e [gruposKA.csv](gruposKA.csv), passados pelo cliente psycopg2. A consulta não contém credenciais.

A execução validou os 23 códigos únicos de mix, os 16 códigos únicos KA e a ausência de duplicação da chave pedido/grupo/linha na saída. Para os candidatos, conferiu coincidência com a primeira data observada, ausência de KA e de empate de pedidos nessa data.

Esta prévia não apura clientes novos/reativados, metas, antecipação ou o total individual de XP. A primeira compra observada está limitada ao histórico e aos códigos disponíveis, com os vínculos de grupo comercial presentes na fonte. O SQL mantém sinalizadores de valores ausentes, datas históricas ausentes e triangulação; o mínimo do candidato foi avaliado na etapa local posterior, usando o time consultado e o mapeamento confirmado.
