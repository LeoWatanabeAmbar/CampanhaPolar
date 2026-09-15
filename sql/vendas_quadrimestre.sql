-- Execute no SQL Editor do Supabase para habilitar a página Venda no Quadrimestre.
-- A função devolve uma linha por região com meta positiva na competência.
begin;

drop function if exists public.campanha_polar_carregar_vendas_regionais(date);

create or replace function public.campanha_polar_carregar_vendas_regionais(p_competencia date)
returns table (
    data_referencia date,
    regiao text,
    "time" text,
    meta numeric,
    realizado numeric,
    vendedores text
)
language plpgsql
security definer
set search_path = ''
set statement_timeout = '60s'
as $$
#variable_conflict use_column
declare
    v_hoje date := (current_timestamp at time zone 'America/Sao_Paulo')::date;
    v_fim_competencia date := (p_competencia + interval '1 month - 1 day')::date;
    v_data_limite date;
begin
    if (select auth.uid()) is null then
        raise exception 'AUTH_REQUIRED' using errcode = '42501';
    end if;
    if p_competencia is null
       or p_competencia <> date_trunc('month', p_competencia)::date
       or extract(year from p_competencia) <> 2026
       or extract(month from p_competencia) not in (9, 10, 11, 12) then
        raise exception 'INVALID_MONTH' using errcode = '22023';
    end if;

    v_data_limite := least(v_hoje, v_fim_competencia);

    return query
    with metas as (
        select
            trim(m.regiao)::text as regiao,
            case
                when count(distinct upper(trim(m.time))) = 1 then min(trim(m.time))::text
                else 'Múltiplos times'::text
            end as time_meta,
            sum(m.meta)::numeric as valor_meta
        from comercial_marts.metas_comerciais as m
        where m.data = p_competencia
          and m.meta > 0
          and nullif(trim(m.regiao), '') is not null
          and upper(trim(m.time)) in ('CANAIS', 'TIME NORTE', 'TIME SUL')
        group by trim(m.regiao)
    ),
    vendedores_dim as (
        select
            trim(v.vendedor_id)::text as vendedor_id,
            case when count(distinct trim(v.nome_vendedor)) = 1
                then min(trim(v.nome_vendedor))::text end as nome_vendedor,
            case when count(distinct trim(v.regiao)) = 1
                then min(trim(v.regiao))::text end as regiao,
            count(distinct trim(v.regiao)) = 1 as mapeamento_unico
        from comercial_marts.app_vendedor_regiao_time as v
        where nullif(trim(v.vendedor_id), '') is not null
        group by trim(v.vendedor_id)
    ),
    clientes_bloqueados as (
        select distinct trim(i.cliente_loja_id)::text as cliente_loja_id
        from comercial_marts.vw_clientes_inadimplentes as i
        where nullif(trim(i.cliente_loja_id), '') is not null
    ),
    pedido_contexto as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            max(f.data_emissao)::date as data_emissao,
            max(trim(f.cliente_id))::text as cliente_id,
            max(trim(f.loja_cliente_id))::text as loja_cliente_id
        from comercial_marts.fct_pedido_item as f
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and f.data_emissao >= p_competencia
          and f.data_emissao < (p_competencia + interval '1 month')::date
          and f.data_emissao <= v_data_limite
        group by trim(f.filial_id), trim(f.pedido_id)
    ),
    vendas_nao_bloqueadas as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_total, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_pedido_item as f
        inner join pedido_contexto as p
          on p.filial_id = trim(f.filial_id)
         and p.pedido_id = trim(f.pedido_id)
        left join clientes_bloqueados as b
          on b.cliente_loja_id = trim(f.cliente_id) || '-' || trim(f.loja_cliente_id)
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and b.cliente_loja_id is null
        group by
            trim(f.filial_id), trim(f.pedido_id),
            nullif(trim(f.vendedor_metricas_id), '')
    ),
    vendas_bloqueadas_faturadas as (
        select
            p.filial_id,
            p.pedido_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_item, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_faturamento_item as f
        inner join pedido_contexto as p
          on p.filial_id = trim(f.filial_id)
         and p.pedido_id = trim(f.pedido_id)
        inner join clientes_bloqueados as b
          on b.cliente_loja_id = p.cliente_id || '-' || p.loja_cliente_id
        where f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
        group by
            p.filial_id, p.pedido_id,
            nullif(trim(f.vendedor_metricas_id), '')
    ),
    vendas_brutas as (
        select * from vendas_nao_bloqueadas
        union all
        select * from vendas_bloqueadas_faturadas
    ),
    vendas_por_pedido_vendedor as (
        select
            v.filial_id,
            v.pedido_id,
            v.vendedor_id,
            sum(v.valor_bruto_elegivel)::numeric as valor_bruto_elegivel
        from vendas_brutas as v
        group by v.filial_id, v.pedido_id, v.vendedor_id
    ),
    notas_pedido as (
        select
            trim(f.nota_fiscal_id)::text as nota_fiscal_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            min(p.filial_id)::text as filial_id,
            min(p.pedido_id)::text as pedido_id,
            count(distinct (p.filial_id, p.pedido_id)) as quantidade_pedidos
        from comercial_marts.fct_faturamento_item as f
        inner join pedido_contexto as p
          on p.filial_id = trim(f.filial_id)
         and p.pedido_id = trim(f.pedido_id)
        where nullif(trim(f.nota_fiscal_id), '') is not null
        group by trim(f.nota_fiscal_id), nullif(trim(f.vendedor_metricas_id), '')
    ),
    devolucoes_por_pedido_vendedor as (
        select
            n.filial_id,
            n.pedido_id,
            n.vendedor_id,
            sum(coalesce(d.valor_devolucao_alocado, 0))::numeric as valor_devolvido
        from comercial_marts.fct_nota_devolucao as d
        inner join notas_pedido as n
          on n.nota_fiscal_id = trim(d.nota_fiscal_original_id)
         and n.vendedor_id is not distinct from nullif(trim(d.vendedor_metricas_id), '')
         and n.quantidade_pedidos = 1
        where d.data_devolucao is null or d.data_devolucao <= v_hoje
        group by n.filial_id, n.pedido_id, n.vendedor_id
    ),
    vendas_liquidas as (
        select
            v.filial_id,
            v.pedido_id,
            v.vendedor_id,
            greatest(
                v.valor_bruto_elegivel - coalesce(d.valor_devolvido, 0),
                0
            )::numeric as valor_liquido_elegivel
        from vendas_por_pedido_vendedor as v
        left join devolucoes_por_pedido_vendedor as d
          on d.filial_id = v.filial_id
         and d.pedido_id = v.pedido_id
         and d.vendedor_id is not distinct from v.vendedor_id
    ),
    vendas_regionais as (
        select
            vd.regiao,
            sum(v.valor_liquido_elegivel)::numeric as realizado,
            string_agg(
                distinct coalesce(vd.nome_vendedor, v.vendedor_id),
                ' · ' order by coalesce(vd.nome_vendedor, v.vendedor_id)
            )::text as vendedores
        from vendas_liquidas as v
        inner join vendedores_dim as vd
          on vd.vendedor_id = v.vendedor_id
         and vd.mapeamento_unico
         and nullif(vd.regiao, '') is not null
        where v.valor_liquido_elegivel > 0
        group by vd.regiao
    )
    select
        v_data_limite,
        m.regiao,
        m.time_meta,
        m.valor_meta,
        coalesce(v.realizado, 0)::numeric,
        coalesce(v.vendedores, 'Sem venda elegível')::text
    from metas as m
    left join vendas_regionais as v on v.regiao = m.regiao
    order by m.regiao;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_vendas_regionais(date)
    from public, anon;
grant execute on function public.campanha_polar_carregar_vendas_regionais(date)
    to authenticated;

commit;

notify pgrst, 'reload schema';
