# Regras da campanha XP Polar

Fonte: [RegrasPolar.pdf](../contexto/RegrasPolar.pdf), páginas 1 a 3. As transcrições abaixo não resolvem ambiguidades do regulamento; as dúvidas estão indicadas para preenchimento.

## Período e elegibilidade

**Conforme PDF:** campanha de setembro a dezembro, com fechamento e apuração final na segunda semana de janeiro. Pontuação individual e acumulativa.

- Ano da campanha: 2026, conforme recorte de pedidos indicado pelo usuário em 10/09/2026.
- Início do recorte: 01/09/2026; proposta inclui esse dia. Fim em 31/12/2026 conforme quadrimestre do PDF; data exata de fechamento a confirmar.
- Data de apuração dos pedidos: **confirmada pelo usuário em 14/09/2026**, emissão = implantação do pedido, no campo `data_emissao`. Essa data determina a inclusão no recorte e na competência mensal.
- Participantes elegíveis: **confirmado pelo usuário em 14/09/2026**, regiões de Canais e Construção com meta válida cadastrada na competência. Na fonte, Canais corresponde ao time `Canais` e Construção corresponde a `Time Norte` e `Time Sul`. Considerar meta válida quando `metas_comerciais.meta > 0`; linha ausente ou meta zerada não habilita a região naquela competência. Os vendedores vinculados à região elegível participam dos indicadores individuais, sujeitos às demais regras.
- Mudança de região: **confirmado pelo usuário em 14/09/2026**, os vendedores não mudarão de região durante a campanha. Usar o vínculo regional fixo descrito em [Dados de metas](../dados/dadoMeta.md).
- Admitidos e desligados: **confirmado pelo usuário em 14/09/2026**, calcular normalmente os XP das vendas elegíveis atribuídas a cada vendedor no período em que ele participar. Não proporcionalizar os pontos, mínimos ou tetos pelo número de meses disponíveis e não projetar pontuação para completar quatro meses. O vendedor desligado mantém os XP já apurados e continua visível no histórico; o admitido começa a acumular quando surgirem vendas elegíveis. O menor tempo de campanha apenas reduz sua oportunidade prática de atingir os máximos.

**Elegibilidade dos pedidos confirmada em 14/09/2026:** um pedido cancelado equivale a um pedido excluído e deixa integralmente de ser uma venda válida. Ele sai do realizado, do histórico de compras elegíveis e de todos os XP; pedidos posteriores e totais afetados são recalculados como se ele nunca tivesse participado. Pedidos de clientes bloqueados por inadimplência do grupo só participam pela parte já faturada. SMART PODS e MRV são exceções ao bloqueio, conforme o Gestão Comercial. Quando a dívida for quitada durante a campanha, o saldo em aberto volta a participar pela data original de implantação, recalculando as competências e os XP afetados. Aplicar os demais critérios também às exceções. Detalhes e fontes em [Elegibilidade de vendas](../dados/elegibilidadeVendas.md).

**Histórico sob inadimplência confirmado em 14/09/2026:** pedido bloqueado e não faturado não conta como compra anterior para novos, reativados ou mix. Em faturamento parcial, somente os itens e quantidades faturados entram no histórico. Após quitação, reintegrar a parte em aberto na ordem cronológica de sua implantação original e recalcular os eventos posteriores afetados.

**Devoluções confirmadas em 14/09/2026:** considerar todas as devoluções, sem filtro por setor responsável, motivo, submotivo, tipo ou outra classificação. Abater somente o valor devolvido da competência original de implantação e recalcular os XP afetados. Devolução parcial preserva o saldo líquido elegível; devolução total pode remover o evento original e alterar a classificação de pedidos posteriores. Em triangulações, usar a alocação regional da devolução sem nova divisão. A identificação da linha devolvida para o mix depende de detalhe por produto/item, conforme [Elegibilidade de vendas](../dados/elegibilidadeVendas.md).

**Operações não comerciais confirmadas em 14/09/2026:** bonificações, remessas e transferências de mercadoria não compõem vendas, histórico de compras elegíveis nem XP de qualquer indicador. Selecionar somente operações com `is_venda_comercial = true` e excluir registros marcados como `is_bonificacao`, `is_remessa` ou `is_transferencia`. Essa transferência é uma classificação da operação de mercadoria e não se confunde com o vínculo regional fixo dos vendedores.

