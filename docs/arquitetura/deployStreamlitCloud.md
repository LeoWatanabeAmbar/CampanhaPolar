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
[database]
url = "postgresql+psycopg2://USUARIO:SENHA_URL_ENCODED@HOST:5432/postgres"

[access]
microsoft_tenant_id = "TENANT_ID_DA_ORGANIZACAO"

[auth]
redirect_uri = "https://SUBDOMINIO.streamlit.app/oauth2callback"
cookie_secret = "SEGREDO_LONGO_ALEATORIO"

[auth.microsoft]
client_id = "APPLICATION_CLIENT_ID"
client_secret = "CLIENT_SECRET_VALUE"
server_metadata_url = "https://login.microsoftonline.com/TENANT_ID_DA_ORGANIZACAO/v2.0/.well-known/openid-configuration"
```

Para o Supabase, prefira a conexão **Session pooler**, porta 5432, copiada em **Connect** no painel do projeto. Ela funciona em redes IPv4 e aceita conexões persistentes. Se a senha contiver `@`, `:`, `/`, `#`, `%`, espaço ou outro caractere reservado, use a senha codificada para URL.

O `cookie_secret` deve ser aleatório e diferente do segredo do Microsoft Entra. Ele pode ser gerado localmente com:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 4. Autorizar a URL no Microsoft Entra

No Azure Portal:

1. Abra **Microsoft Entra ID → App registrations**.
2. Selecione o aplicativo usado pelo painel.
3. Abra **Authentication → Platform configurations → Web**.
4. Adicione exatamente `https://SUBDOMINIO.streamlit.app/oauth2callback` em **Redirect URIs**.
5. Salve. A URL local `http://localhost:8501/oauth2callback` pode permanecer cadastrada para desenvolvimento.

O valor de `client_secret` no Streamlit é o **Value** do segredo criado em **Certificates & secrets**, não o Secret ID.

## 5. Preparar o banco

Antes do primeiro uso, execute [adiantamento_meta.sql](../../sql/adiantamento_meta.sql) no SQL Editor do Supabase. O usuário da URL privada precisa conseguir:

- ler `comercial_marts.metas_comerciais`;
- ler e gravar `comercial_marts.campanha_polar_adiantamento`;
- inserir em `comercial_marts.campanha_polar_adiantamento_historico`.

## 6. Publicar e validar

Clique em **Deploy** e acompanhe os logs. Depois verifique:

1. abertura da tela de login;
2. entrada com uma conta do tenant configurado;
3. carregamento das regiões e metas de setembro;
4. consulta com um usuário comum;
5. salvamento com Laís ou Leonardo;
6. persistência após recarregar a página.

Como o repositório é privado, o aplicativo nasce privado no Community Cloud. Os visualizadores podem ser convidados nas configurações de compartilhamento. Se o acesso do Streamlit for tornado público no futuro, o login Microsoft do próprio painel continuará restringindo a leitura ao tenant configurado.

## Atualizações

O Community Cloud acompanha o GitHub. Novos commits enviados para `main` atualizam o aplicativo automaticamente; mudanças em `requirements.txt` provocam a reinstalação das dependências.

Referências oficiais: [publicar um aplicativo](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [secrets no Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [login com Microsoft](https://docs.streamlit.io/develop/tutorials/authentication/microsoft) e [conexões PostgreSQL do Supabase](https://supabase.com/docs/guides/database/connecting-to-postgres).
