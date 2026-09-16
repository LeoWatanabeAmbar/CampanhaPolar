-- Execute no SQL Editor do Supabase para habilitar o gráfico do Budget Anual.
-- O realizado segue as regras de elegibilidade de vendas confirmadas para a campanha.
begin;

drop function if exists public.campanha_polar_carregar_budget_anual();

create or replace function public.campanha_polar_carregar_budget_anual()
returns table (
    data_referencia date,
    realizado numeric
)
language plpgsql
security definer
set search_path = ''
set statement_timeout = '60s'
as $$
#variable_conflict use_column
declare
    v_hoje date := (current_timestamp at time zone 'America/Sao_Paulo')::date;
begin
    if (select auth.uid()) is null then
        raise exception 'AUTH_REQUIRED' using errcode = '42501';
    end if;

    return query
    with clientes_bloqueados as (
        select distinct trim(i.cliente_loja_id)::text as cliente_loja_id
        from comercial_marts.vw_clientes_inadimplentes as i
        where nullif(trim(i.cliente_loja_id), '') is not null
    ),
    pedido_contexto as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            max(trim(f.cliente_id))::text as cliente_id,
            max(trim(f.loja_cliente_id))::text as loja_cliente_id
        from comercial_marts.fct_pedido_item as f
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and f.data_emissao >= date '2026-01-01'
          and f.data_emissao <= v_hoje
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
        select greatest(
            v.valor_bruto_elegivel - coalesce(d.valor_devolvido, 0),
            0
        )::numeric as valor_liquido_elegivel
        from vendas_por_pedido_vendedor as v
        left join devolucoes_por_pedido_vendedor as d
          on d.filial_id = v.filial_id
         and d.pedido_id = v.pedido_id
         and d.vendedor_id is not distinct from v.vendedor_id
    )
    select
        v_hoje,
        coalesce(sum(v.valor_liquido_elegivel), 0)::numeric
    from vendas_liquidas as v;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_budget_anual()
    from public, anon;
grant execute on function public.campanha_polar_carregar_budget_anual()
    to authenticated;

commit;

notify pgrst, 'reload schema';
