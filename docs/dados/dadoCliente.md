# Dados de clientes e histórico de produtos

Estas informações permitem explicar clientes novos, reativados e expansão de mix. Elas podem estar na própria base de vendas; não é obrigatório existir um arquivo separado.

**Proposta solicitada em 10/09/2026:** derivar o enquadramento dos pedidos desde 01/09/2026 a partir do histórico de vendas. Estrutura, lógica e pendências estão em [Enquadramento dos pedidos](dadoEnquadramento.md).

A [conferência de novos e reativados](previaClientes.md) apresenta os primeiros casos reais e as pendências de identificação do grupo comercial, com consulta somente leitura de 10/09/2026.

## Fontes disponíveis

- Cadastro de clientes: `comercial_marts.dim_cliente`, ligado por `cliente_id` + `loja_cliente_id`; contém `documento_cliente` para eventual agrupamento por CNPJ.
- Histórico de compras: `comercial_marts.fct_pedido_item`; histórico observado desde 03/01/2022, conforme consulta de 09/09/2026. **Confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para identificar clientes novos e primeiras compras das linhas de mix. Usar pedidos comerciais válidos, sem exigir histórico anterior a 2022.
- Histórico de produtos comprados por cliente: derivar dos eventos de compra da mesma tabela, por cliente e `produto_id`/grupo validado de mix, sem repetir alocações como novas compras.
- Classificação KA: [lista de 16 grupos fornecida pelo usuário](dadoKA.md), com códigos conferidos em `comercial_marts.dim_grupo_comercial` no Supabase em 10/09/2026. Vínculo por `grupo_comercial_id`.
- Cadastro de produtos e famílias: `comercial_marts.dim_produto`; campos `produto_id`, `descricao_produto`, `linha_produto` e `subfamilia`. Os quatro grupos do regulamento estão mapeados pelos códigos informados pelo usuário: Hydrofix, CPP 009, Grelha + Porta Grelha e Suporte de Bancada.
- Responsável e frequência de atualização: [PREENCHER]

## Dicionário de colunas

| Base/aba | Nome real da coluna | O que significa | Tipo/formato | Exemplo fictício |
| --- | --- | --- | --- | --- |
| [PREENCHER] | [PREENCHER] | [PREENCHER] | [PREENCHER] | [PREENCHER] |

## Identificação e histórico

