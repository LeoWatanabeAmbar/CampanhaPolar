# Grupos comerciais KA

**Fonte:** lista enviada pelo usuário em imagem em 10/09/2026 para a campanha Polar. Os 16 nomes tiveram correspondência exata, após normalização de caixa e espaços externos, em `comercial_marts.dim_grupo_comercial`, consultada no Supabase em 10/09/2026, somente para leitura.

O arquivo [gruposKA.csv](gruposKA.csv) registra os códigos e nomes para futura implementação. Os códigos devem ser tratados como texto. A lista foi registrada localmente; nenhuma tabela ou classificação foi alterada no Supabase.

| Código do grupo | Nome confirmado |
| --- | --- |
| `C02` | MRV |
| `C45` | TENDA |
| `CMN` | CURY CONSTRUTORA |
| `C49` | DIRECIONAL |
| `C48` | CYRELA |
| `C15` | PLANO & PLANO |
| `CE1` | ECON CONSTRUTORA |
| `C01` | PACAEMBU |
| `C57` | TRISUL |
| `C65` | BRZ |
| `CTX` | CONSTRUTORA P4 |
| `E287` | LAVVI |
| `CII` | GRAAL ENGENHARIA |
| `CGI` | TOLEDO FERRARI |
| `C16` | VIBRA |
| `C03` | EMCCAMP |

## Aplicação na campanha

- Relacionar a lista com `fct_pedido_item.grupo_comercial_id`, usando o código exato do grupo. O nome serve para exibição e conferência.
- Todos os clientes/lojas pertencentes a um grupo listado recebem `is_ka = true` na tabela derivada.
- Para grupo identificado e válido no cadastro, mas fora desta lista, usar `is_ka = false`, considerando a lista fornecida como referência da campanha.
- Grupo ausente ou código sem correspondência no cadastro fica com `is_ka = null` e motivo de pendência. **Confirmado pelo usuário em 14/09/2026:** aguardar a correção do cadastro. Não transformar falta de identificação em não KA nem substituir o grupo pelo cliente individual para liberar a pontuação de mix.
- `is_ka = true` implica `is_mix_elegivel = false`, com motivo `grupo_comercial_ka`, mesmo que haja produto novo e mínimo atingido no pedido.
- A exclusão KA do regulamento se aplica ao indicador de expansão de mix. Ela não exclui automaticamente o pedido das vendas nem dos indicadores de novos/reativados; estes seguem suas próprias regras.

**Confirmado pelo usuário em 14/09/2026:** esta lista é fixa para toda a campanha de 2026. Não haverá entrada ou saída de grupos KA entre setembro e dezembro. A data de recebimento não é um corte: aplicar a lista a todo o período da campanha. Se outra fonte indicar mudança durante o período, registrar a divergência para correção cadastral e manter esta versão na apuração.
