# Manual do projeto Campanha Polar

Este é o ponto de entrada da documentação vigente do projeto. O manual descreve o que o painel faz, como cada regra é calculada, quais dados utiliza, como é operado e quais limitações ainda existem.

Uma versão visual, navegável e pronta para impressão está disponível em [docs/projeto.html](../projeto.html).

## Escopo desta fotografia

- Código analisado: branch `main`, commit `b1e4ea5` de 16/09/2026.
- Documentação revisada em: 18/09/2026.
- Campanha: 01/09/2026 a 31/12/2026.
- Apuração final prevista no regulamento: segunda semana de janeiro de 2027; o dia e o responsável pelo aceite final ainda não estão definidos no repositório.
- Aplicação: painel Streamlit autenticado pelo Supabase.
- Validação local desta fotografia: 106 testes aprovados.

O manual documenta o repositório e não comprova que os scripts SQL já estejam instalados no projeto Supabase de produção. Essa confirmação exige acesso ao ambiente publicado.

## Como ler

1. [Regras de negócio consolidadas](01-regras-de-negocio.md): participantes, vendas elegíveis, cinco indicadores, XP, classificações e prêmios.
2. [Arquitetura, dados e contratos](02-arquitetura-dados-contratos.md): componentes, tabelas, funções RPC, grãos e fluxo de dados.
3. [Operação, segurança e implantação](03-operacao-seguranca-deploy.md): configuração, permissões, salvamento, publicação e runbook.
4. [Exceções, divergências e pendências](04-excecoes-divergencias-pendencias.md): casos de borda, comportamento efetivo e lacunas conhecidas.
5. [Testes e rastreabilidade](05-testes-rastreabilidade.md): cobertura automatizada, limites da validação e checklist de aceite.

Os documentos antigos em `docs/contexto`, `docs/regras`, `docs/dados` e `docs/arquitetura` preservam o levantamento detalhado, as prévias de dados e as decisões datadas. Eles são anexos e evidências; este manual é o índice operacional consolidado.

## Hierarquia das fontes

Quando duas fontes discordarem, use esta ordem para entender o estado do projeto:

1. O código e o SQL descrevem o comportamento executável atual.
2. Os testes descrevem os contratos automatizados do repositório.
3. As decisões explicitamente confirmadas nos documentos descrevem a regra de negócio pretendida.
4. O PDF descreve o regulamento original.
5. Prévias CSV/JSON são fotografias históricas e não representam o resultado corrente.

Uma divergência entre o comportamento executável e a regra pretendida não é resolvida por essa hierarquia: ela deve permanecer registrada como lacuna até que o código ou a decisão seja corrigido. A lista está em [Exceções, divergências e pendências](04-excecoes-divergencias-pendencias.md).

## Vocabulário de status

| Status | Significado |
| --- | --- |
| Implementada | Existe no código/SQL atual e faz parte do fluxo do painel |
| Manual | Depende de decisão humana registrada no sistema |
| Parcial | Parte da regra está implementada, mas existem limitações conhecidas |
| Divergente | O comportamento atual não coincide com a regra documentada |
| Pendente | Falta decisão, dado, integração ou comprovação no ambiente |
| Histórico | Evidência de uma consulta passada; não é recalculada pelo painel |

## Estado funcional resumido

| Área | Estado | Observação |
| --- | --- | --- |
| Login e sessão | Implementada | Supabase Auth por e-mail e senha; sessão revalidada em cada execução |
| Consulta das sete páginas | Implementada | Exige usuário autenticado e funções RPC instaladas |
| Budget anual | Implementada | R$ 119 milhões; vendas brutas elegíveis de 2026 menos todas as devoluções ocorridas em 2026 |
| Venda no quadrimestre | Implementada | Meta acumulada, proporcionalização do mês corrente e XP regional |
| Clientes novos | Implementada com limitações | Histórico desde 2022, evento diário e XP por vendedor; teto aplicado somente na consolidação |
| Clientes reativados | Implementada com limitações | Prazo de 6/12 meses, evento diário e XP por vendedor; teto aplicado somente na consolidação |
| Expansão de mix | Implementada com limitações | 23 produtos, 4 famílias, mínimos, KA e devolução pendente |
| Adiantamento | Manual e implementada | 12 checks por região; cinco contas podem salvar; histórico no banco |
| Visão geral e análise individual | Implementada | Consolidação e classificação são regionais no painel atual |
| Prêmio estimado | Não implementada | O painel mostra budget e classificação, mas não calcula valor de prêmio |
| Evolução histórica/exportação | Não implementada | Não há tela de série histórica nem exportação dedicada |
| Integração real | Pendente de comprovação | Testes locais não acessam o Supabase real |

## Mapa rápido do repositório

| Caminho | Responsabilidade |
| --- | --- |
| `app.py` | Interface, navegação, consolidação regional, classificação e apresentação |
| `polar/autenticacao.py` | Login, renovação, cliente autenticado e logout |
| `polar/atualizacao.py` | Data/hora do último refresh do dataflow |
| `polar/vendas.py` | Dias úteis, meta parcial/acumulada e faixas de XP de vendas |
| `polar/budget.py` | Contrato do budget anual e percentual de atingimento |
| `polar/clientes_novos.py` | Contrato da RPC de clientes novos |
| `polar/clientes_reativados.py` | Contrato da RPC de reativados |
| `polar/mix_produtos.py` | Contrato da RPC de mix |
| `polar/adiantamento.py` | Permissões, validação e persistência do adiantamento |
| `sql/*.sql` | Objetos de banco e regras analíticas executadas no Supabase |
| `sql/migrations/*.sql` | Alterações incrementais para instalações existentes |
| `tests/` | Testes unitários, de contrato de SQL e de interface Streamlit |
| `docs/dados/` | Dicionários, decisões, consultas de prévia e fotografias históricas |
| `assets/` | Logo e favicon |

## Fontes primárias e anexos

- [Regulamento original](../contexto/RegrasPolar.pdf)
- [Regras históricas detalhadas](../regras/regrasCampanha.md)
- [Interpretação de negócio histórica](../regras/regraNegocio.md)
- [Elegibilidade de vendas](../dados/elegibilidadeVendas.md)
- [Enquadramento dos pedidos](../dados/dadoEnquadramento.md)
- [Produtos do mix](../dados/produtosMix.csv)
- [Grupos KA](../dados/gruposKA.csv)
- [Times e segmentos](../dados/timesSegmentos.csv)
- [Feriados da campanha](../dados/feriadosNacionaisCampanha2026.csv)
- [Implantação no Streamlit Cloud](../arquitetura/deployStreamlitCloud.md)
