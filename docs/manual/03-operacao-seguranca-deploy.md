# Operação, segurança e implantação

## Pré-requisitos

- Python compatível com as dependências; o guia de cloud fixa Python 3.12.
- Acesso ao projeto Supabase para instalar os SQLs e administrar usuários.
- Repositório GitHub privado `LeoWatanabeAmbar/CampanhaPolar`, branch `main`, para o deploy descrito.
- Dependências: Streamlit 1.x a partir de 1.59, pandas 2.x, supabase-py 2.31 ou posterior abaixo de 3 e tzdata 2025.1 ou superior.

## Execução local

1. Instale as dependências:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Copie `.streamlit/secrets.example.toml` para `.streamlit/secrets.toml`.
3. Preencha somente:

   ```toml
   SUPABASE_URL = "https://SEU_PROJETO.supabase.co"
   SUPABASE_PUBLISHABLE_KEY = "sb_publishable_SUBSTITUA"
   ```

4. Inicie:

   ```powershell
   python -m streamlit run app.py
   ```

Sem os secrets, o painel para antes do login e exibe aviso de configuração pendente.

## Preparação do banco

Para uma instalação nova, execute no SQL Editor do Supabase, nesta ordem operacional:

1. `sql/adiantamento_meta.sql`
2. `sql/budget_anual.sql`
3. `sql/vendas_quadrimestre.sql`
4. `sql/clientes_novos.sql`
5. `sql/clientes_reativados.sql`
6. `sql/mix_produtos.sql`

Os scripts usam transação e notificam o PostgREST para recarregar o schema. Reexecutar o arquivo principal de uma função substitui sua versão.

As migrations documentam instalações antigas:

| Migration | Finalidade |
| --- | --- |
| `20260914_adicionar_leonardo_adiantamento.sql` | histórico: adicionou o segundo editor |
| `20260915_usar_data_api.sql` | migrou adiantamento para Auth + Data API e criou salvamento da campanha |
| `20260915_ampliar_timeout_data_api.sql` | aplica 60 s às três consultas de clientes/mix |
| `20260916_adicionar_editores_adiantamento.sql` | amplia a lista para cinco editores |
| `20260916_budget_sem_inadimplencia.sql` | retira inadimplência do budget |
| `20260916_budget_todas_devolucoes_2026.sql` | passa a descontar toda devolução ocorrida em 2026 |

Em uma instalação nova, os SQLs principais já incorporam o estado final conhecido; não é necessário aplicar migrations anteriores por cima deles.

## Usuários e permissões

Qualquer conta válida no Supabase Auth pode ler o painel. O cadastro público deve permanecer desabilitado e as contas devem ser criadas ou convidadas por um administrador.

Podem alterar adiantamento:

- `lais.vendrasco@ambar.tech`
- `leonardo.watanabe@ambar.tech`
- `jorge.castro@ambar.tech`
- `anyelle.santos@ambar.tech`
- `luis.oliveira@ambar.tech`

A lista está duplicada no Python, nas constraints das tabelas e na função SQL. Uma alteração de editor precisa atualizar todas essas ocorrências e seus testes.

## Modelo de segurança

- O navegador envia e-mail e senha ao Supabase Auth; a aplicação não lê `auth.users` diretamente.
- A senha não é armazenada no estado do Streamlit.
- O estado mantém ID, e-mail, access token e refresh token.
- Cada execução revalida a sessão com `set_session` e `get_user`; tokens renovados substituem os anteriores.
- Clientes Supabase não persistem sessão globalmente e não ativam auto-refresh interno.
- Logout usa escopo local e limpa o estado da sessão Streamlit.
- Contas anônimas são recusadas.
- A aplicação rejeita chave `sb_secret_*` e JWT com papel `service_role`.
- A Data API recebe a chave publicável e o JWT do usuário.
- As tabelas de adiantamento têm RLS habilitada e privilégios diretos revogados de `public`, `anon` e `authenticated`.
- Funções RPC têm execução revogada de `public`/`anon` e concedida a `authenticated`.
- A função de escrita revalida `auth.uid()` e o e-mail do JWT; esconder o botão na interface não é o controle de segurança final.
- Não existe restrição de leitura por região: qualquer usuário autenticado consulta todas as regiões e todos os detalhes retornados pelas RPCs.

## Salvamento do adiantamento

O editor carrega uma versão por região/mês. Ao salvar:

