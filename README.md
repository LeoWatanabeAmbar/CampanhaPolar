# Campanha Polar

Painel implementado no padrão visual do Gestão Comercial, com navegação lateral e cinco páginas:

- **Visão geral:** metas publicadas da campanha, regiões participantes, fases confirmadas, XP regional de adiantamento, cobertura por fase e detalhamento regional.
- **Clientes novos:** resumo por região e detalhamento por vendedor, com duas linhas para triangulações e o XP atribuído a cada participante.
- **Clientes reativados:** resumo por região e detalhamento por vendedor dos retornos após 6 meses em Canais ou 12 meses em Construção.
- **Mix de produtos:** resumo regional e detalhamento por vendedor da primeira compra das famílias, mínimos, exclusões, pendências e XP.
- **Adiantamento de meta:** uma linha por região e 12 checks, com as três fases de setembro, outubro, novembro e dezembro na mesma tabela.

O ícone azul da Polar em [assets/icone_polar.png](assets/icone_polar.png) é usado como favicon da aba do navegador. O logotipo horizontal permanece na interface do painel.

O login usa e-mail e senha do Supabase Authentication. Qualquer conta válida cadastrada em `auth.users` pode consultar o painel. Somente `lais.vendrasco@ambar.tech` e `leonardo.watanabe@ambar.tech` podem preencher e salvar. A sessão é revalidada no Supabase e o mesmo JWT acessa funções restritas da Data API.

## Configuração e execução

1. Instale as dependências: `python -m pip install -r requirements.txt`.
2. Execute [sql/adiantamento_meta.sql](sql/adiantamento_meta.sql), [sql/clientes_novos.sql](sql/clientes_novos.sql), [sql/clientes_reativados.sql](sql/clientes_reativados.sql) e [sql/mix_produtos.sql](sql/mix_produtos.sql) no SQL Editor do Supabase. Eles habilitam o adiantamento e as três consultas autenticadas de clientes. Em uma instalação que recebeu a versão anterior do adiantamento, execute [20260915_usar_data_api.sql](sql/migrations/20260915_usar_data_api.sql) antes dos SQLs de clientes.
3. Copie [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) para `.streamlit/secrets.toml` e configure somente `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY`. Nunca use `service_role` ou `sb_secret_...`.
4. Inicie: `python -m streamlit run app.py`.

Para publicar no Streamlit Community Cloud, siga o [guia de implantação](docs/arquitetura/deployStreamlitCloud.md). Ele registra o repositório, branch, arquivo principal e os dois secrets necessários.

O Supabase Authentication recebe e-mail e senha e devolve os tokens da sessão; a aplicação não consulta `auth.users` diretamente. O painel chama a Data API com a chave publicável e o JWT do usuário. As tabelas permanecem sem acesso direto para `anon` e `authenticated`. A função de leitura aceita qualquer usuário autenticado; a função de gravação extrai e-mail e ID do próprio JWT e aceita somente as duas contas editoras. Nenhuma senha de PostgreSQL é armazenada no Streamlit.

**Situação local:** a visão geral, a tela de adiantamento, as regras de autorização e o SQL estão implementados. Os valores reais dos dois secrets não ficam no repositório, e o SQL ainda precisa ser executado no projeto Supabase antes do primeiro acesso. O aplicativo mostra uma mensagem de configuração pendente sem esses secrets.

## Preenchimento

- A navegação não possui filtro de competência. As visões abrangem toda a campanha e identificam a competência nas tabelas; o adiantamento reúne setembro a dezembro na mesma tabela.
- Marque cada fase após a conferência manual de suas condições. As fases são independentes; marcar 80% não marca automaticamente 32% ou 56%.
- Clique em **Salvar alterações** para gravar todos os meses em uma única transação. Se houver conflito com outra sessão, nenhuma linha do envio é aplicada.
- O histórico conserva os valores anteriores, os novos valores, a conta autenticada e a data/hora. É possível desmarcar um check como correção, preservando essa alteração no histórico.
- Um check desmarcado significa atingimento não confirmado. A coluna de atualizações distingue linhas já salvas de regiões sem registro.
- A tabela não consulta valores de venda para marcar fases nem impõe datas de bloqueio. A avaliação de atingimento dentro das semanas fica com a responsável, conforme solicitado.

As tabelas de adiantamento são mantidas pelo aplicativo e não devem ser reconstruídas pelo dataflow. O usuário confirmou que os XP de adiantamento pertencem à região: 10 por fase confirmada, até 30 no mês e 120 na campanha, sem divisão ou duplicação por vendedor. O painel calcula e exibe esses XP a partir da versão atual dos checks salvos. A integração desse resultado com a apuração completa da campanha segue descrita na [documentação do adiantamento](docs/dados/dadoAdiantamento.md).

## Validação

Instale a ferramenta de testes com `python -m pip install "pytest>=8,<9"` e execute:

`python -m pytest -q`

Os testes verificam autenticação e renovação de sessão, os contratos da Data API, as páginas de novos, reativados e mix, autorização, independência das fases e dos meses, correções e histórico, rollback em conflito e interação da tela com editor/leitor. A integração com o projeto Supabase real depende da configuração do ambiente.
