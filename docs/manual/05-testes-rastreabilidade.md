# Testes e rastreabilidade

## Estado da validação

Em 18/09/2026, a suíte local executou com sucesso:

```text
106 passed
```

Comando:

```powershell
python -m pytest -q
```

O pytest não está em `requirements.txt`; para um ambiente novo, instale separadamente:

```powershell
python -m pip install "pytest>=8,<9"
```

## Cobertura por arquivo

| Arquivo | Área coberta |
| --- | --- |
| `test_autenticacao.py` | chave publicável, login, erro genérico, renovação, logout e tela |
| `test_atualizacao.py` | escolha do refresh, fallback e conversão de fuso |
| `test_budget.py` | contrato, regra anual, retirada da inadimplência e devoluções de 2026 |
| `test_vendas.py` | dias úteis, meses acumulados, limites de XP, cálculo, RPC e página |
| `test_clientes_novos.py` | competência, SQL, página, resumo e triangulação |
| `test_clientes_reativados.py` | competência, prazos, SQL, página e resumo |
| `test_mix_produtos.py` | competência, erros de API, listas/mínimos, devolução, página e resumo |
| `test_adiantamento.py` | autorização, cinco editores, validação, histórico, conflito, transação e UI |
| `test_visao_geral.py` | consolidação, tetos, classificação, ordenação e budget |
| `test_analise_individual.py` | seleção regional, composição e tabelas de detalhe |

## Matriz regra → implementação → teste

| Regra | Implementação principal | Evidência automatizada |
| --- | --- | --- |
| 60/70/80/90/100/110/120/130/140% | `polar/vendas.py:sales_xp` | `test_sales_xp_uses_exact_confirmed_boundaries` |
| Dias úteis e feriado nacional | `polar/vendas.py:working_days` | `test_september_working_days_include_reference_and_exclude_national_holiday` |
| Acumulado até o mês atual | `calculate_cumulative_region_results` | teste de outubro acumulado |
| Budget R$ 119 milhões | `polar/budget.py` | teste do repositório e cartão |
| Budget sem inadimplência | `sql/budget_anual.sql` | teste textual do SQL |
| Todas as devoluções de 2026 no budget | SQL e migration | teste textual da função/migration |
| Novo desde 2022 | `sql/clientes_novos.sql` | teste textual e teste de página |
| Reativação 6/12 meses | `sql/clientes_reativados.sql` | teste textual de intervalos e `lag` |
| 23 produtos e mínimos | `sql/mix_produtos.sql` | teste textual de códigos/mínimos |
| 16 KA | `sql/mix_produtos.sql` | teste da presença da CTE KA |
| Divisão 50/50 | SQL de novos/reativados/mix | testes textuais e resumos |
| Tetos 100/80 | `app.py:indicator_xp_by_region` | teste da Visão geral |
| Classificações | `app.py:campaign_classification` | teste parametrizado de limites |
| Checks independentes | `polar/adiantamento.py` + SQL | testes de salvar/desmarcar |
| Concorrência otimista | função SQL e repositório | teste de rollback em conflito |
| Cinco editores | Python + SQL | testes da allowlist/migration |
| Segurança das RPCs | SQL | testes de `security definer`, search path e grants |

## O que os testes não comprovam

- Não conectam ao projeto Supabase real.
- Não executam PostgreSQL; vários testes apenas procuram trechos no texto SQL.
- Não validam plano de execução, índices, volume real ou timeout.
- Não comprovam RLS/grants efetivamente instalados.
- Não validam os valores atuais das tabelas comerciais.
- Não comprovam cancelamentos, estornos e refaturamentos de ponta a ponta.
- Não comprovam as exceções SMART PODS/MRV.
- Não testam diferenças de fuso perto da meia-noite entre banco e São Paulo.
- Não comparam o resultado completo com uma fonte oficial aprovada.
- Não testam cálculo de prêmio, pois ele não existe no painel.

## Checklist de aceite funcional

### Autenticação e acesso

- [ ] chave secreta é rejeitada;
- [ ] conta comum entra e apenas consulta;
- [ ] cada uma das cinco contas editoras salva;
- [ ] conta não autorizada não grava nem chamando a RPC diretamente;
- [ ] logout revoga a sessão local;
- [ ] sessão expirada retorna ao login sem expor detalhes.

### Dados e regras

- [ ] meta regional soma corretamente linhas duplicadas esperadas;
- [ ] região sem meta não aparece;
- [ ] venda normal usa valor bruto alocado;
- [ ] bloqueado usa apenas faturado;
- [ ] SMART PODS e MRV têm resultado confirmado;
- [ ] devolução parcial e total recalculam o pedido original;
- [ ] devolução sem vínculo aparece em relatório de pendência;
- [ ] pedido cancelado desaparece do histórico elegível;
- [ ] refaturamento não duplica a venda;
- [ ] triangulação preserva valor monetário e divide apenas XP do evento;
- [ ] primeiro pedido abaixo do mínimo impede mix posterior;
- [ ] grupo KA não pontua mix e pode pontuar novo/reativado;
- [ ] igualdade exata a 6/12 meses pontua reativação;
- [ ] tetos mostram bruto, contabilizado e excedente.

### Fechamento

- [ ] metas dos quatro meses estão publicadas;
- [ ] feriados usados foram aprovados;
- [ ] data/hora de corte foi registrada;
- [ ] versão do código e das funções SQL foi registrada;
- [ ] fotografia dos dados e resultados foi preservada;
- [ ] divergências foram resolvidas ou aceitas formalmente;
- [ ] aprovador final assinou/registrou o aceite;
- [ ] prêmio foi calculado na unidade oficialmente decidida.

## Testes de integração recomendados

Criar em ambiente controlado ao menos um caso para cada cenário:

1. venda normal com um vendedor;
2. triangulação entre duas regiões e dentro da mesma região;
3. bloqueio, faturamento parcial e quitação;
4. SMART PODS/MRV bloqueados;
5. cancelamento depois de pontuar;
6. devolução parcial, total, sem vínculo e em pedido de mix;
7. estorno com refaturamento;
8. novo + mix no mesmo evento;
9. reativação exatamente no limite;
10. três vendedores ou segmento divergente;
11. disputa de edição do adiantamento;
12. mês futuro sem meta e depois com meta publicada.

Para cada caso, comparar fonte, retorno da RPC, valor mostrado, XP bruto, teto, XP contabilizado e classificação.

## Rastreabilidade documental

| Tema | Documento detalhado |
| --- | --- |
| Regulamento | `docs/contexto/RegrasPolar.pdf` |
| Decisões da campanha | `docs/regras/regrasCampanha.md` |
| Interpretação de dados | `docs/regras/regraNegocio.md` |
| Vendas e campos | `docs/dados/dadoVenda.md` |
| Metas e calendário | `docs/dados/dadoMeta.md`, `calendarioCampanha.md` |
| Financeiro e devoluções | `docs/dados/elegibilidadeVendas.md` |
| Clientes/mix | `docs/dados/dadoCliente.md`, `dadoEnquadramento.md` |
| KA e produtos | `docs/dados/dadoKA.md`, `produtosMix.csv` |
| Adiantamento | `docs/dados/dadoAdiantamento.md` |
| Deploy | `docs/arquitetura/deployStreamlitCloud.md` |

## Regra de manutenção da documentação

Toda mudança de regra deve alterar, no mesmo pull request ou entrega:

1. o manual consolidado;
2. o SQL/Python executável;
3. ao menos um teste de limite ou regressão;
4. a migration, quando o ambiente existente precisar dela;
5. o checklist/registro da versão instalada.
