# Visão de clientes novos

**Implementada em 15/09/2026:** a página **Clientes novos** consulta a situação atual do Supabase por competência e mostra os grupos comerciais cuja primeira compra elegível foi encontrada no histórico disponível desde janeiro de 2022.

## Conteúdo da página

- indicadores de grupos novos, pedidos reunidos no primeiro evento, valor líquido elegível e XP bruto confirmado;
- filtros por região, situação da atribuição e busca por grupo, pedido ou vendedor;
- detalhe da primeira compra, grupo comercial, pedidos, vendedores, regiões, segmento, valor e XP;
- sinalização dos casos em que a atribuição ainda está pendente.

Pedidos do mesmo grupo comercial na mesma data formam um único evento. Um evento confirmado gera 10 XP brutos de cliente novo. Com um vendedor identificado, ele recebe 10 XP; com exatamente dois vendedores válidos, cada um recebe 5 XP. A página informa o valor anterior ao teto individual acumulado de 100 XP, cuja consolidação será feita na apuração completa da campanha.

## Consulta e regras aplicadas

A função `public.campanha_polar_carregar_clientes_novos(date)`, criada por [clientes_novos.sql](../../sql/clientes_novos.sql), é executada pela Data API com o JWT do usuário. Somente o papel `authenticated` recebe permissão para chamá-la.

A consulta:

- usa `grupo_comercial_id` como identidade e exige correspondência em `dim_grupo_comercial`;
- considera o histórico elegível a partir de 01/01/2022;
- usa `data_emissao` como data de implantação e primeira compra;
- exclui pedidos e itens inválidos, bonificações, remessas e transferências;
- usa a situação financeira atual de `vw_clientes_inadimplentes`; para bloqueados, considera somente `fct_faturamento_item`, enquanto SMART PODS e MRV já são exceções na view;
- abate todas as devoluções vinculadas por nota original, pedido e alocação comercial;
- remove da conclusão os grupos com data histórica ausente ou devolução sem vínculo inequívoco ao pedido;
- reúne pedidos do mesmo grupo e dia e considera somente eventos ligados a pelo menos uma região com meta positiva da competência;
- exige um ou dois vendedores, mapeamento único, segmento consistente e meta positiva em todas as regiões para confirmar os 10 XP do evento.

Grupos ausentes ou desconhecidos não aparecem como clientes novos: permanecem aguardando correção cadastral, conforme definido. A função recalcula o resultado a cada consulta; cancelamentos, faturamento, quitações, devoluções, cadastro do grupo e metas podem alterar retroativamente a lista.

## Limite atual

O XP exibido é o XP bruto do evento. A aplicação do teto individual de 100 XP exige consolidar todas as atribuições da campanha por vendedor em ordem cronológica; essa visão acumulada ainda será construída. Casos sem vínculo confiável para concluir a novidade são omitidos em vez de receber crédito provisório.
