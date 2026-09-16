# Campanha Polar

Painel implementado no padrão visual do Gestão Comercial, com navegação lateral e sete páginas:

- **Visão geral:** cartão do realizado elegível de 2026 contra o budget anual de R$ 119 milhões e ranking regional, ordenado pelo XP total, com os cinco indicadores e a classificação da campanha.
- **Análise individual:** filtro de região, XP total, classificação, composição dos cinco indicadores em barras horizontais e tabelas com todos os eventos que formam o resultado.
- **Venda no Quadrimestre:** realizado elegível acumulado desde setembro contra as metas regionais disponíveis, usando a meta proporcional do mês atual para calcular o atingimento e o XP por região.
- **Clientes novos:** resumo por região e detalhamento por vendedor, com duas linhas para triangulações e o XP atribuído a cada participante.
- **Clientes reativados:** resumo por região e detalhamento por vendedor dos retornos após 6 meses em Canais ou 12 meses em Construção.
- **Mix de produtos:** resumo regional e detalhamento por vendedor da primeira compra das famílias, mínimos, exclusões, pendências e XP.
- **Adiantamento de meta:** uma linha por região e 12 checks, com as três fases de setembro, outubro, novembro e dezembro na mesma tabela.

A barra lateral mostra a data e a hora da última atualização do painel no fuso de São Paulo. A data dessa atualização é usada como referência nos cálculos de budget, vendas e XP regional.

O ícone azul da Polar em [assets/icone_polar.png](assets/icone_polar.png) é usado como favicon da aba do navegador. O logotipo horizontal permanece na interface do painel.

O login usa e-mail e senha do Supabase Authentication. Qualquer conta válida cadastrada em `auth.users` pode consultar o painel. As contas `lais.vendrasco@ambar.tech`, `leonardo.watanabe@ambar.tech`, `jorge.castro@ambar.tech`, `anyelle.santos@ambar.tech` e `luis.oliveira@ambar.tech` podem preencher e salvar. A sessão é revalidada no Supabase e o mesmo JWT acessa funções restritas da Data API.

## Configuração e execução

1. Instale as dependências: `python -m pip install -r requirements.txt`.
2. Execute [sql/adiantamento_meta.sql](sql/adiantamento_meta.sql), [sql/budget_anual.sql](sql/budget_anual.sql), [sql/vendas_quadrimestre.sql](sql/vendas_quadrimestre.sql), [sql/clientes_novos.sql](sql/clientes_novos.sql), [sql/clientes_reativados.sql](sql/clientes_reativados.sql) e [sql/mix_produtos.sql](sql/mix_produtos.sql) no SQL Editor do Supabase. Eles habilitam o adiantamento e as consultas autenticadas do painel. Em uma instalação existente, execute [20260916_adicionar_editores_adiantamento.sql](sql/migrations/20260916_adicionar_editores_adiantamento.sql) para liberar as cinco contas editoras e [20260916_budget_sem_inadimplencia.sql](sql/migrations/20260916_budget_sem_inadimplencia.sql) para atualizar o cálculo do Budget anual.
3. Copie [.streamlit/secrets.example.toml](.streamlit/secrets.example.toml) para `.streamlit/secrets.toml` e configure somente `SUPABASE_URL` e `SUPABASE_PUBLISHABLE_KEY`. Nunca use `service_role` ou `sb_secret_...`.
4. Inicie: `python -m streamlit run app.py`.

Para publicar no Streamlit Community Cloud, siga o [guia de implantação](docs/arquitetura/deployStreamlitCloud.md). Ele registra o repositório, branch, arquivo principal e os dois secrets necessários.

O Supabase Authentication recebe e-mail e senha e devolve os tokens da sessão; a aplicação não consulta `auth.users` diretamente. O painel chama a Data API com a chave publicável e o JWT do usuário. As tabelas permanecem sem acesso direto para `anon` e `authenticated`. A função de leitura aceita qualquer usuário autenticado; a função de gravação extrai e-mail e ID do próprio JWT e aceita somente as cinco contas editoras. Nenhuma senha de PostgreSQL é armazenada no Streamlit.

**Situação local:** a visão geral, a tela de adiantamento, as regras de autorização e o SQL estão implementados. Os valores reais dos dois secrets não ficam no repositório, e o SQL ainda precisa ser executado no projeto Supabase antes do primeiro acesso. O aplicativo mostra uma mensagem de configuração pendente sem esses secrets.

## Preenchimento

- A navegação não possui filtro de competência. As visões abrangem toda a campanha e identificam a competência nas tabelas; o adiantamento reúne setembro a dezembro na mesma tabela.
- Em Venda no Quadrimestre, os meses encerrados entram integralmente e o mês atual entra proporcionalmente aos dias úteis decorridos. Em 15/09/2026, setembro possui 10 de 21 dias úteis decorridos; em outubro, a comparação será `setembro integral + outubro parcial`, tanto nas metas quanto nas vendas. O percentual acumulado exato define o XP, uma única vez por região.
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