**Estorno de nota fiscal confirmado em 14/09/2026:** se o pedido continuar ativo para refaturamento, ele permanece como venda válida na competência de implantação original. O estorno da nota não cancela o pedido, e a nota emitida no refaturamento não gera uma segunda venda nem transfere o evento para sua data de emissão. Para cliente bloqueado por inadimplência, a parcela elegível continua limitada ao faturamento válido: a nota estornada deixa de comprovar faturamento até que exista uma nova nota válida.

**Apuração dinâmica confirmada em 14/09/2026:** considerar sempre a situação atual das fontes. Qualquer mudança relevante recalcula as competências, sequências históricas e XP afetados, inclusive após uma apuração ou fechamento anterior. Manter fotografias e motivos para auditoria, mas apresentar como resultado oficial o cálculo mais recente. Os checks manuais de adiantamento permanecem como foram salvos até uma edição autorizada.

## 1. Clientes novos

**Conforme PDF:** primeira compra durante a campanha; 10 XP por cliente, limitados a 100 XP.

- Como comprovar a primeira compra: **confirmado pelo usuário em 14/09/2026**, o histórico disponível desde janeiro de 2022 em `comercial_marts.fct_pedido_item` é suficiente. Verificar ausência de compra anterior do grupo comercial nesse histórico, incluindo pedidos já realizados na campanha. Não exigir histórico anterior a 2022.
- Data considerada para a compra: **confirmada pelo usuário em 14/09/2026**, `data_emissao` corresponde à implantação do pedido e é a referência para a campanha. As demais condições de elegibilidade estão em [regraNegocio.md](regraNegocio.md).
- Regras adicionais de elegibilidade: grupo comercial identificado; pedido comercial válido e não cancelado; regra financeira atendida; atribuição do vendedor definida. Grupo pendente aguarda correção cadastral. Cliente bloqueado por inadimplência só pontua pela parte faturada, salvo SMART PODS/MRV; após quitação, o saldo volta pela implantação original.

## 2. Clientes reativados

**Conforme PDF:** 8 XP por cliente, limitados a 80 XP. Inatividade mínima de 1 ano para Construção e 6 meses para Canais.

- Como medir a inatividade, incluindo o dia limite: **confirmado pelo usuário em 14/09/2026**, a reativação vale no dia em que se completam exatamente 6 meses sem compras em Canais ou 12 meses em Construção. Considerar a última compra válida do grupo comercial anterior ao evento analisado, incluindo compras já realizadas na campanha. Usar meses de calendário e comparação inclusiva, sem aproximar os prazos por 180 ou 365 dias. Na referência confirmada por emissão/implantação: `data_ultima_compra_anterior <= data_emissao - intervalo_exigido`.
- Quantas vezes o mesmo grupo pode pontuar: no máximo uma reativação durante a campanha. Cada compra válida reinicia a contagem de inatividade e, entre setembro e dezembro, não há tempo para completar novamente os 6 meses de Canais ou os 12 meses de Construção.

## 3. Expansão de mix

**Conforme PDF:** 10 XP por cliente elegível, sem limite de XP. Clientes KA não pontuam neste indicador.

**Confirmado pelo usuário:** clientes novos e existentes podem pontuar quando compram produto novo.

**Detalhamento confirmado pelo usuário:** a expansão é a primeira compra de uma linha pelo grupo comercial em todo o histórico consultado, atingindo o mínimo dessa linha no próprio pedido. Cada combinação de grupo comercial e linha elegível gera 10 XP uma única vez. Hydrofix e Suporte de Bancada são duas linhas independentes: se ambas cumprirem suas condições, geram duas expansões e 20 XP, inclusive se estiverem no mesmo pedido. KA continua excluído e o indicador não tem teto de XP por vendedor.

**Lista KA fixa confirmada em 14/09/2026:** usar os 16 grupos definidos para todas as competências da campanha. Não haverá mudança de um grupo para KA ou saída da classificação durante o período; divergências em outra fonte ficam pendentes para correção e não alteram a lista desta campanha.

