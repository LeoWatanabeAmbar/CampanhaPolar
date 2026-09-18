# Regras de negócio consolidadas

## Objetivo e unidade de acompanhamento

O painel acompanha a campanha XP Polar de setembro a dezembro de 2026. O regulamento declara pontuação individual; a implementação atual agrega os XP individuais dos vendedores por região e soma a eles os indicadores regionais de vendas e adiantamento. Por isso, a classificação exibida atualmente é uma **classificação regional**, não uma apuração individual de prêmio. Essa diferença está registrada como divergência.

Há cinco indicadores:

| Indicador | Unidade do evento | Titular do XP | XP | Teto |
| --- | --- | --- | ---: | ---: |
| Cliente novo | Grupo comercial + primeira data elegível | Vendedor | 10 por evento | 100 por vendedor/campanha |
| Cliente reativado | Grupo comercial + data de retorno | Vendedor | 8 por evento | 80 por vendedor/campanha |
| Expansão de mix | Grupo comercial + família + primeira data | Vendedor | 10 por família | Sem teto |
| Venda no quadrimestre | Região | Região | Pela faixa de atingimento | Sem teto |
| Adiantamento | Região + competência + fase | Região | 10 por check confirmado | 30/mês e 120/campanha |

Quando um evento individual tem exatamente dois vendedores identificados, o XP é dividido igualmente. O valor monetário não é redistribuído por essa regra: ele permanece conforme as alocações da fonte.

## Período, referência e participantes

- Período dos eventos da campanha: de 01/09/2026, inclusive, a 31/12/2026, inclusive.
- Histórico aceito para novidade e inatividade: a partir de 01/01/2022.
- Data do pedido: `fct_pedido_item.data_emissao`, tratada como data de implantação.
- Participa, em cada competência, a região com meta positiva em `metas_comerciais` e time `Canais`, `Time Norte` ou `Time Sul`.
- `Time Norte` e `Time Sul` pertencem ao segmento Construção; `Canais` pertence ao segmento Canais.
- Região sem linha de meta ou com meta menor ou igual a zero não participa naquela competência.
- Não há proporcionalização de teto para admitidos ou desligados. O histórico elegível permanece.
- O vínculo vendedor–região é tratado como fixo durante a campanha. Um vendedor com mais de uma região ou time no cadastro fica sem mapeamento único.

## Venda elegível

Um item/pedido entra na base analítica quando atende simultaneamente aos filtros abaixo:

- `is_item_valido_metricas = true` quando a fonte usada possui esse campo;
- `is_venda_comercial = true`;
- não é bonificação;
- não é remessa;
- não é transferência de mercadoria;
- tem data dentro da janela consultada;
- não foi removido da fonte elegível por cancelamento.

### Inadimplência

A regra pretendida é aplicar o bloqueio financeiro ao grupo, com exceção de SMART PODS e MRV. Para um cliente bloqueado, somente a parte faturada participa. Após quitação, a situação corrente deixa de bloqueá-lo e o pedido volta pela data original.

O SQL atual identifica bloqueio por `cliente_loja_id` em `vw_clientes_inadimplentes` e usa `fct_faturamento_item.valor_bruto_item` para a parte faturada. As exceções SMART PODS/MRV não aparecem explicitamente no SQL do projeto; portanto, dependem de já estarem excluídas da view ou ainda precisam ser implementadas.

### Devoluções

- Budget anual: subtrai todas as devoluções com `data_devolucao` em 2026 até a data corrente, sem exigir vínculo com pedido de 2026.
- Venda regional, novos e reativados: a devolução é vinculada por nota fiscal original + vendedor e somente quando a nota aponta para um único pedido. O valor é abatido do pedido, limitado a saldo mínimo zero.
- Mix: como a devolução não informa produto/item, qualquer devolução vinculada ao pedido torna o evento de mix pendente e gera zero XP.
- Devolução não vinculável é ignorada na venda regional; em novos e reativados, um grupo com devolução não vinculável é excluído do resultado; no mix, somente devoluções vinculadas são detectadas.

### Estorno e refaturamento

A regra de negócio pretende manter um pedido ativo na competência de implantação, sem duplicá-lo quando houver refaturamento. O SQL depende do conteúdo já tratado de `fct_faturamento_item`; não existe lógica explícita no repositório para reconhecer estorno de nota.