- Identidade para novo/reativado: `grupo_comercial_id`, confirmado pelo usuário. Reunir o histórico dos clientes/lojas do mesmo grupo; manter `cliente_id` + `loja_cliente_id` para rastreabilidade.
- **Grupo comercial pendente — confirmado pelo usuário em 14/09/2026:** aguardar a correção do cadastro quando o grupo estiver ausente ou o código não tiver correspondência no cadastro de grupos. A apuração dependente do grupo permanece pendente, sem XP de novos, reativados ou mix e sem avaliação individual por cliente, CPF ou CNPJ em substituição ao grupo.
- Segundo o usuário, muitas vezes esses clientes são compradores pessoa física do Mercado Livre e não representam um grupo. Essa informação é contexto operacional, não uma classificação comprovada de cada pedido sem grupo. Preservar os registros para conferência do cadastro, sem criar um grupo fictício comum.
- Vendedor responsável e segmento: `fct_pedido_item.vendedor_metricas_id` ligado a `app_vendedor_regiao_time.vendedor_id`. Conforme confirmado pelo usuário, Time Norte e Time Sul correspondem a Construção; Canais corresponde a Canais. Ver [timesSegmentos.csv](timesSegmentos.csv). **Confirmado em 14/09/2026:** nas vendas de triangulação e nos eventos diários que consolidem pedidos de exatamente dois vendedores identificados, cada vendedor recebe 50% dos XP elegíveis antes dos tetos individuais. Nas triangulações, ambos pertencem sempre ao mesmo segmento; usar esse segmento comum para mínimos de mix e prazos de reativação. Em um evento diário formado por pedidos distintos, os segmentos também devem ser consistentes para concluir o enquadramento. Conferir a flag de triangulação e as alocações de representante/executivo conforme [Dados de vendas](dadoVenda.md). Divergência ou ausência de segmento e atribuições com responsável ausente ou mais de dois vendedores são pendências de dados a conferir.
- Onde encontrar a primeira compra para a campanha: derivar de `comercial_marts.fct_pedido_item` pelo grupo comercial, usando o histórico disponível desde janeiro de 2022, aceito como suficiente pelo usuário. Consultar eventos comerciais válidos até o pedido analisado e usar `data_emissao`, equivalente à implantação do pedido, como referência confirmada pelo usuário em 14/09/2026. Para mix, acrescentar o grupo de mix à identidade histórica.
- Elegibilidade por inadimplência, **confirmada em 14/09/2026**: bloqueio por grupo comercial seguindo o Gestão Comercial, com exceções SMART PODS/MRV. Para os demais bloqueados, somente a parte já faturada do pedido participa. Um pedido totalmente em aberto fica fora também do histórico de novos, reativados e mix; em faturamento parcial, somente os itens e quantidades faturados constituem compra anterior. Fonte complementar identificada: `vw_clientes_inadimplentes`; usar a situação financeira atual para a elegibilidade corrente. Após quitação durante a campanha, reintegrar os pedidos em aberto pela implantação original e recalcular cronologicamente os resultados afetados. Detalhes em [Elegibilidade de vendas](elegibilidadeVendas.md).
- Onde encontrar a última compra anterior ao retorno do cliente: [PREENCHER]
- O histórico cobre pelo menos os períodos de inatividade do regulamento: [PREENCHER]
- Há classificação pronta de novo/reativado? Quem calcula e com qual regra: [PREENCHER]
- Como identificar KA: pertencimento de `grupo_comercial_id` à lista em [gruposKA.csv](gruposKA.csv). **Confirmado pelo usuário em 14/09/2026:** a lista é fixa para toda a campanha e não haverá mudança de classificação durante o período. Divergências ficam pendentes para correção cadastral.
- Novidade de mix: consultar eventos anteriores pela combinação de grupo comercial e grupo de mix (Hydrofix, CPP 009, Grelha + Porta Grelha ou Suporte de Bancada). Trocar código, medida ou versão dentro do mesmo grupo de mix não constitui expansão, conforme esclarecido pelo usuário com o exemplo de Suporte 300 para Suporte 500. **Confirmado pelo usuário em 14/09/2026:** pedidos do mesmo grupo na mesma data formam um evento único e seus valores elegíveis são somados por linha para o mínimo; pedidos de datas diferentes não se acumulam.
- Evento de expansão confirmado: primeira compra da linha pelo grupo comercial no histórico, atingindo o mínimo próprio da linha. Cada linha elegível gera 10 XP; Hydrofix + Suporte elegíveis geram 20 XP. A linha não pontua novamente em compras posteriores, mesmo se a primeira ficou abaixo do mínimo.
- Como diferenciar ausência de compra de histórico indisponível na proposta: com grupo identificado e consulta válida ao histórico desde 2022, a ausência de compra anterior atende ao critério de novidade. Falha de consulta, grupo pendente ou datas históricas ausentes continuam como pendência, sem interpretar dado indisponível como ausência de compra. A necessidade de histórico anterior a 2022 foi resolvida pela confirmação do usuário.

## Correspondência dos produtos

| Produto citado no regulamento | Código(s) ou família na base | Observações |
| --- | --- | --- |
| Hydrofix | `002920` — HYDROFIX AF; `002921` — HYDROFIX AQ | Códigos fornecidos pelo usuário e conferidos no Supabase em 10/09/2026. Ambos pertencem ao grupo Hydrofix para apurar o mínimo por pedido. |
| Grelha + Porta Grelha / Grelha e Porta grelha | `002968` — KIT GRELHA E PORTA GRELHA DN100; `002969` — KIT GRELHA E PORTA GRELHA DN150 | Kits fornecidos pelo usuário e conferidos no Supabase em 10/09/2026. Ambos pertencem ao grupo Grelha + Porta Grelha para apurar o mínimo por pedido. |
| Suporte de Bancada | `001626`, `001627`, `001628`, `002054`, `002055`, `002056`, `002064`, `002065`, `002066`, `002893`, `002894`, `002895`, `002917`, `002918`, `002919`, `003026`, `003027` | 17 códigos fornecidos pelo usuário e conferidos no Supabase em 10/09/2026. Descrições em [produtosMix.csv](produtosMix.csv). Todos pertencem ao grupo Suporte de Bancada para apurar o mínimo por pedido. |
| CPP 009 | `000010` — CAIXA DE PASSAGEM POLAR SPLIT CPP 009; `002736` — CAIXA DE PASSAGEM POLAR SPLIT CPP 009 RV (M10) | Códigos fornecidos pelo usuário e conferidos no Supabase em 10/09/2026. Ambos pertencem ao grupo CPP 009 para apurar o mínimo por pedido. |

