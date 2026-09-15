-- Execute no SQL Editor do Supabase para habilitar a página Clientes reativados.
-- A função usa a situação atual das fontes e fica disponível somente para usuários autenticados.
begin;

drop function if exists public.campanha_polar_carregar_clientes_reativados(date);

create or replace function public.campanha_polar_carregar_clientes_reativados(p_competencia date)
returns table (
    grupo_comercial_id text,
    nome_grupo_comercial text,
    data_reativacao date,
    data_ultima_compra date,
    prazo_meses integer,
    pedidos text,
    vendedor text,
    regiao text,
    segmento text,
    situacao_atribuicao text,
    xp numeric
)
language plpgsql
security definer
set search_path = ''
set statement_timeout = '60s'
as $$
#variable_conflict use_column
begin
    if (select auth.uid()) is null then
        raise exception 'AUTH_REQUIRED' using errcode = '42501';
    end if;
    if p_competencia is not null and (
       p_competencia <> date_trunc('month', p_competencia)::date
       or extract(year from p_competencia) <> 2026
       or extract(month from p_competencia) not in (9, 10, 11, 12)
    ) then
        raise exception 'INVALID_MONTH' using errcode = '22023';
    end if;

    return query
    with vendedores_dim as (
        select
            trim(v.vendedor_id)::text as vendedor_id,
            case when count(distinct trim(v.nome_vendedor)) = 1
                then min(trim(v.nome_vendedor))::text end as nome_vendedor,
            case when count(distinct trim(v.regiao)) = 1
                then min(trim(v.regiao))::text end as regiao,
            case when count(distinct upper(trim(v.time))) = 1
                then min(trim(v.time))::text end as time_vendedor,
            count(distinct trim(v.regiao)) = 1
                and count(distinct upper(trim(v.time))) = 1 as mapeamento_unico
        from comercial_marts.app_vendedor_regiao_time as v
        where nullif(trim(v.vendedor_id), '') is not null
        group by trim(v.vendedor_id)
    ),
    grupos_dim as (
        select
            trim(g.grupo_comercial_id)::text as grupo_comercial_id,
            max(trim(g.nome_grupo_comercial))::text as nome_grupo_comercial
        from comercial_marts.dim_grupo_comercial as g
        where nullif(trim(g.grupo_comercial_id), '') is not null
        group by trim(g.grupo_comercial_id)
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
            max(trim(f.loja_cliente_id))::text as loja_cliente_id,
            max(nullif(trim(f.grupo_comercial_id), ''))::text as grupo_comercial_id
        from comercial_marts.fct_pedido_item as f
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and f.data_emissao >= date '2022-01-01'
          and f.data_emissao <= current_date
        group by trim(f.filial_id), trim(f.pedido_id)
    ),
    grupos_com_data_pendente as (
        select distinct nullif(trim(f.grupo_comercial_id), '')::text as grupo_comercial_id
        from comercial_marts.fct_pedido_item as f
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and f.data_emissao is null
          and nullif(trim(f.grupo_comercial_id), '') is not null
    ),
    vendas_nao_bloqueadas as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            f.data_emissao::date as data_emissao,
            nullif(trim(f.grupo_comercial_id), '')::text as grupo_comercial_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_total, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_pedido_item as f
        left join clientes_bloqueados as b
          on b.cliente_loja_id = trim(f.cliente_id) || '-' || trim(f.loja_cliente_id)
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and b.cliente_loja_id is null
          and f.data_emissao >= date '2022-01-01'
          and f.data_emissao <= current_date
        group by
            trim(f.filial_id), trim(f.pedido_id), f.data_emissao,
            nullif(trim(f.grupo_comercial_id), ''),
            nullif(trim(f.vendedor_metricas_id), '')
    ),
    vendas_bloqueadas_faturadas as (
        select
            p.filial_id,
            p.pedido_id,
            p.data_emissao,
            p.grupo_comercial_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_item, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_faturamento_item as f
        inner join pedido_contexto as p
          on p.filial_id = trim(f.filial_id)
         and p.pedido_id = trim(f.pedido_id)
        inner join clientes_bloqueados as b
          on b.cliente_loja_id = trim(f.cliente_id) || '-' || trim(f.loja_cliente_id)
        where f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and p.data_emissao >= date '2022-01-01'
          and p.data_emissao <= current_date
        group by
            p.filial_id, p.pedido_id, p.data_emissao, p.grupo_comercial_id,
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
            v.data_emissao,
            v.grupo_comercial_id,
            v.vendedor_id,
            sum(v.valor_bruto_elegivel)::numeric as valor_bruto_elegivel
        from vendas_brutas as v
        group by v.filial_id, v.pedido_id, v.data_emissao, v.grupo_comercial_id, v.vendedor_id
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
    grupos_com_devolucao_pendente as (
        select distinct nullif(trim(d.grupo_comercial_id), '')::text as grupo_comercial_id
        from comercial_marts.fct_nota_devolucao as d
        left join notas_pedido as n
          on n.nota_fiscal_id = trim(d.nota_fiscal_original_id)
         and n.vendedor_id is not distinct from nullif(trim(d.vendedor_metricas_id), '')
         and n.quantidade_pedidos = 1
        where nullif(trim(d.grupo_comercial_id), '') is not null
          and n.nota_fiscal_id is null
          and (d.data_devolucao is null or d.data_devolucao <= current_date)
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
        where d.data_devolucao is null or d.data_devolucao <= current_date
        group by n.filial_id, n.pedido_id, n.vendedor_id
    ),
    vendas_liquidas as (
        select
            v.*,
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
    alocacoes as (
        select
            v.*,
            vd.nome_vendedor,
            vd.regiao,
            case
                when upper(trim(vd.time_vendedor)) in ('TIME NORTE', 'TIME SUL') then 'Construção'
                when upper(trim(vd.time_vendedor)) = 'CANAIS' then 'Canais'
            end::text as segmento_campanha,
            coalesce(vd.mapeamento_unico, false) as mapeamento_unico,
            exists (
                select 1
                from comercial_marts.metas_comerciais as m
                where m.data = date_trunc('month', v.data_emissao)::date
                  and m.meta > 0
                  and trim(m.regiao) = vd.regiao
                  and upper(trim(m.time)) in ('CANAIS', 'TIME NORTE', 'TIME SUL')
            ) as is_regiao_participante
        from vendas_liquidas as v
        left join vendedores_dim as vd on vd.vendedor_id = v.vendedor_id
        where v.valor_liquido_elegivel > 0
          and v.grupo_comercial_id is not null
    ),
    eventos as (
        select
            a.grupo_comercial_id,
            a.data_emissao,
            string_agg(
                distinct a.filial_id || '/' || a.pedido_id,
                ' · ' order by a.filial_id || '/' || a.pedido_id
            )::text as pedidos,
            count(distinct (a.filial_id, a.pedido_id)) as quantidade_pedidos,
            string_agg(
                distinct coalesce(a.nome_vendedor, a.vendedor_id, 'Não identificado'),
                ' · ' order by coalesce(a.nome_vendedor, a.vendedor_id, 'Não identificado')
            )::text as vendedores,
            string_agg(distinct a.regiao, ' · ' order by a.regiao)::text as regioes,
            case when count(distinct a.segmento_campanha) = 1
                then min(a.segmento_campanha)::text else 'Múltiplos'::text end as segmento,
            sum(a.valor_liquido_elegivel)::numeric as valor_liquido_elegivel,
            count(distinct a.vendedor_id) as quantidade_vendedores,
            bool_or(a.vendedor_id is null) as tem_vendedor_ausente,
            bool_and(a.mapeamento_unico and a.segmento_campanha is not null) as mapeamento_valido,
            count(distinct a.segmento_campanha) as quantidade_segmentos,
            bool_or(a.is_regiao_participante) as tem_regiao_participante,
            bool_and(a.is_regiao_participante) as todas_regioes_participantes
        from alocacoes as a
        group by a.grupo_comercial_id, a.data_emissao
    ),
    detalhes as (
        select
            a.grupo_comercial_id,
            a.data_emissao,
            a.vendedor_id,
            coalesce(a.nome_vendedor, a.vendedor_id, 'Não identificado')::text as vendedor,
            coalesce(a.regiao, '')::text as regiao,
            string_agg(
                distinct a.filial_id || '/' || a.pedido_id,
                ' · ' order by a.filial_id || '/' || a.pedido_id
            )::text as pedidos
        from alocacoes as a
        group by
            a.grupo_comercial_id,
            a.data_emissao,
            a.vendedor_id,
            coalesce(a.nome_vendedor, a.vendedor_id, 'Não identificado'),
            coalesce(a.regiao, '')
    ),
    sequencia as (
        select
            e.*,
            lag(e.data_emissao) over (
                partition by e.grupo_comercial_id
                order by e.data_emissao
            )::date as data_ultima_compra
        from eventos as e
    ),
    candidatos as (
        select
            s.*,
            case
                when s.segmento = 'Canais' then 6
                when s.segmento = 'Construção' then 12
            end::integer as prazo_meses
        from sequencia as s
        inner join grupos_dim as g on g.grupo_comercial_id = s.grupo_comercial_id
        left join grupos_com_data_pendente as dp on dp.grupo_comercial_id = s.grupo_comercial_id
        left join grupos_com_devolucao_pendente as dv on dv.grupo_comercial_id = s.grupo_comercial_id
        where s.data_emissao >= date '2026-09-01'
          and s.data_emissao < date '2027-01-01'
          and (
              p_competencia is null
              or (
                  s.data_emissao >= p_competencia
                  and s.data_emissao < (p_competencia + interval '1 month')::date
              )
          )
          and s.data_ultima_compra is not null
          and (
              (s.segmento = 'Canais'
               and s.data_ultima_compra <= (s.data_emissao - interval '6 months')::date)
              or
              (s.segmento = 'Construção'
               and s.data_ultima_compra <= (s.data_emissao - interval '12 months')::date)
          )
          and s.tem_regiao_participante
          and dp.grupo_comercial_id is null
          and dv.grupo_comercial_id is null
    ),
    reativados as (
        select c.*
        from (
            select
                candidatos.*,
                row_number() over (
                    partition by candidatos.grupo_comercial_id
                    order by candidatos.data_emissao
                ) as ordem_reativacao
            from candidatos
        ) as c
        where c.ordem_reativacao = 1
    )
    select
        r.grupo_comercial_id,
        g.nome_grupo_comercial,
        r.data_emissao as data_reativacao,
        r.data_ultima_compra,
        r.prazo_meses,
        d.pedidos,
        d.vendedor,
        d.regiao,
        r.segmento,
        case
            when r.tem_vendedor_ausente then 'Pendente: vendedor não identificado'
            when r.quantidade_vendedores not in (1, 2) then 'Pendente: quantidade de vendedores'
            when not r.mapeamento_valido then 'Pendente: região ou segmento'
            when r.quantidade_segmentos <> 1 then 'Pendente: segmentos divergentes'
            when not r.todas_regioes_participantes then 'Pendente: região sem meta'
            when r.quantidade_vendedores = 1 then 'Integral'
            else 'Divisão 50/50'
        end::text as situacao_atribuicao,
        case
            when not r.tem_vendedor_ausente
             and r.quantidade_vendedores in (1, 2)
             and r.mapeamento_valido
             and r.quantidade_segmentos = 1
             and r.todas_regioes_participantes
            then 8.0 / r.quantidade_vendedores else 0
        end::numeric as xp
    from reativados as r
    inner join grupos_dim as g on g.grupo_comercial_id = r.grupo_comercial_id
    inner join detalhes as d
      on d.grupo_comercial_id = r.grupo_comercial_id
     and d.data_emissao = r.data_emissao
    order by r.data_emissao, g.nome_grupo_comercial, d.vendedor, d.regiao;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_clientes_reativados(date)
    from public, anon;
grant execute on function public.campanha_polar_carregar_clientes_reativados(date)
    to authenticated;

commit;

notify pgrst, 'reload schema';
