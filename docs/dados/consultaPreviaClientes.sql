-- Diagnostico somente leitura de novos e reativados, sem concessao de XP.
-- Parametro psycopg2 times_segmentos: JSON dos registros de timesSegmentos.csv.
-- Usa todos os produtos comerciais validos da fonte, nao apenas o mix.
-- O segmento vem do cadastro atual; emissao = implantacao, referencia confirmada.
-- Diagnostico sem o filtro de inadimplencia/parte faturada definido em 14/09/2026.
-- Nao abate devolucoes posteriores; ver elegibilidadeVendas.md.
-- Confirmado em 14/09/2026: pedidos do mesmo grupo e data formam um evento unico.
-- O limite de 6/12 meses e inclusivo e o XP de triangulacao e dividido em 50%.
-- Um evento diario com dois vendedores identificados tambem divide o XP em 50%.
with times_segmentos as (
    select time, segmento_campanha
    from jsonb_to_recordset(%(times_segmentos)s::jsonb)
        as t(time text, segmento_campanha text)
),
itens as (
    select
        f.filial_id,
        f.pedido_id,
        f.data_emissao,
        nullif(trim(f.grupo_comercial_id), '') as grupo_comercial_id,
        nullif(trim(f.vendedor_metricas_id), '') as vendedor_id,
        f.valor_bruto_total,
        v.time,
        t.segmento_campanha
    from comercial_marts.fct_pedido_item f
    left join comercial_marts.app_vendedor_regiao_time v
        on v.vendedor_id = f.vendedor_metricas_id
    left join times_segmentos t on t.time = trim(v.time)
    where f.is_item_valido_metricas is true
      and f.is_venda_comercial is true
),
eventos_diarios as (
    select
        case
            when grupo_comercial_id is not null then grupo_comercial_id
            else '__SEM_GRUPO__:' || coalesce(trim(filial_id), '?') || ':'
                || coalesce(trim(pedido_id), '?')
        end as evento_grupo_chave,
        grupo_comercial_id,
        data_emissao,
        string_agg(
            distinct coalesce(trim(filial_id), '?') || '/' || coalesce(trim(pedido_id), '?'),
            ', ' order by coalesce(trim(filial_id), '?') || '/' || coalesce(trim(pedido_id), '?')
        ) as pedidos_evento,
        count(distinct (filial_id, pedido_id)) as quantidade_pedidos_evento,
        string_agg(distinct vendedor_id, ', ' order by vendedor_id) as vendedores_alocados,
        count(distinct vendedor_id) as quantidade_vendedores,
        bool_or(vendedor_id is null) as tem_vendedor_ausente,
        string_agg(distinct time, ', ' order by time) as times_cadastro_atual,
        case
            when count(distinct segmento_campanha) = 1
             and not bool_or(segmento_campanha is null)
            then min(segmento_campanha)
        end as segmento_campanha,
        count(distinct segmento_campanha) as quantidade_segmentos,
        bool_or(segmento_campanha is null) as tem_segmento_desconhecido,
        bool_or(nullif(trim(filial_id), '') is null or nullif(trim(pedido_id), '') is null)
            as tem_pedido_sem_identificacao,
        sum(valor_bruto_total) as valor_evento_soma_alocacoes
    from itens
    group by evento_grupo_chave, grupo_comercial_id, data_emissao
),
perfil_grupo as (
    select
        grupo_comercial_id,
        min(data_emissao) as primeira_compra_observada,
        bool_or(data_emissao is null) as historico_tem_data_ausente
    from eventos_diarios
    where grupo_comercial_id is not null
    group by grupo_comercial_id
),
historico as (
    select
        e.*,
        lag(data_emissao) over (
            partition by evento_grupo_chave order by data_emissao
        ) as ultima_compra_em_data_anterior
    from eventos_diarios e
),
base as (
    select
        h.*,
        g.nome_grupo_comercial,
        g.grupo_comercial_id is not null as grupo_identificado,
        p.primeira_compra_observada,
        p.historico_tem_data_ausente,
        h.data_emissao - h.ultima_compra_em_data_anterior as dias_sem_compra,
        case h.segmento_campanha
            when 'Construção' then 12
            when 'Canais' then 6
        end as meses_inatividade_exigidos
    from historico h
    left join perfil_grupo p on p.grupo_comercial_id = h.grupo_comercial_id
    left join comercial_marts.dim_grupo_comercial g
        on g.grupo_comercial_id = h.grupo_comercial_id
    where h.data_emissao >= date '2026-09-01'
      and h.data_emissao < date '2027-01-01'
      and h.data_emissao <= current_date
),
avaliado as (
    select *,
        case
            when meses_inatividade_exigidos is not null
            then (data_emissao - make_interval(months => meses_inatividade_exigidos))::date
        end as data_limite_reativacao_proposta
    from base
)
select *,
    case
        when not grupo_identificado then 'pendente_grupo_comercial'
        when tem_pedido_sem_identificacao then 'pendente_identificacao_pedido'
        when historico_tem_data_ausente then 'pendente_data_historica'
        when ultima_compra_em_data_anterior is null then 'novo_no_historico'
        when segmento_campanha is null then 'pendente_segmento'
        when ultima_compra_em_data_anterior <= data_limite_reativacao_proposta
            then 'candidato_reativado'
        else 'ativo'
    end as resultado_previa,
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
from avaliado
order by data_emissao, evento_grupo_chave;
