# Exceções, divergências e pendências

Este documento faz parte do produto: casos não resolvidos não devem ser transformados silenciosamente em zero, falso ou elegível.

## Exceções de negócio implementadas

| Caso | Comportamento atual |
| --- | --- |
| Pedido não comercial | Excluído por flags de venda/bonificação/remessa/transferência |
| Pedido cancelado | Depende de já estar marcado como item inválido/ausente na fonte elegível |
| Cliente bloqueado | Só a parte faturada participa |
| Quitação posterior | Como a view é corrente, o pedido volta integralmente pela data original quando deixa de estar bloqueado |
| Devolução maior que o valor elegível | Saldo do pedido é limitado a zero em vendas/novos/reativados |
| Dois vendedores | XP de novo, reativado e mix é dividido 50/50 |
| Mais de dois vendedores | Evento fica pendente e recebe zero XP |
| Segmentos divergentes | Evento fica pendente e recebe zero XP |
| Região sem meta positiva | Não participa; evento individual recebe zero se alguma região do evento não participar |
| Grupo KA | Só o mix é excluído; novos e reativados continuam possíveis |
| Primeira compra de mix abaixo do mínimo | Não pontua; compras posteriores não recuperam a novidade |
| Duas famílias novas no mesmo evento | Cada família é avaliada e pode gerar 10 XP |
| Fase posterior de adiantamento marcada sozinha | Aceita; checks são independentes |
| Correção de check | Pode desmarcar; cria nova versão e histórico |
| Meta futura ausente | Mês fica sem linha/check e o acumulado termina no último mês publicado |

## Divergências entre regra e implementação

### Alta prioridade

| Divergência | Regra documentada | Implementação atual | Risco |
| --- | --- | --- | --- |
| Apuração individual versus regional | PDF diz pontuação individual | painel soma tudo por região e classifica a região | prêmio pode ser associado à unidade errada |
| Exceções SMART PODS/MRV | não devem sofrer bloqueio por inadimplência | SQL bloqueia todo `cliente_loja_id` presente na view; não há exceção explícita | venda e XP podem ficar menores, salvo se a view já tratar isso |
| Bloqueio por grupo | regra fala em inadimplência do grupo comercial | junção efetiva usa cliente + loja | lojas do mesmo grupo podem receber tratamentos diferentes |
| Data final/aceite | fechamento na segunda semana de janeiro | não há data, responsável nem processo de congelamento | resultado oficial pode mudar sem rito de aprovação |

### Média prioridade

| Divergência | Regra/documentação | Implementação atual | Consequência |
| --- | --- | --- | --- |
| Grupo pendente visível | deveria permanecer pendente | grupo nulo/desconhecido é removido das consultas | usuário não enxerga a pendência no painel |
| Devolução sem vínculo em mix | falta de item deveria impedir conclusão segura | só devolução que consegue vínculo nota–pedido marca pendência | devolução não vinculável pode passar despercebida |
| Devolução não vinculável em novos/reativados | registrar pendência do evento afetado | o grupo inteiro é retirado da saída | perda de transparência e possível exclusão ampla |
| Estorno/refaturamento | pedido ativo deve permanecer único | não há regra explícita; depende da mart | comportamento não é comprovável pelo repositório |
| Teto nos detalhes | teto é por vendedor/campanha | detalhes e resumos mostram XP bruto; só visão consolidada limita | telas podem exibir totais diferentes sem coluna de excedente |
| Observação de adiantamento | contrato aceita justificativa | interface não permite editar observação | correção manual não recebe motivo pela UI |
| Histórico do adiantamento | histórico deve apoiar auditoria | banco grava, mas painel não consulta o histórico completo | auditoria exige acesso ao banco |
| Prêmio pelo budget | regulamento define valores condicionais | painel não calcula prêmio | usuário precisa interpretar manualmente |
| Contagem dos resumos | quantidade deveria deixar claro se mede evento confirmado | novos/reativados contam linhas retornadas mesmo com zero XP; mix conta somente XP positivo | quantidades entre páginas não têm a mesma semântica |

### Baixa prioridade ou técnica