## Evento diário e atribuição

Para clientes novos e reativados, todos os pedidos elegíveis do mesmo grupo comercial e mesma data formam um evento. Para mix, a chave inclui também a família do produto.

O evento só recebe XP quando:

- o grupo comercial é identificado e existe em `dim_grupo_comercial`;
- há exatamente um ou dois vendedores distintos;
- nenhum vendedor está ausente;
- cada vendedor possui região e time com mapeamento único;
- todos os vendedores têm o mesmo segmento de campanha;
- todas as regiões envolvidas possuem meta positiva na competência.

Com um vendedor, ele recebe 100% do evento. Com dois, cada um recebe 50%. Zero, três ou mais vendedores deixam a atribuição pendente e o XP fica em zero.

## 1. Clientes novos

Um grupo é novo quando seu primeiro evento elegível desde 01/01/2022 ocorre durante a campanha.

Regras efetivas:

- a identidade é o `grupo_comercial_id`, reunindo clientes e lojas;
- vários pedidos na primeira data formam um único evento;
- o evento gera 10 XP, dividido entre um ou dois vendedores;
- grupos com data histórica ausente ou devolução não vinculável são retirados do resultado;
- grupo ausente ou desconhecido não aparece na página, em vez de aparecer como pendência;
- o teto de 100 XP é aplicado por vendedor apenas ao montar a Visão geral/Análise individual; a página de detalhe mostra XP bruto.

Exemplos:

| Situação | Resultado |
| --- | --- |
| Primeiro evento do grupo com um vendedor | 10 XP para o vendedor |
| Primeiro evento com dois vendedores | 5 XP para cada |
| 12 eventos integrais para o mesmo vendedor | 120 XP bruto; 100 XP na consolidação |
| Grupo sem cadastro válido | Não aparece na consulta atual |

## 2. Clientes reativados

Um grupo é reativado quando existe evento anterior elegível e o intervalo mínimo foi cumprido:

- Canais: pelo menos 6 meses de calendário;
- Construção: pelo menos 12 meses de calendário.

A comparação é inclusiva. O dia exato em que se completam 6 ou 12 meses já é elegível. A última compra vem do evento diário imediatamente anterior na sequência do grupo.

Regras efetivas:

- somente a primeira reativação candidata da campanha é selecionada quando a página carrega a campanha inteira;
- o evento gera 8 XP: 8 para um vendedor ou 4 para cada um de dois vendedores;
- o teto de 80 XP é aplicado somente na consolidação da Visão geral/Análise individual;
- as mesmas condições de grupo, dados pendentes, participação e devoluções de clientes novos se aplicam.

## 3. Expansão de mix

A expansão é a primeira compra histórica de uma família mapeada pelo grupo comercial. A primeira compra precisa ocorrer na campanha e alcançar o mínimo no próprio evento diário. Uma compra anterior da família, ainda que abaixo do mínimo, impede XP posterior.

### Famílias e mínimos

| Segmento | Família | Mínimo |
| --- | --- | ---: |
| Construção | Hydrofix | R$ 3.000 |
| Construção | Grelha + Porta Grelha | R$ 6.000 |
| Construção | Suporte de Bancada | R$ 9.000 |
| Canais | Suporte de Bancada | R$ 1.000 |
| Canais | Grelha + Porta Grelha | R$ 1.000 |
| Canais | CPP 009 | R$ 2.200 |

O mapeamento contém 23 códigos: 2 Hydrofix, 2 CPP 009, 2 kits Grelha + Porta Grelha e 17 Suportes de Bancada. A lista efetiva está embutida em `sql/mix_produtos.sql` e duplicada em `docs/dados/produtosMix.csv`.

### KA

Os 16 grupos de `docs/dados/gruposKA.csv` não pontuam mix. A lista é fixa para a campanha e também está embutida no SQL. Ser KA não exclui clientes novos nem reativados.

### Ordem dos motivos exibidos

Quando mais de uma condição se aplica, o SQL escolhe o primeiro motivo desta ordem:

1. cliente KA;
2. data histórica ausente;
3. família comprada anteriormente;
4. devolução na nota do pedido;
5. família fora do segmento;
6. valor abaixo do mínimo;
7. vendedor ausente;
8. quantidade de vendedores diferente de um ou dois;
9. região ou segmento sem mapeamento único;
10. segmentos divergentes;
11. região sem meta;
12. elegível integral ou 50/50.