| Segmento | Produto conforme PDF | Venda mínima |
| --- | --- | ---: |
| Construção | Hydrofix | R$ 3.000,00 |
| Construção | Grelha + Porta Grelha | R$ 6.000,00 |
| Construção | Suporte de Bancada | R$ 9.000,00 |
| Canais | Suporte de Bancada | R$ 1.000,00 |
| Canais | Grelha e Porta grelha | R$ 1.000,00 |
| Canais | CPP 009 | R$ 2.200,00 |

- Os mínimos se aplicam à primeira compra da linha pelo grupo comercial, tanto para clientes novos quanto existentes.
- O mínimo é apurado em um único evento de compra. **Confirmado pelo usuário em 14/09/2026:** pedidos do mesmo grupo comercial no mesmo dia são tratados como um só evento e seus valores elegíveis são somados por linha de mix. Não acumular pedidos de dias diferentes.
- **Triangulações — confirmado pelo usuário em 14/09/2026:** o mínimo considera o valor total da linha no pedido antes da divisão entre vendedores. R$ 3.000 de Hydrofix em Construção atende ao mínimo mesmo com R$ 1.500 alocados a cada vendedor. Cumpridas as demais condições de mix, o evento gera 10 XP, sendo 5 XP para cada um dos dois participantes.
- Cada linha é avaliada separadamente. Não é necessário combinar linhas; o valor de uma linha não completa o mínimo de outra.
- Pontuação: 10 XP por linha nova elegível para o grupo comercial, sem repetir a mesma linha. Duas linhas novas elegíveis geram 20 XP; não limitar a uma expansão por grupo comercial.
- Novidade por grupo de mix: consultar se o grupo comercial já comprou qualquer código do grupo avaliado (Hydrofix, CPP 009, Grelha + Porta Grelha ou Suporte de Bancada). Trocar medida ou versão dentro do mesmo grupo de mix não conta; o usuário confirmou o exemplo de Suporte 300 para Suporte 500. **Confirmado pelo usuário em 14/09/2026:** o histórico disponível desde janeiro de 2022 é suficiente para verificar a primeira compra da linha; não exigir consulta a períodos anteriores a 2022.
- Grelha e porta-grelha: os códigos fornecidos pelo usuário são kits DN100 (`002968`) e DN150 (`002969`). Somar os valores dos kits no mesmo pedido, sem exigir as duas medidas juntas; produtos avulsos não foram mapeados.

Uma compra anterior da mesma linha impede a novidade, mesmo se ocorreu abaixo do mínimo ou antes da campanha. Assim, se o primeiro evento diário da linha ficar abaixo do mínimo, um evento de data posterior não se torna uma primeira compra elegível. Somente pedidos do mesmo grupo e da mesma data são somados; dias diferentes não se acumulam.

## 4. Antecipação de pedidos

**Conforme PDF:** fases de 32%, 56% e 80%, com 10 XP por fase atingida e limite de 120 XP na campanha. O documento menciona etapas semanais e remete à campanha em vigor.

- **Regra confirmada pelo usuário em 14/09/2026:** em cada mês, cada região possui três checks: uma semana/32%, duas semanas/56% e três semanas/80%. As referências identificam as fases; não é necessário parametrizar as datas de encerramento nem calcular o resultado pelas vendas.
- **Comprovação manual:** somente `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech` podem preencher e salvar os checks por região/mês; os demais usuários podem visualizar. Considerações operacionais impedem confirmar as fases somente a partir das vendas.
- Reinício: mensal, com registros próprios para cada região e competência.
- **XP regional confirmado pelo usuário em 14/09/2026:** cada fase confirmada gera 10 XP para a região, até 30 XP no mês e 120 XP no acumulado da campanha. Mesmo com dois vendedores na região, registrar a pontuação uma única vez, sem rateio nem inclusão nos totais individuais. Essa definição substitui o teto anteriormente descrito como individual para antecipação.
- Os checks representam confirmações independentes; marcar uma fase posterior não confirma automaticamente as anteriores. `true` significa atingiu e `false` significa não atingiu. O lançamento pode registrar correções, com histórico. Não confundir a data de edição do check com a data em que a condição comercial foi cumprida.
- A informação manual salva é suficiente para o XP: cada `true` gera 10 XP regionais na fase. A tela não precisa validar data, percentual ou vendas para aceitar a decisão das contas autorizadas. Detalhes em [Dados de adiantamento](../dados/dadoAdiantamento.md).

