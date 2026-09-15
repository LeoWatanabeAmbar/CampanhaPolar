-- Previa somente leitura: uma linha por grupo comercial, data e linha de mix.
-- Nao concede XP nem conclui elegibilidade por minimo, segmento ou vendedor.
-- Nao aplica inadimplencia/parte faturada, definidas em elegibilidadeVendas.md.
-- Nao abate devolucoes; a fonte observada nao detalha produto/item devolvido.
-- Parametros psycopg2: produtos_mix e grupos_ka recebem JSON dos CSVs locais.
-- Confirmado em 14/09/2026: pedidos do mesmo grupo e data formam um evento unico
-- e seus valores elegiveis sao somados por linha; dias diferentes nao se acumulam.
-- Com dois vendedores identificados no evento, cada um recebe 50% do XP da linha.
with produtos_mix as (
    select produto_id, grupo_mix
    from jsonb_to_recordset(%(produtos_mix)s::jsonb)
        as m(produto_id text, grupo_mix text)
),
grupos_ka as (
    select grupo_comercial_id
    from jsonb_to_recordset(%(grupos_ka)s::jsonb)
        as k(grupo_comercial_id text)
),
itens_mix as (
    select
        f.filial_id,
        f.pedido_id,
        f.data_emissao,
        nullif(trim(f.grupo_comercial_id), '') as grupo_comercial_id,
        m.grupo_mix,
        f.produto_id,
        nullif(trim(f.vendedor_metricas_id), '') as vendedor_metricas_id,
        f.valor_bruto_total,
        f.is_triangulacao,
        f.executivo_id
    from comercial_marts.fct_pedido_item f
    join produtos_mix m on m.produto_id = f.produto_id
    where f.is_item_valido_metricas is true
      and f.is_venda_comercial is true
),
eventos_linha_dia as (
    select
        case
            when grupo_comercial_id is not null then grupo_comercial_id
            else '__SEM_GRUPO__:' || coalesce(trim(filial_id), '?') || ':'
                || coalesce(trim(pedido_id), '?')
        end as evento_grupo_chave,
        grupo_comercial_id,
        data_emissao,
        grupo_mix,
        string_agg(
            distinct coalesce(trim(filial_id), '?') || '/' || coalesce(trim(pedido_id), '?'),
            ', ' order by coalesce(trim(filial_id), '?') || '/' || coalesce(trim(pedido_id), '?')
        ) as pedidos_evento,
        count(distinct (filial_id, pedido_id)) as quantidade_pedidos_evento,
        string_agg(distinct produto_id, ', ' order by produto_id) as produtos,
        string_agg(distinct vendedor_metricas_id, ', ' order by vendedor_metricas_id)
            as vendedores_alocados,
        count(distinct vendedor_metricas_id) as quantidade_vendedores,
        bool_or(vendedor_metricas_id is null) as tem_vendedor_ausente,
        sum(valor_bruto_total) as valor_linha_evento_soma_alocacoes,
        bool_or(valor_bruto_total is null) as tem_valor_ausente,
        bool_or(is_triangulacao) as tem_triangulacao,
        bool_or(is_triangulacao and nullif(trim(executivo_id), '') is null)
            as tem_triangulacao_sem_executivo,
        bool_or(nullif(trim(filial_id), '') is null or nullif(trim(pedido_id), '') is null)
            as tem_pedido_sem_identificacao
    from itens_mix
    group by evento_grupo_chave, grupo_comercial_id, data_emissao, grupo_mix
),
historico as (
    select
        e.*,
        min(data_emissao) over (
            partition by evento_grupo_chave, grupo_mix
        ) as primeira_data_linha_observada,
        bool_or(data_emissao is null) over (
            partition by evento_grupo_chave, grupo_mix
        ) as historico_tem_data_ausente
    from eventos_linha_dia e
),
classificado as (
    select
        h.*,
        g.nome_grupo_comercial,
        case
            when h.grupo_comercial_id is null or g.grupo_comercial_id is null then null
            else k.grupo_comercial_id is not null
        end as is_ka,
        case
            when h.grupo_comercial_id is null or g.grupo_comercial_id is null
                then 'pendente_grupo_comercial'
            when k.grupo_comercial_id is not null then 'excluido_ka'
            when h.historico_tem_data_ausente then 'pendente_data_historica'
            when h.data_emissao > h.primeira_data_linha_observada
                then 'linha_com_compra_anterior'
            when h.tem_pedido_sem_identificacao then 'pendente_identificacao_pedido'
            else 'candidato_primeira_compra_linha'
        end as resultado_previa
    from historico h
    left join comercial_marts.dim_grupo_comercial g
        on g.grupo_comercial_id = h.grupo_comercial_id
    left join grupos_ka k on k.grupo_comercial_id = h.grupo_comercial_id
    where h.data_emissao >= date '2026-09-01'
      and h.data_emissao < date '2027-01-01'
      and h.data_emissao <= current_date
)
select
    data_emissao,
    grupo_comercial_id,
    nome_grupo_comercial,
    grupo_mix,
    pedidos_evento,
    quantidade_pedidos_evento,
    produtos,
    vendedores_alocados,
    quantidade_vendedores,
    tem_vendedor_ausente,
    valor_linha_evento_soma_alocacoes,
    tem_valor_ausente,
    tem_triangulacao,
    tem_triangulacao_sem_executivo,
    primeira_data_linha_observada,
    historico_tem_data_ausente,
    is_ka,
    resultado_previa,
    case
        when tem_vendedor_ausente then 'pendente_vendedor_ausente'
        when quantidade_vendedores = 1 then 'um_vendedor_xp_integral'
        when quantidade_vendedores = 2 then 'dois_vendedores_xp_meio_a_meio'
        else 'pendente_quantidade_vendedores'
    end as situacao_atribuicao,
    case
        when not tem_vendedor_ausente and quantidade_vendedores = 1 then 1.0
        when not tem_vendedor_ausente and quantidade_vendedores = 2 then 0.5
    end as fracao_xp_por_vendedor
from classificado
order by data_emissao, evento_grupo_chave, grupo_mix;