A correspondência está em [produtosMix.csv](produtosMix.csv), com 23 códigos únicos nos quatro grupos informados pelo usuário: 2 Hydrofix, 2 CPP 009, 2 kits Grelha + Porta Grelha e 17 Suportes de Bancada. Carregar `produto_id` como texto para preservar os zeros à esquerda. Produtos identificados fora da lista não pertencem ao mix mapeado; código ausente ou inválido gera pendência de identificação. Eventuais inclusões devem atualizar a lista e a versão da regra.

Na regra da campanha, “linha” corresponde ao `grupo_mix` desse mapeamento. Não depender da coluna física `dim_produto.linha_produto`, que estava nula nos códigos consultados. Consultar a novidade por `grupo_comercial_id` + `grupo_mix`, reunindo todos os códigos da linha e todos os clientes do grupo comercial.

**Mínimo em triangulações — confirmado pelo usuário em 14/09/2026:** considerar o valor total dos produtos da linha no mesmo pedido, antes da divisão entre vendedores. Na fonte, somar as alocações válidas e completas de representante e executivo para recompor esse total, conforme [Dados de vendas](dadoVenda.md). Exemplo confirmado: Hydrofix de R$ 3.000 em Construção atende ao mínimo com R$ 1.500 alocados a cada vendedor; cumpridas as demais condições, gera uma expansão de 10 XP, sendo 5 XP para cada participante.

Na consulta somente leitura de 10/09/2026, `002920` e `002921` foram encontrados com as descrições acima e `is_produto_elegivel_analise = true`. Ambos tinham `linha_produto` e `subfamilia` nulos, portanto o enquadramento deve usar os códigos explícitos. Nenhuma alteração foi feita no banco.

Para Construção, somar os valores de Hydrofix AF e AQ no mesmo pedido para comparar com o mínimo de R$ 3.000,00. Isso não exige comprar as duas variantes juntas. A novidade é avaliada pelo grupo Hydrofix; comprar AQ após já ter comprado AF não representa um novo grupo de mix.

Os códigos `000010` e `002736` também foram encontrados no Supabase em consulta somente leitura de 10/09/2026, com as descrições informadas, `is_produto_elegivel_analise = true` e `linha_produto`/`subfamilia` nulos. Usar os códigos explícitos para identificar CPP 009.

Para Canais, somar os valores das duas variantes de CPP 009 no mesmo pedido para comparar com o mínimo de R$ 2.200,00, sem exigir a presença de ambas. A novidade é avaliada pelo grupo CPP 009; adquirir a versão RV após já ter comprado a versão comum não representa expansão. Nenhuma alteração foi feita no banco.

Os kits `002968` e `002969` foram encontrados no Supabase em consulta somente leitura de 10/09/2026, com as descrições informadas, `is_produto_elegivel_analise = true` e `linha_produto`/`subfamilia` nulos. O vínculo deve usar os códigos explícitos de [produtosMix.csv](produtosMix.csv).

Somar os valores de DN100 e DN150 dentro do mesmo pedido para o mínimo de R$ 6.000,00 em Construção ou R$ 1.000,00 em Canais. Não é necessário comprar as duas medidas juntas: cada código identifica um kit de grelha e porta-grelha. Produtos avulsos não foram mapeados. A novidade é avaliada pelo grupo Grelha + Porta Grelha; trocar DN100 por DN150 não representa expansão. Nenhuma alteração foi feita no banco.

Os 17 códigos de Suporte de Bancada foram encontrados no Supabase em consulta somente leitura de 10/09/2026, com `is_produto_elegivel_analise = true` e `linha_produto`/`subfamilia` nulos. As descrições conferem com as informadas após normalizar espaços. Usar o código, pois existem descrições iguais em códigos diferentes; não eliminar esses códigos como duplicatas.

Somar os valores dos 17 códigos de Suporte de Bancada presentes no mesmo pedido para comparar com o mínimo de R$ 9.000,00 em Construção ou R$ 1.000,00 em Canais. Não exigir medidas ou versões diferentes juntas. A indicação `PAR` é parte da descrição do produto; não multiplicar nem dividir o valor de venda por dois por esse motivo. A novidade é avaliada pelo grupo Suporte de Bancada: qualquer compra anterior de um dos 17 códigos impede considerar uma nova medida ou versão como expansão. O usuário confirmou expressamente que trocar Suporte 300 por Suporte 500 não conta. Nenhuma alteração foi feita no banco.

## Amostra

Cole exemplos fictícios ou anonimizados de um cliente novo, um reativado e um existente que comprou produto novo.

```text
[PREENCHER]
```
