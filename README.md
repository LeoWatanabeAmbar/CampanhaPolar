# Campanha Polar

Primeira versão do painel implementada no padrão visual do Gestão Comercial, com navegação lateral e duas páginas:

- **Visão geral:** meta total do mês, regiões participantes, fases confirmadas, XP regional de adiantamento, cobertura por fase e detalhamento regional.
- **Adiantamento de meta:** uma linha por região e mês, com checks independentes para 32% na primeira semana, 56% na segunda e 80% na terceira.

O login usa e-mail e senha do Supabase Authentication. Qualquer conta válida cadastrada em `auth.users` pode consultar o painel. Somente `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech` podem preencher e salvar. A sessão é revalidada no Supabase e o mesmo JWT acessa funções restritas da Data API.

## Configuração e execução

1. Instale as dependências: `python -m pip install -r requirements.txt`.
2. Execute [sql/adiantamento_meta.sql](sql/adiantamento_meta.sql) no SQL Editor do Supabase. O script cria as duas tabelas de registro e histórico no schema `comercial_marts` e duas funções públicas restritas para leitura e gravação pela Data API. Em uma instalação que já recebeu o SQL anterior, execute [20260915_usar_data_api.sql](sql/migrations/20260915_usar_data_api.sql).
3. Copie [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) para `.streamlit/secrets.toml` e configure somente `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY`. Nunca use `service_role` ou `sb_secret_...`.
4. Inicie: `python -m streamlit run app.py`.

Para publicar no Streamlit Community Cloud, siga o [guia de implantação](docs/arquitetura/deployStreamlitCloud.md). Ele registra o repositório, branch, arquivo principal e os dois secrets necessários.

O Supabase Authentication recebe e-mail e senha e devolve os tokens da sessão; a aplicação não consulta `auth.users` diretamente. O painel chama a Data API com a chave publicável e o JWT do usuário. As tabelas permanecem sem acesso direto para `anon` e `authenticated`. A função de leitura aceita qualquer usuário autenticado; a função de gravação extrai e-mail e ID do próprio JWT e aceita somente as duas contas editoras. Nenhuma senha de PostgreSQL é armazenada no Streamlit.

**Situação local:** a visão geral, a tela de adiantamento, as regras de autorização e o SQL estão implementados. Os valores reais dos dois secrets não ficam no repositório, e o SQL ainda precisa ser executado no projeto Supabase antes do primeiro acesso. O aplicativo mostra uma mensagem de configuração pendente sem esses secrets.

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

Os testes verificam autenticação e renovação de sessão, o contrato da Data API, autorização, independência das fases e dos meses, correções e histórico, rollback em conflito e interação da tela com editor/leitor. A integração com o projeto Supabase real depende da configuração do ambiente.