1. a identidade é revalidada;
2. a interface cria um lote com todos os meses disponíveis;
3. o cliente valida competência, região, booleanos, versão e observação;
4. a função externa agrupa por competência;
5. a função mensal valida o lote inteiro antes de gravar;
6. cada linha é bloqueada e sua versão é comparada;
7. linhas sem alteração são ignoradas;
8. alterações recebem versão incrementada e uma entrada de histórico;
9. qualquer erro desfaz toda a chamada.

Um conflito produz `CONCURRENT_CHANGE`; o usuário deve buscar a versão atual e refazer a edição. O histórico guarda valores anteriores, novos valores, instante, e-mail e ID do usuário. A interface mostra apenas a última atualização, não o histórico completo.

## Publicação

O procedimento detalhado está em [Publicação no Streamlit Community Cloud](../arquitetura/deployStreamlitCloud.md). Configuração registrada:

- repositório: `LeoWatanabeAmbar/CampanhaPolar`;
- branch: `main`;
- arquivo principal: `app.py`;
- Python: 3.12;
- secrets: somente URL e chave publicável do Supabase.

O repositório privado não torna o login Supabase desnecessário. Se o app do Streamlit for privado, o usuário enfrenta duas camadas de acesso; se for público, os dados continuam bloqueados até o login Supabase.

## Runbook de verificação diária

1. Entrar com uma conta de consulta.
2. Conferir a data/hora de atualização na lateral.
3. Abrir Visão geral e confirmar que budget e ranking carregam.
4. Conferir se a meta da competência corrente existe.
5. Comparar ao menos uma região com o Gestão Comercial/dataflow.
6. Abrir novos, reativados e mix e procurar linhas pendentes.
7. Com uma conta editora, conferir a versão atual antes de alterar adiantamento.
8. Registrar qualquer diferença de fonte, data de refresh ou regra antes de corrigir manualmente.

## Diagnóstico de erros

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| “aguardando a configuração do Supabase” | secrets ausentes ou inválidos | configurar URL e chave publicável |
| “E-mail ou senha inválidos” | credencial recusada com 400/401 | conferir conta e senha no Auth |
| sessão expirou | tokens ausentes, inválidos ou revogados | entrar novamente |
| `AUTH_REQUIRED` / 42501 | JWT não chegou ou expirou | entrar novamente e conferir grants |
| `PERMISSION_DENIED` | conta não está na allowlist | usar conta autorizada ou atualizar código + SQL |
| `INVALID_MONTH` | competência fora de set–dez/2026 ou não é dia 1 | corrigir chamada/versão do app |
| `INVALID_REGION` | região sem meta positiva no mês | publicar/corrigir a meta e recarregar |
| `CONCURRENT_CHANGE` | outra sessão alterou a mesma linha | recarregar e reaplicar a alteração |
| formato anterior dos dados | função RPC desatualizada no Supabase | reaplicar o SQL indicado e reiniciar o app |
| timeout | consulta excedeu 60 s | revisar plano/índices e volume; não aumentar silenciosamente |
| última atualização indisponível | consulta ao controle falhou ou não retornou linha válida | conferir `cpv_refresh_controle` e permissões |

## Mudanças seguras

### Alterar uma regra analítica

1. Atualizar o documento de regra e registrar a decisão.
2. Alterar o SQL/Python correspondente.
3. Atualizar testes de limite e de contrato.
4. Executar a suíte completa.
5. Reaplicar a função no Supabase.
6. Validar casos reais e regressões retroativas.

### Alterar produtos ou KA

Atualizar simultaneamente o SQL e os CSVs de referência. Produtos precisam continuar como texto para preservar zeros à esquerda. Recalcular todo o histórico desde 2022, pois a novidade depende da primeira ocorrência.

### Alterar feriados

Atualizar `polar/vendas.py`, o CSV de referência e os testes de dias úteis. Feriados estaduais/municipais não são considerados hoje.

### Alterar editor

Atualizar `EDITOR_EMAILS`, as duas constraints, a allowlist da função SQL, a migration para instalações existentes, a documentação e os testes.

## Backup e recuperação

O repositório não define política de backup do Supabase. Antes de mudanças estruturais, preservar ao menos:

- `campanha_polar_adiantamento`;
- `campanha_polar_adiantamento_historico`;
- versão instalada das funções RPC;
- fotografia dos resultados usados em fechamentos.

Não há procedimento automatizado de rollback no repositório. A recuperação de função é feita reaplicando uma versão SQL conhecida; recuperação de dados depende do backup do banco.