| Divergência | Situação |
| --- | --- |
| Fuso de clientes/mix | usam `current_date` do banco; budget/vendas e UI usam America/Sao_Paulo |
| Status do refresh | consulta pega a linha mais recente por `atualizado_em`, sem exigir status concluído |
| Listas duplicadas | produtos, KA e editores estão repetidos em mais de um artefato e podem divergir |
| Data futura de checks | não há bloqueio por data; um editor pode confirmar mês futuro se a meta existir |
| Teto por `(região,vendedor)` | equivale ao teto global apenas sob a premissa de vínculo regional fixo |
| Budget negativo/superior a 100% | permitido no cálculo; somente a largura da barra é limitada |

## Limitações de auditoria

- O painel não mostra valor bruto, valor devolvido e valor líquido lado a lado para cada pedido.
- Não mostra itens cancelados ou operações não comerciais excluídas.
- Não mostra grupos sem identificação que ficaram fora da consulta.
- Não expõe fotografia histórica do ranking/XP.
- Não oferece exportação dedicada.
- Não mostra o excedente acima dos tetos de novos/reativados.
- Não registra qual versão do SQL estava instalada no momento de uma apuração.
- As prévias locais são antigas e não recebem atualização automática.
- Os CSVs/JSONs históricos com nomes e identificadores comerciais estão versionados no repositório; acesso, retenção e eventual anonimização precisam seguir a política interna de dados.

## Decisões ainda não definidas no repositório

| Decisão | Impacto |
| --- | --- |
| Quem aprova a apuração final | governança e aceite do pagamento |
| Dia/hora de corte na segunda semana de janeiro | reprodutibilidade do fechamento |
| Política para mudanças depois do aceite | necessidade de reabertura e trilha formal |
| Responsável operacional pelo dataflow e SLA de atualização | tratamento de dados desatualizados |
| Responsável por corrigir grupos, vendedores e segmentos | tempo de resolução de pendências |
| Regras adicionais de elegibilidade/pagamento | possíveis exclusões não codificadas |
| Necessidade e formato de exportação | auditoria e compartilhamento |
| Política de retenção/backup | recuperação de histórico e evidência |
| Se classificação/prêmio final é individual ou regional | desenho correto da consolidação |

## Premissas fortes

Estas premissas são necessárias para o resultado atual ser coerente:

- `is_item_valido_metricas` representa corretamente cancelamentos e demais invalidações.
- Valores em `fct_pedido_item` e `fct_faturamento_item` já estão alocados por vendedor e não devem ser divididos novamente.
- A dimensão de vendedor é estável durante a campanha.
- O histórico desde janeiro de 2022 é suficiente para declarar novidade.
- `nota_fiscal_id + vendedor` identifica um único pedido quando a devolução é abatida.
- `vw_clientes_inadimplentes` representa a situação corrente e, se necessário, já trata exceções não codificadas.
- A soma de linhas de `metas_comerciais` por região é a meta regional correta.
- Os códigos de produto, grupos KA, feriados e e-mails embutidos são a versão oficial vigente.

Se qualquer premissa falhar, o resultado precisa ser recalculado após a correção.

## Tratamento recomendado para dados incompletos

| Falha | Tratamento seguro |
| --- | --- |
| Grupo ausente/desconhecido | manter pendente e sem XP de novo/reativado/mix |
| Vendedor ausente | manter evento visível, pendente e com zero XP |
| Região/time ambíguo | manter pendente; não escolher arbitrariamente |
| Produto sem código | não classificar como fora do mix até corrigir identificação |
| Data histórica ausente | não concluir primeira compra ou inatividade |
| Devolução sem detalhe de produto | não concluir mínimo de mix |
| Meta ausente | não estimar nem copiar mês anterior |
| Falha de consulta | exibir erro; não transformar em lista vazia oficial |

Parte desses tratamentos recomendados ainda não aparece na interface, conforme as divergências acima.

## Critérios para encerrar as principais pendências

1. Decidir e implementar a unidade oficial de classificação/prêmio.
2. Comprovar onde SMART PODS/MRV são tratados ou adicionar regra explícita e teste.
3. Expor um relatório de pendências cadastrais e devoluções não vinculadas.
4. Definir corte, aprovador e política de reabertura da apuração final.
5. Mostrar XP bruto, teto, contabilizado e excedente por vendedor.
6. Permitir consultar o histórico de adiantamento e registrar observação.
7. Executar teste de integração no Supabase real com casos controlados.
