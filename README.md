# Campanha Polar

Primeira versão do painel implementada no padrão visual do Gestão Comercial, com navegação lateral e duas páginas:

- **Visão geral:** meta total do mês, regiões participantes, fases confirmadas, XP regional de adiantamento, cobertura por fase e detalhamento regional.
- **Adiantamento de meta:** uma linha por região e mês, com checks independentes para 32% na primeira semana, 56% na segunda e 80% na terceira.

O login usa Microsoft OIDC, seguindo o padrão do Gestão Comercial. Somente as contas `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech`, autenticadas no tenant configurado, podem preencher e salvar. Os demais usuários autenticados desse tenant podem consultar. A autorização é conferida novamente no servidor a cada salvamento.

## Configuração e execução

1. Instale as dependências: `python -m pip install -r requirements.txt`.
2. Execute [sql/adiantamento_meta.sql](sql/adiantamento_meta.sql) no Supabase/PostgreSQL. O script cria somente as duas tabelas novas de registro e histórico no schema `comercial_marts`. Se as tabelas já foram criadas com a permissão exclusiva da Laís, aplique também a [migração que inclui Leonardo](sql/migrations/20260914_adicionar_leonardo_adiantamento.sql), que preserva os dados existentes.
3. Copie [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) para `.streamlit/secrets.toml` e configure a conexão privada PostgreSQL e o aplicativo Microsoft Entra do tenant da organização. Não use `common` ou `organizations` no endereço do provedor. Cadastre a URL de retorno `http://localhost:8501/oauth2callback` no aplicativo Entra para a execução local. Em hospedagem, use sua URL HTTPS.
4. Inicie: `python -m streamlit run app.py`.

Para publicar no Streamlit Community Cloud, siga o [guia de implantação](docs/arquitetura/deployStreamlitCloud.md). Ele registra o repositório, branch, arquivo principal, secrets, conexão Supabase e callback do Microsoft Entra necessários para este painel.

A integração OIDC segue a [documentação oficial do Streamlit](https://docs.streamlit.io/develop/tutorials/authentication/microsoft). Use uma conexão de banco restrita ao servidor, com leitura de `metas_comerciais` e `app_vendedor_regiao_time` e acesso às novas tabelas. O script habilita RLS e remove acesso direto das funções `anon` e `authenticated` da API Supabase; a conexão privada precisa pertencer ao proprietário das tabelas ou a um papel de servidor autorizado a operar com RLS. Não disponibilize a credencial de banco ao navegador.

**Situação local:** a visão geral, a tela de adiantamento, as regras de autorização e o SQL estão implementados. Não foram encontradas credenciais de login ou banco nesta pasta, portanto a migração não foi aplicada no Supabase e o login real ainda exige configuração. O aplicativo mostra uma mensagem de configuração pendente nesse estado.

## Preenchimento

- Escolha setembro, outubro, novembro ou dezembro de 2026. A tabela reúne regiões do cadastro ativo, metas do mês e registros já salvos.
- Marque cada fase após a conferência manual de suas condições. As fases são independentes; marcar 80% não marca automaticamente 32% ou 56%.
- Use observações para registrar considerações da apuração e clique em **Salvar alterações**. A gravação é transacional: se houver conflito com outra sessão, nenhuma linha do envio é aplicada.
- O histórico conserva os valores anteriores, os novos valores, a conta autenticada e a data/hora. É possível desmarcar um check como correção, preservando essa alteração no histórico.
- Um check desmarcado significa atingimento não confirmado. A coluna de atualizações distingue linhas já salvas de regiões sem registro.
- A tabela não consulta valores de venda para marcar fases nem impõe datas de bloqueio. A avaliação de atingimento dentro das semanas fica com a responsável, conforme solicitado.

As tabelas de adiantamento são mantidas pelo aplicativo e não devem ser reconstruídas pelo dataflow. O usuário confirmou que os XP de adiantamento pertencem à região: 10 por fase confirmada, até 30 no mês e 120 na campanha, sem divisão ou duplicação por vendedor. O painel calcula e exibe esses XP a partir da versão atual dos checks salvos. A integração desse resultado com a apuração completa da campanha segue descrita na [documentação do adiantamento](docs/dados/dadoAdiantamento.md).

## Validação

Instale a ferramenta de testes com `python -m pip install "pytest>=8,<9"` e execute:

`python -m pytest -q`

Os testes verificam autorização, persistência em banco temporário, independência das fases e dos meses, correções e histórico, rollback em conflito e interação da tela com editor/leitor. A integração com PostgreSQL e o login Microsoft reais dependem da configuração do ambiente.
