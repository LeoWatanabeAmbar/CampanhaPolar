# Calendário de dias úteis da campanha

**Confirmado pelo usuário em 14/09/2026:** contar dias de segunda a sexta, descontando os feriados nacionais. Esse calendário será usado para a meta diária, a meta parcial até a data de referência e o atingimento que determina os XP de vendas durante o mês.

## Referência de feriados

O arquivo [feriadosNacionaisCampanha2026.csv](feriadosNacionaisCampanha2026.csv) contém os seis feriados nacionais de setembro a dezembro de 2026, com data no formato `YYYY-MM-DD`. A referência foi conferida em 14/09/2026 na [Portaria MGI nº 11.460, publicada no DOU de 30/12/2025](https://legis.sigepe.gov.br/sigepe-bgp-ws-legis/legis-service/download/?id=0026440285-ALPDF%2F2025).

Usar dessa referência somente os feriados nacionais no recorte da campanha. Pontos facultativos e feriados estaduais ou municipais não entram no calendário escolhido pelo usuário. Feriado que cai no sábado ou domingo não reduz novamente a contagem: 15/11/2026 já é domingo. Esta é uma referência para o cálculo da campanha, sem definir a escala de trabalho da empresa.

| Mês de 2026 | Dias úteis, após excluir feriados nacionais |
| --- | ---: |
| Setembro | 21 |
| Outubro | 21 |
| Novembro | 19 |
| Dezembro | 22 |

As contagens foram calculadas localmente com as datas do CSV. O arquivo cobre apenas setembro a dezembro de 2026; outras competências exigem seu calendário correspondente.

## Data de referência e contagem

Convenção adotada nesta proposta: usar a data local de São Paulo e incluir a data de referência nos dias úteis decorridos, quando for útil. A meta parcial representa o esperado até o fim desse dia; durante o expediente, o realizado representa o que já está disponível na fonte. Exibir a data/hora da atualização das vendas para tornar essa comparação compreensível.

- `dias_uteis_mes`: dias úteis entre o primeiro e o último dia do mês, incluindo ambos quando úteis.
- `dias_uteis_decorridos`: dias úteis do mês até a data de referência, incluindo essa data quando útil.
- `dias_uteis_restantes`: dias úteis posteriores à data de referência até o fim do mês.
- Portanto, `dias_uteis_mes = dias_uteis_decorridos + dias_uteis_restantes` para uma referência dentro do mês. O dia de referência não é contado nos dois grupos.
- Em fins de semana e feriados, a meta parcial não avança. Em consulta de mês encerrado, limitar a referência ao último dia desse mês. Antes do início do mês, há zero dias decorridos.

Exemplo em **14/09/2026**, incluindo o dia 14: setembro tem **21 dias úteis**, sendo **9 decorridos e 12 restantes**. As fórmulas e um exemplo de meta e vendas estão em [Dados de metas](dadoMeta.md).
