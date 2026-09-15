# Adiantamento de meta: confirmação manual por região

**Definido pelo usuário em 14/09/2026:** cada região tem uma fase de uma semana para 32% da meta mensal, duas semanas para 56% e três semanas para 80%. Essas referências identificam os três checks, mas o sistema não precisa definir datas de encerramento nem calcular o atingimento. A decisão considera particularidades operacionais e é informada diretamente pelo usuário autorizado como `true` ou `false`.

Nesta campanha, o adiantamento mencionado pelo usuário corresponde às fases do indicador de antecipação do regulamento.

## Tela e acesso

A primeira tela está implementada em [app.py](../../app.py). Ela apresenta uma tabela por competência, de setembro a dezembro de 2026:

| Região | 1ª semana · 32% | 2ª semana · 56% | 3ª semana · 80% | Observações |
| --- | --- | --- | --- | --- |
| Região fictícia A | Marcado | Marcado | Desmarcado | Exemplo fictício de conferência |
| Região fictícia B | Marcado | Desmarcado | Desmarcado | Exemplo fictício |

- **Somente `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech` podem preencher e salvar.** A identificação vem da sessão revalidada no Supabase Authentication.
- Os demais usuários válidos cadastrados em `auth.users` visualizam os registros e suas últimas atualizações, sem edição.
- A autorização é verificada no servidor em cada gravação; esconder o botão não é o único controle.
- O botão **Salvar alterações** grava os checks e observações no PostgreSQL/Supabase. Cada competência tem registros próprios.
- **Participação confirmada pelo usuário em 14/09/2026:** as linhas vêm somente das regiões de Canais e Construção com meta positiva na competência selecionada. O cadastro de vendedores ativos e registros antigos não criam linhas sem meta. Um mês futuro fica sem regiões até suas metas serem publicadas; depois da publicação, a tela passa a exibi-las pela situação atual.
- Uma única linha representa uma região no mês, mesmo que nela apareçam dois vendedores.

## Interpretação dos checks

| Campo | Referência comercial do check | Valor informado pelo usuário |
| --- | --- | --- |
| `semana_1_32` | Uma semana / 32% | `true` se a região atingiu; `false` se não atingiu |
| `semana_2_56` | Duas semanas / 56% | `true` se a região atingiu; `false` se não atingiu |
| `semana_3_80` | Três semanas / 80% | `true` se a região atingiu; `false` se não atingiu |

Cada check é independente. Marcar 80% não marca automaticamente 32% ou 56%. Na versão salva, marcado significa **atingiu** (`true`) e desmarcado significa **não atingiu** (`false`). A falta de uma avaliação salva é identificada pela ausência de versão/data de gravação, e não pelo cálculo de vendas.

As contas autorizadas podem registrar ou corrigir os checks, inclusive desmarcando-os. A tela não bloqueia edições por data, não converte as semanas em dias corridos ou úteis, não interpreta a data de edição como data do atingimento e não valida os percentuais contra as vendas. **Confirmado pelo usuário em 14/09/2026:** não é necessário definir datas exatas de encerramento das semanas; a avaliação manual `true`/`false` é a evidência suficiente para a apuração.

## Persistência e rastreabilidade

Tabela: `comercial_marts.campanha_polar_adiantamento`. Chave: `competencia` + `regiao`.

| Coluna | Tipo | Finalidade |
| --- | --- | --- |
| `competencia` | date | Primeiro dia do mês, de setembro a dezembro de 2026 |
| `regiao` | text | Região comercial; não depende do vendedor individual |
| `semana_1_32`, `semana_2_56`, `semana_3_80` | boolean | Checks manuais, inicialmente desmarcados |
| `observacao` | text | Considerações de quem preencheu; até 2.000 caracteres |
| `versao` | integer | Controle de concorrência; impede sobrescrever uma versão que mudou |
| `atualizado_em` | timestamptz | Horário de gravação; exibição no fuso de São Paulo |
| `atualizado_por` | text | E-mail obtido da sessão autenticada |
| `usuario_id` | text | Identificador autenticado de quem salvou |

O histórico fica em `comercial_marts.campanha_polar_adiantamento_historico`, registrando versão, valores anteriores e novos, data/hora e autoria da alteração. Registro e histórico são gravados na mesma transação. Se qualquer linha do envio estiver desatualizada, o envio inteiro é revertido e a tela pede recarga.

Essas tabelas pertencem ao aplicativo, não ao processamento que reconstrói os fatos de vendas. Não devem ser sobrescritas pelo dataflow.

## Relação com XP

**Titularidade confirmada pelo usuário em 14/09/2026:** os XP de adiantamento pertencem à região, assim como os XP de atingimento de vendas. Cada fase confirmada vale 10 XP para a região: até 30 XP por mês e 120 XP na campanha de setembro a dezembro de 2026. Essa decisão atualiza a definição anterior de teto individual deste indicador.

Uma fase pontua uma única vez na chave `campanha_id` + `regiao` + `competencia` + `fase`. A presença de dois vendedores na região, a edição por ambas as contas autorizadas ou várias versões do registro não criam créditos adicionais. Esses XP não são divididos entre vendedores nem incluídos em seus totais individuais.

Para a apuração corrente, usar os checks confirmados da versão atual salva: `xp_adiantamento_regiao_mes = 10 * quantidade_fases_confirmadas`. Consolidar as competências distintas da mesma região: `xp_adiantamento_regiao_campanha = min(120, soma(xp_adiantamento_regiao_mes))`. As versões do histórico servem para conferência, não são parcelas somáveis de XP. Check desmarcado não gera XP confirmado.

Exemplo: uma região com dois vendedores e os três checks confirmados em setembro gera **30 XP regionais**. Se confirmar duas fases em outubro, acrescenta 20 XP e passa a 50 XP regionais na campanha.

A tela registra as confirmações por região e mês e exibe o XP regional correspondente: quantidade de checks `true` multiplicada por 10, limitada naturalmente às três fases do mês. A visão geral apresenta o total mensal e o detalhamento por região. A apuração usa sempre a versão atual salva e reflete correções feitas pelas contas autorizadas, preservando o histórico das versões anteriores. A integração com o total completo da campanha e a apuração própria dos XP de vendas ainda serão adicionadas; as regras de vendas estão em [Dados de metas](dadoMeta.md).

## Situação de implantação

Código funcional, autorização e salvamento implementados e testados localmente. O SQL de criação está em [sql/adiantamento_meta.sql](../../sql/adiantamento_meta.sql). Como não foram encontradas credenciais de banco ou login nesta pasta, as tabelas ainda não foram criadas no Supabase por esta implementação.

A preparação do banco e a configuração do login estão no [README do projeto](../../README.md). Os testes exercitam login, renovação da sessão, salvamento, leitura por outros usuários, independência das fases/meses, correções, histórico e conflitos. O Supabase Auth e o PostgreSQL reais ainda exigem a configuração do ambiente.