## 5. Vendas: acompanhamento mensal e fechamento do quadrimestre

**Conforme PDF, para o fechamento:** XP pelo atingimento da meta acumulada de setembro a dezembro, sem limite de pontuação neste indicador.

**Acompanhamento durante o quadrimestre confirmado pelo usuário em 14 e 15/09/2026:** a meta de outubro só será conhecida em outubro; durante setembro, usar somente a parcela decorrida da meta de setembro. A partir de outubro, acumular a meta e o realizado integrais dos meses encerrados e adicionar o realizado e a meta proporcional do mês atual. Assim, em outubro, o denominador é `meta de setembro + meta parcial de outubro`, e o numerador é `vendas de setembro + vendas de outubro até a referência`. Esse atingimento acumulado determina os XP atuais de vendas.

**Valor do realizado confirmado pelo usuário em 14/09/2026:** usar o valor bruto dos pedidos, com referência em `fct_pedido_item.valor_bruto_total`, para comparar as vendas com a meta. A competência é determinada pela emissão/implantação do pedido. A atribuição monetária em triangulações e os demais critérios de elegibilidade seguem em [Regras de negócio](regraNegocio.md) e [Dados de vendas](../dados/dadoVenda.md).

**Rateio monetário confirmado pelo usuário em 14/09/2026:** seguir o dataflow e o Gestão Comercial: cada parcela já rateada compõe o realizado da região do respectivo vendedor. Pedido de R$ 10.000 em triangulação entre duas regiões gera R$ 5.000 em cada; se ambos os participantes forem da mesma região, somar as parcelas e registrar R$ 10.000 nela. Não dividir novamente os valores da fonte. O rateio monetário não altera a meta integral de cada região nem distribui seus XP de vendas aos vendedores.

**Apuração regional confirmada pelo usuário em 14/09/2026:** considerar meta e vendas por região. Mesmo quando dois vendedores aparecerem na mesma região no mês, manter uma única meta regional integral e somar as vendas atribuídas à região. Calcular a meta parcial, o atingimento e a faixa de XP nesse grão. **O usuário confirmou que os XP de atingimento ficam na região**, sem distribuição aos vendedores e sem aplicação do rateio dos eventos de triangulação.

**Calendário confirmado:** segunda a sexta, descontando feriados nacionais. Fórmulas do mês atual: `meta_diaria = meta_mes / dias_uteis_mes` e `meta_parcial = meta_diaria * dias_uteis_decorridos`. No acumulado: `meta_acumulada_ate_data = soma_metas_meses_encerrados + meta_parcial_mes_atual` e `atingimento_acumulado_pct = 100 * realizado_acumulado / meta_acumulada_ate_data`. Aplicar as faixas abaixo a esse percentual exato. A data de referência entra nos dias decorridos quando for útil e não aparece também nos dias restantes. As condições de cálculo estão em [Dados de metas](../dados/dadoMeta.md) e [Calendário da campanha](../dados/calendarioCampanha.md).

**Correção confirmada pelo usuário em 14/09/2026:** a faixa de 550 XP começa em **110%**. O PDF apresenta `100%–119,99%`, sobrepondo a faixa de 500 XP. Com o uso do percentual exato também confirmado pelo usuário, essa faixa abrange de 110% até menos de 120%, incluindo valores como 119,999%.

| Atingimento exato da meta, com limites confirmados | XP |
| --- | ---: |
| De 0% a menos de 60% | 0 |
| De 60% a menos de 70% | 100 |
| De 70% a menos de 80% | 200 |
| De 80% a menos de 90% | 350 |
| De 90% a menos de 100% | 450 |
| De 100% a menos de 110% | 500 |
| De 110% a menos de 120% | 550 |
| De 120% a menos de 130% | 600 |
| De 130% a menos de 140% | 650 |
| A partir de 140% | 650 XP + 50 XP por bloco completo de 10 pontos percentuais acima de 130% |

**Confirmado pelo usuário em 14/09/2026:** acima de 130%, acrescentar 50 XP somente ao completar mais 10 pontos percentuais de atingimento, sem pontuação proporcional por bloco incompleto. Exemplos confirmados: 135% mantém 650 XP; 140% passa a 700 XP. Pela mesma regra, 150% corresponde a 750 XP, seguindo sem teto para este indicador.

