# Visão de clientes reativados

**Implementada em 15/09/2026:** a página **Clientes reativados** consulta a situação atual do Supabase para toda a campanha. Ela mostra os grupos comerciais que voltaram a comprar depois de pelo menos 6 meses em Canais ou 12 meses em Construção.

## Conteúdo da página

- tabela inicial com uma linha por região; dentro da célula da lista, cada cliente aparece abaixo do anterior, enquanto quantidade e XP permanecem únicos para a região;
- apenas filtro de região no detalhamento;
- data da última compra válida, data da reativação e prazo aplicado;
- uma linha por vendedor e região, com pedidos, segmento, atribuição e XP.

Na exibição dos pedidos, o prefixo da filial padrão `01101/` fica oculto. Pedidos de outras filiais preservam sua identificação completa.

Pedidos do mesmo grupo comercial na mesma data formam um único evento. O limite do prazo é inclusivo: a compra pode pontuar no dia em que completa exatamente 6 ou 12 meses. Um evento confirmado gera 8 XP; um vendedor recebe os 8 XP e exatamente dois vendedores aparecem em duas linhas de 4 XP cada. O teto individual acumulado na campanha é 80 XP.

## Consulta e regras aplicadas

A função `public.campanha_polar_carregar_clientes_reativados(date)`, criada por [clientes_reativados.sql](../../sql/clientes_reativados.sql), é executada pela Data API com o JWT do usuário autenticado.

A consulta reutiliza as regras de elegibilidade da visão de clientes novos: histórico desde 01/01/2022, implantação em `data_emissao`, grupo comercial como identidade, exclusão de operações inválidas, tratamento da inadimplência pela parte faturada e abatimento das devoluções vinculadas. A última compra é calculada na sequência cronológica dos eventos válidos do grupo.

A página considera apenas regiões participantes com meta positiva na competência. Vendedor ausente, quantidade diferente de um ou dois, mapeamento ambíguo, segmentos divergentes ou região sem meta impedem o crédito provisório e aparecem como atribuição pendente.

O resultado é recalculado a cada consulta. Cancelamentos, quitações, faturamentos, devoluções, correções cadastrais e metas podem alterar tanto a última compra quanto o evento de reativação.
