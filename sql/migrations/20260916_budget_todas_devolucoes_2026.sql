-- Atualiza o Budget anual para descontar todas as notas devolvidas em 2026.
-- A nota original pode pertencer a qualquer ano e nao precisa estar vinculada a um pedido de 2026.
-- Execute uma vez no SQL Editor do Supabase em instalacoes existentes.
begin;

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
    with pedido_contexto as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id
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
    vendas_brutas as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_total, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_pedido_item as f
        inner join pedido_contexto as p
          on p.filial_id = trim(f.filial_id)
         and p.pedido_id = trim(f.pedido_id)
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
        group by
            trim(f.filial_id), trim(f.pedido_id),
            nullif(trim(f.vendedor_metricas_id), '')
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
    vendas_2026 as (
        select coalesce(sum(v.valor_bruto_elegivel), 0)::numeric as valor_bruto
        from vendas_por_pedido_vendedor as v
    ),
    devolucoes_2026 as (
        select coalesce(sum(d.valor_devolucao_alocado), 0)::numeric as valor_devolvido
        from comercial_marts.fct_nota_devolucao as d
        where d.data_devolucao >= date '2026-01-01'
          and d.data_devolucao <= v_hoje
    )
    select
        v_hoje,
        (v.valor_bruto - d.valor_devolvido)::numeric
    from vendas_2026 as v
    cross join devolucoes_2026 as d;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_budget_anual()
    from public, anon;
grant execute on function public.campanha_polar_carregar_budget_anual()
    to authenticated;

commit;

notify pgrst, 'reload schema';