Fórmula para atingimento `p >= 130`: `xp_vendas = 650 + 50 * floor((p - 130) / 10)`. Nessa expressão, `p` é o percentual exato na escala em que `140` significa `140%`, e `floor` mantém apenas os blocos completos, sem arredondar previamente o percentual.

**Precisão confirmada pelo usuário em 14/09/2026:** usar o percentual exato para definir os XP de vendas, sem arredondar ou truncar antes de comparar com os limites. Cada faixa inclui seu limite inicial e exclui o início da seguinte. Exemplo confirmado: 109,999% mantém 500 XP; somente ao atingir 110% passam a ser 550 XP. Da mesma forma, 139,999% mantém 650 XP e 140% passa a 700 XP. Na implementação, preservar a precisão decimal dos valores usados no cálculo; eventual formatação para exibição não deve alterar o enquadramento nem alimentar o cálculo de XP.

- Durante a campanha: acumular as competências decorridas e proporcionalizar somente a meta do mês atual pelos dias úteis. Não exigir nem estimar metas futuras; se a meta do novo mês ainda não estiver cadastrada, informar a indisponibilidade e manter o acumulado encerrado no último mês publicado.
- Recalcular os XP de vendas na data de referência; o resultado pode aumentar ou diminuir conforme o realizado, o avanço da meta parcial e mudanças posteriores de elegibilidade. Não somar fotografias diárias nem os XP dos meses para apurar o XP final do quadrimestre. O fechamento segue o atingimento acumulado previsto no PDF quando as metas dos quatro meses estiverem disponíveis, mas permanece sujeito ao recálculo pela situação atual das fontes.

## Unidades de apuração e limites de XP

**Triangulação — confirmado pelo usuário em 14/09/2026:** dividir igualmente os XP dos eventos elegíveis do pedido entre os dois vendedores, 50% para cada um. Clientes novos: 10 XP no evento, 5 para cada; reativados: 8 XP no evento, 4 para cada; mix: 10 XP por linha elegível, 5 para cada por linha. Um pedido elegível como novo e com uma expansão de mix gera 20 XP no total, sendo 5 XP de novo + 5 XP de mix para cada vendedor, antes dos respectivos tetos.

**Evento diário com pedidos de vendedores diferentes — confirmado pelo usuário em 14/09/2026:** se os pedidos elegíveis do mesmo grupo comercial e data reunirem exatamente dois vendedores identificados, aplicar o mesmo rateio de XP: metade para cada um. Com um vendedor identificado, atribuir o XP integral a ele. Manter o valor das vendas em cada pedido e região conforme as alocações originais; a divisão igual vale somente para os XP de novos, reativados e mix. Responsável ausente ou mais de dois vendedores exige conferência.

**Segmento confirmado pelo usuário em 14/09/2026:** os dois vendedores de uma triangulação pertencem sempre ao mesmo segmento. Usar o segmento comum, Construção ou Canais, para determinar os mínimos de mix e os prazos de reativação.

**Unidades confirmadas pelo usuário:** novos, reativados e mix são apurados por vendedor; antecipação e atingimento de vendas são apurados por região. Aplicar os tetos no acumulado da campanha da respectiva unidade, depois de identificar os eventos que efetivamente pontuam. O limite da campanha não se reinicia a cada pedido, mês, cliente, grupo de mix ou filtro do painel. Na antecipação, as três fases de cada mês permitem até 30 XP regionais e compõem o teto de 120 XP regionais da campanha.

| Tipo de regra | XP gerado conforme regra documentada | Teto na unidade de apuração | Situação |
| --- | --- | ---: | --- |
| Clientes novos | 10 XP por cliente elegível | 100 XP por vendedor | Limite informado no PDF |
| Clientes reativados | 8 XP por cliente elegível | 80 XP por vendedor | Limite informado no PDF |
| Expansão de mix | 10 XP por primeira compra elegível de linha pelo grupo comercial | Sem limite, por vendedor | Unidade de pontuação e ausência de teto confirmadas pelo usuário |
| Antecipação de pedidos | 10 XP por fase confirmada da região; até 30 XP no mês | 120 XP por região na campanha | XP vinculado à região, confirmado pelo usuário; conferência manual |
| Vendas | XP da região pela faixa do atingimento acumulado: meses encerrados integrais mais a parcela decorrida do mês atual | Sem limite, por região | XP vinculado à região, confirmado pelo usuário |

