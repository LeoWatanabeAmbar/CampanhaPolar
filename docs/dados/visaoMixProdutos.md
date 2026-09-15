# Visão de mix de produtos

**Implementada em 15/09/2026:** a página **Mix de produtos** consulta todas as compras das famílias mapeadas durante a campanha e explica a elegibilidade de cada evento. Ela abrange Hydrofix, CPP 009, Grelha + Porta Grelha e Suporte de Bancada.

## Conteúdo da página

- tabela inicial com uma linha por região; dentro da célula da lista, cada expansão confirmada aparece abaixo da anterior, enquanto quantidade e XP permanecem únicos para a região;
- apenas filtro de região no detalhamento;
- data da compra, data da primeira compra histórica da família, códigos dos produtos, pedidos reunidos no dia e família;
- uma linha por vendedor e região, com segmento, valor, mínimo, resultado e XP.

Na exibição dos pedidos, o prefixo da filial padrão `01101/` fica oculto. Pedidos de outras filiais preservam sua identificação completa.

O valor dos pedidos do mesmo grupo, data e família é somado antes de verificar o mínimo. Cada primeira compra de família que cumprir as regras gera 10 XP. Um vendedor recebe 10 XP; exatamente dois aparecem em duas linhas de 5 XP cada. O indicador não possui teto individual. O detalhamento também mostra clientes KA, famílias compradas anteriormente, compras abaixo do mínimo e pendências. Somente eventos elegíveis entram no resumo regional.

## Consulta e regras aplicadas

A função `public.campanha_polar_carregar_mix_produtos(date)`, criada por [mix_produtos.sql](../../sql/mix_produtos.sql), é executada pela Data API com o JWT do usuário autenticado. Os 23 códigos e os 16 grupos KA estão versionados no SQL conforme [produtosMix.csv](produtosMix.csv) e [gruposKA.csv](gruposKA.csv).

O script recria a função quando seu contrato de retorno muda e, ao final, solicita a recarga do cache de schema da Data API. A diretiva de resolução de nomes da função prioriza as colunas dos CTEs e evita conflito com os nomes das colunas de retorno do PL/pgSQL.

Os mínimos aplicados são:

| Segmento | Família | Mínimo |
| --- | --- | ---: |
| Construção | Hydrofix | R$ 3.000,00 |
| Construção | Grelha + Porta Grelha | R$ 6.000,00 |
| Construção | Suporte de Bancada | R$ 9.000,00 |
| Canais | CPP 009 | R$ 2.200,00 |
| Canais | Grelha + Porta Grelha | R$ 1.000,00 |
| Canais | Suporte de Bancada | R$ 1.000,00 |

A consulta usa o histórico desde 01/01/2022 para identificar a primeira compra da família, mas devolve todas as compras ocorridas entre setembro e dezembro de 2026. Ela considera somente itens elegíveis e usa a parte faturada quando o cliente está bloqueado por inadimplência. A primeira compra da família impede pontuação posterior mesmo quando não alcança o mínimo; essas compras posteriores aparecem como `Sem XP: família comprada anteriormente`.

## Devoluções

Uma devolução só provoca a reavaliação da expansão quando sua nota fiscal original pertence a um dos pedidos que formam o evento de mix. A consulta liga `fct_nota_devolucao.nota_fiscal_original_id` a `fct_faturamento_item.nota_fiscal_id` e, por essa nota, identifica o pedido implantado. Devoluções de outros pedidos do mesmo grupo comercial não alteram o evento.

Como `fct_nota_devolucao` não identifica o produto ou item devolvido, o evento diretamente afetado fica como `Pendente: devolução na nota do pedido` e sem XP até ser possível conferir se o valor mínimo da família continua atendido. A aplicação não distribui arbitrariamente a devolução entre produtos ou famílias.
