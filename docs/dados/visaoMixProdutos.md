# Visão de mix de produtos

**Implementada em 15/09/2026:** a página **Mix de produtos** consulta a primeira compra de cada família mapeada pelo grupo comercial durante a campanha. Ela abrange Hydrofix, CPP 009, Grelha + Porta Grelha e Suporte de Bancada.

## Conteúdo da página

- indicadores de linhas avaliadas, expansões confirmadas, valor das linhas e XP confirmado;
- filtros por região, família, resultado e busca por grupo, produto, pedido ou vendedor;
- competência, primeira compra, códigos dos produtos, pedidos reunidos no dia, responsáveis e regiões;
- valor da linha, mínimo aplicável, resultado do enquadramento e distribuição dos XP.

O valor dos pedidos do mesmo grupo, data e família é somado antes de verificar o mínimo. Cada primeira compra de família que cumprir as regras gera 10 XP. Um vendedor recebe 10 XP; exatamente dois recebem 5 XP cada. O indicador não possui teto individual. Clientes KA aparecem sem XP.

## Consulta e regras aplicadas

A função `public.campanha_polar_carregar_mix_produtos(date)`, criada por [mix_produtos.sql](../../sql/mix_produtos.sql), é executada pela Data API com o JWT do usuário autenticado. Os 23 códigos e os 16 grupos KA estão versionados no SQL conforme [produtosMix.csv](produtosMix.csv) e [gruposKA.csv](gruposKA.csv).

Os mínimos aplicados são:

| Segmento | Família | Mínimo |
| --- | --- | ---: |
| Construção | Hydrofix | R$ 3.000,00 |
| Construção | Grelha + Porta Grelha | R$ 6.000,00 |
| Construção | Suporte de Bancada | R$ 9.000,00 |
| Canais | CPP 009 | R$ 2.200,00 |
| Canais | Grelha + Porta Grelha | R$ 1.000,00 |
| Canais | Suporte de Bancada | R$ 1.000,00 |

A consulta usa o histórico desde 01/01/2022, considera somente itens elegíveis e usa a parte faturada quando o cliente está bloqueado por inadimplência. A primeira compra da família impede pontuação posterior mesmo quando não alcança o mínimo.

## Devoluções

`fct_nota_devolucao` não identifica o produto ou item devolvido. Por isso, qualquer grupo com devolução encontrada permanece pendente na visão de mix e não recebe XP até existir uma fonte por produto/item. A aplicação não distribui arbitrariamente o valor devolvido entre as famílias.