Cada família elegível gera 10 XP. Famílias distintas no mesmo dia podem gerar XP independentes. O indicador não tem teto.

## 4. Adiantamento de meta

O adiantamento não é calculado pelas vendas. É uma confirmação manual, por região e mês, das fases:

- 1ª semana / 32%: 10 XP;
- 2ª semana / 56%: 10 XP;
- 3ª semana / 80%: 10 XP.

As fases são independentes. Marcar 80% não marca 32% nem 56%. Um check desmarcado significa “não confirmado” e pode representar tanto não atingimento quanto ausência de registro; a versão distingue linhas salvas de linhas ainda não gravadas.

O limite natural da estrutura é 30 XP por mês e 120 XP nos quatro meses. O painel não bloqueia datas, não confere os percentuais e permite desmarcar correções. Só regiões com meta positiva aparecem.

As observações existem no banco e no contrato, mas a interface atual não oferece campo para editá-las; ela apenas preserva o valor recebido.

## 5. Venda no quadrimestre

O SQL retorna meta e realizado por região/competência. O Python acumula:

`meta_acumulada_ate_data = metas integrais dos meses encerrados + meta proporcional do mês atual`

`atingimento = 100 × realizado acumulado / meta_acumulada_ate_data`

Para o mês atual:

`meta_diaria = meta_mes / dias_uteis_mes`

`meta_parcial = meta_diaria × dias_uteis_decorridos`

São dias úteis as segundas a sextas, menos os feriados nacionais cadastrados para setembro a dezembro de 2026. O dia de referência conta como decorrido quando é útil.

| Atingimento exato | XP |
| --- | ---: |
| Menor que 60% | 0 |
| 60% a menos de 70% | 100 |
| 70% a menos de 80% | 200 |
| 80% a menos de 90% | 350 |
| 90% a menos de 100% | 450 |
| 100% a menos de 110% | 500 |
| 110% a menos de 120% | 550 |
| 120% a menos de 130% | 600 |
| 130% a menos de 140% | 650 |
| A partir de 140% | 650 + 50 por bloco completo de 10 pontos acima de 130% |

O percentual exato define a faixa; o arredondamento de uma casa é somente visual. Exemplos: 109,999% = 500 XP; 110% = 550; 135% = 650; 140% = 700.

Se a meta do mês atual não estiver publicada, a tela usa os meses disponíveis e avisa que o acumulado termina no último mês com dados. Não soma fotografias mensais de XP: recalcula uma única pontuação sobre o acumulado.

## Budget anual

- Budget fixo no código Python: R$ 119.000.000.
- Período do realizado: pedidos de 01/01/2026 até a data corrente.
- Base: valor bruto de itens comerciais válidos, sem bonificações, remessas ou transferências.
- Inadimplência não reduz o budget.
- Abatimento: todas as devoluções ocorridas em 2026 até a data corrente, mesmo que a venda original seja de outro ano ou não possa ser vinculada.
- Percentual: `100 × realizado / 119.000.000`.
- A barra visual é limitada entre 0% e 100%, mas o percentual textual pode ficar abaixo de zero ou acima de 100%.

## Classificações e prêmios

| Classificação | XP | Prêmio se o budget validar integralmente a campanha |
| --- | ---: | --- |
| Sem classificação | abaixo de 370 | Sem prêmio definido |
| Bronze | 370–500 | Vale Flash de R$ 100 |
| Prata | 501–800 | Vale Flash de R$ 200 |
| Ouro | 801–1.039 | Vale Flash de R$ 500 |
| Diamante | 1.040–1.200 | R$ 7.500 em PIX |
| Polar | 1.201 ou mais | R$ 15.000 em PIX |

Validação pelo budget:

| Atingimento anual | Efeito regulatório |
| --- | --- |
| Abaixo de 90% | Campanha sem pagamento |
| 90% a 94,99% | Apenas Diamante recebe R$ 1.000 e Polar recebe R$ 2.000 |
| 95% ou mais | Prêmio integral do nível |

O painel atual não calcula prêmio. Ele mostra o budget e a classificação regional separadamente.