**Confirmado pelo usuário:** expansão de mix e venda no quadrimestre continuam sem teto, conforme o PDF. Registrar explicitamente essas regras como `sem_limite`; ausência de configuração não significa ausência de limite.

Para uma regra com teto definido: `xp_contabilizado = min(xp_gerado, limite_xp)`. Aqui, `xp_gerado` é o acumulado na unidade do indicador: vendedor em novos e reativados, já considerando sua metade nos eventos atribuídos a dois vendedores; região em antecipação, contando cada fase confirmada uma única vez por mês. **Confirmado pelo usuário em 14/09/2026:** os XP de indicadores diferentes podem ser somados, inclusive quando gerados pelo mesmo pedido. O total individual reúne somente os indicadores atribuídos ao vendedor, após seus respectivos limites; os XP de antecipação e de atingimento de vendas permanecem na região. Manter `xp_gerado`, `xp_contabilizado` e `xp_excedente` para explicar o resultado. Atingir o teto não torna os próximos pedidos inelegíveis; apenas limita o crédito de XP. Quando houver dois vendedores, o excedente permanece com seu vendedor e não aumenta a parcela do outro.

Exemplo confirmado: grupo novo que também cumpra os critérios de expansão de uma linha no mesmo pedido gera 10 XP de novo + 10 XP de mix = 20 XP. Com ambos os eventos atribuídos ao mesmo vendedor, o total é contabilizado integralmente se houver saldo de pelo menos 10 XP no teto de novos. Se esse teto já tiver sido atingido, o pedido acrescenta apenas os 10 XP de mix ao total individual. Antecipação e venda no quadrimestre continuam sendo apuradas conforme suas próprias regras, sem criar XP fixo adicional por pedido.

Para mix e venda no quadrimestre, `xp_contabilizado = xp_gerado` e `xp_excedente = 0`, depois de aplicar as regras de elegibilidade e cálculo de cada indicador. A ausência de teto não permite repetir o mesmo evento pontuável por item nem somar fotografias mensais do XP de atingimento acumulado.

Exemplo: 12 grupos comerciais novos elegíveis integralmente atribuídos ao mesmo vendedor geram 120 XP brutos, mas contabilizam 100 XP; os 20 XP excedentes continuam registrados para conferência. Isso não consome o limite de clientes reativados nem o de outro vendedor. Nas triangulações e nos eventos diários consolidados com exatamente dois vendedores identificados, cada grupo novo elegível atribui 5 XP a cada vendedor; 20 eventos assim atribuídos a um vendedor totalizam seu teto de 100 XP de novos. Casos com responsável ausente ou quantidade diferente de um ou dois vendedores permanecem pendentes.

## Níveis e prêmios

**Conforme PDF:**

| Nível | XP | Prêmio com campanha válida |
| --- | --- | --- |
| Bronze | 370–500 | Vale Flash de R$ 100,00 |
| Prata | 501–800 | Vale Flash de R$ 200,00 |
| Ouro | 801–1.039 | Vale Flash de R$ 500,00 |
| Diamante | 1.040–1.200 | Voucher de R$ 7.500,00 em PIX |
| Polar | 1.201 ou mais | Voucher de R$ 15.000,00 em PIX |

- Abaixo de 370 XP, o painel usa o rótulo operacional `Sem classificação`; essa faixa não constitui um nível ou prêmio adicional.
- Há condições adicionais para receber o prêmio: [PREENCHER]

## Validação pelo Budget Anual

**Conforme PDF:**

| Atingimento da empresa | Efeito nos prêmios |
| --- | --- |
| Abaixo de 90% | Campanha não válida para pagamento |
| De 90% a 94,99% | Somente Diamante recebe R$ 1.000,00 e Polar recebe R$ 2.000,00 |
| Igual ou superior a 95% | Prêmio correspondente ao nível atingido |

- Cálculo implementado em 16/09/2026: `100 * venda bruta elegível acumulada de 2026 / 119000000`, preservando a precisão no cálculo e arredondando somente a exibição.
- Durante a campanha, usar o realizado anual até a data, sem projeção.
- Responsável por confirmar a regra final: [PREENCHER]
