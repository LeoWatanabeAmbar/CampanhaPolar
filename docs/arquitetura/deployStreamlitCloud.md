# Publicação no Streamlit Community Cloud

O painel é publicado a partir do repositório privado `LeoWatanabeAmbar/CampanhaPolar`, branch `main`, usando `app.py` como arquivo principal.

## 1. Conectar o GitHub

1. Acesse [share.streamlit.io](https://share.streamlit.io/) e entre com a conta associada ao GitHub.
2. Conecte a conta GitHub ao workspace do Streamlit.
3. Autorize o Streamlit a acessar repositórios privados. A conta usada precisa ter permissão administrativa no repositório.

## 2. Criar o aplicativo

1. Clique em **Create app**.
2. Escolha **Yup, I have an app**.
3. Preencha:
   - Repository: `LeoWatanabeAmbar/CampanhaPolar`
   - Branch: `main`
   - Main file path: `app.py`
4. Escolha um subdomínio disponível, por exemplo `campanha-polar-ambar`. A URL resultante terá o formato `https://campanha-polar-ambar.streamlit.app`.
5. Em **Advanced settings**, selecione Python 3.12 e preencha os secrets descritos abaixo.

## 3. Configurar os secrets

Nunca grave os valores reais no GitHub. Cole este conteúdo no campo **Secrets** do Streamlit, substituindo todos os marcadores:

```toml
SUPABASE_URL = "https://SEU_PROJETO.supabase.co"
SUPABASE_PUBLISHABLE_KEY = "sb_publishable_SUBSTITUA"
```

Encontre a URL do projeto e a chave publicável em **Project Settings → API Keys** no Supabase. O painel acessa os dados pela Data API com o JWT da conta autenticada. Não é necessário configurar Session pooler, usuário de banco ou senha de PostgreSQL.

`SUPABASE_PUBLISHABLE_KEY` deve receber a chave publicável do projeto, normalmente iniciada por `sb_publishable_`. Não use `service_role`, JWT com papel `service_role` ou chave iniciada por `sb_secret_`; essas credenciais têm privilégios administrativos e o aplicativo rejeita seu uso no login.

## 4. Preparar os usuários

1. No Supabase, abra **Authentication → Providers → Email** e mantenha habilitado o login por e-mail e senha.
2. Desative o cadastro público de usuários para que somente contas administradas tenham acesso.
3. Em **Authentication → Users**, crie ou convide as pessoas que poderão entrar no painel.
4. Confirme que Laís e Leonardo usam exatamente os e-mails autorizados no código; esses dois usuários podem editar o adiantamento e os demais possuem consulta.

O aplicativo usa a API do Supabase Authentication para validar `auth.users`; não consulta diretamente a tabela protegida nem oferece cadastro público.

## 5. Preparar o banco

Antes do primeiro uso, execute [adiantamento_meta.sql](../../sql/adiantamento_meta.sql), [clientes_novos.sql](../../sql/clientes_novos.sql), [clientes_reativados.sql](../../sql/clientes_reativados.sql) e [mix_produtos.sql](../../sql/mix_produtos.sql) no SQL Editor do Supabase. Em um projeto que já recebeu a versão anterior do adiantamento, execute também [20260915_usar_data_api.sql](../../sql/migrations/20260915_usar_data_api.sql). Os scripts:

- mantém as tabelas de adiantamento e histórico sem acesso direto pela API;
- cria uma função de leitura para usuários autenticados;
- cria uma função de gravação que confere no JWT se a conta é Laís ou Leonardo;
- cria funções de consulta para clientes novos, clientes reativados e expansão de mix;
- valida competência, região, tipos, versões e histórico dentro do banco.

As funções ficam no schema `public`, já atendido pela Data API padrão, e acessam internamente as tabelas de `comercial_marts`. Não é preciso expor o schema `comercial_marts` nas configurações da API.

Quando uma atualização alterar as colunas retornadas por uma função, execute novamente o arquivo SQL correspondente. Os scripts notificam o PostgREST para recarregar o cache de schema após a transação. Se a Data API ainda recusar uma consulta, a mensagem do painel informa o código e a descrição enviados pelo Supabase para orientar o diagnóstico.

## 6. Publicar e validar

Clique em **Deploy** e acompanhe os logs. Depois verifique:

1. abertura da tela de login;
2. entrada com e-mail e senha de uma conta cadastrada em `auth.users`;
3. carregamento das regiões e metas de setembro;
4. carregamento dos clientes novos e seus primeiros eventos;
5. carregamento das reativações e conferência da última compra;
6. carregamento do mix, mínimos e situações sem XP ou pendentes;
7. consulta com um usuário comum;
8. salvamento com Laís ou Leonardo;
9. persistência após recarregar a página.

Como o repositório é privado, o aplicativo nasce privado no Community Cloud. Para usar somente o login do Supabase, altere **App settings → Sharing** para aplicativo público; a URL ficará acessível, mas nenhum dado será carregado antes da autenticação do próprio painel. Se o aplicativo permanecer privado no Community Cloud, cada pessoa precisará passar pelo acesso do Streamlit e depois pelo login do Supabase.

## Atualizações

O Community Cloud acompanha o GitHub. Novos commits enviados para `main` atualizam o aplicativo automaticamente; mudanças em `requirements.txt` provocam a reinstalação das dependências.

Referências oficiais: [publicar um aplicativo](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [secrets no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [login com senha no Supabase](https://supabase.com/docs/guides/auth/passwords), [Data API](https://supabase.com/docs/guides/api), [funções de banco](https://supabase.com/docs/guides/database/functions) e [segurança da Data API](https://supabase.com/docs/guides/database/secure-data).
