-- Execute no SQL Editor do Supabase para habilitar a página Mix de produtos.
-- A função usa a situação atual das fontes e fica disponível somente para usuários autenticados.
begin;

create or replace function public.campanha_polar_carregar_mix_produtos(p_competencia date)
returns table (
    grupo_comercial_id text,
    nome_grupo_comercial text,
    data_expansao date,
    grupo_mix text,
    produtos text,
    pedidos text,
    quantidade_pedidos bigint,
    vendedores text,
    regioes text,
    segmento text,
    valor_linha_elegivel numeric,
    valor_minimo numeric,
    quantidade_vendedores bigint,
    situacao_evento text,
    xp_evento numeric,
    xp_por_vendedor numeric
)
language plpgsql
security definer
set search_path = ''
as $$
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
    with produtos_mix(produto_id, grupo_mix) as (
        values
            ('002920'::text, 'Hydrofix'::text),
            ('002921', 'Hydrofix'),
            ('000010', 'CPP 009'),
            ('002736', 'CPP 009'),
            ('002968', 'Grelha + Porta Grelha'),
            ('002969', 'Grelha + Porta Grelha'),
            ('001626', 'Suporte de Bancada'),
            ('001627', 'Suporte de Bancada'),
            ('001628', 'Suporte de Bancada'),
            ('002054', 'Suporte de Bancada'),
            ('002055', 'Suporte de Bancada'),
            ('002056', 'Suporte de Bancada'),
            ('002064', 'Suporte de Bancada'),
            ('002065', 'Suporte de Bancada'),
            ('002066', 'Suporte de Bancada'),
            ('002893', 'Suporte de Bancada'),
            ('002894', 'Suporte de Bancada'),
            ('002895', 'Suporte de Bancada'),
            ('002917', 'Suporte de Bancada'),
            ('002918', 'Suporte de Bancada'),
            ('002919', 'Suporte de Bancada'),
            ('003026', 'Suporte de Bancada'),
            ('003027', 'Suporte de Bancada')
    ),
    grupos_ka(grupo_comercial_id) as (
        values
            ('C02'::text), ('C45'), ('CMN'), ('C49'),
            ('C48'), ('C15'), ('CE1'), ('C01'),
            ('C57'), ('C65'), ('CTX'), ('E287'),
            ('CII'), ('CGI'), ('C16'), ('C03')
    ),
    vendedores_dim as (
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
            max(nullif(trim(f.grupo_comercial_id), ''))::text as grupo_comercial_id
        from comercial_marts.fct_pedido_item as f
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
        group by trim(f.filial_id), trim(f.pedido_id)
    ),
    grupos_com_data_pendente as (
        select distinct nullif(trim(f.grupo_comercial_id), '')::text as grupo_comercial_id
        from comercial_marts.fct_pedido_item as f
        inner join produtos_mix as pm on pm.produto_id = trim(f.produto_id)
        where f.is_item_valido_metricas is true
          and f.is_venda_comercial is true
          and not coalesce(f.is_bonificacao, false)
          and not coalesce(f.is_remessa, false)
          and not coalesce(f.is_transferencia, false)
          and f.data_emissao is null
          and nullif(trim(f.grupo_comercial_id), '') is not null
    ),
    grupos_com_devolucao_sem_produto as (
        select distinct nullif(trim(d.grupo_comercial_id), '')::text as grupo_comercial_id
        from comercial_marts.fct_nota_devolucao as d
        where nullif(trim(d.grupo_comercial_id), '') is not null
          and (d.data_devolucao is null or d.data_devolucao <= current_date)
    ),
    vendas_nao_bloqueadas as (
        select
            trim(f.filial_id)::text as filial_id,
            trim(f.pedido_id)::text as pedido_id,
            f.data_emissao::date as data_emissao,
            nullif(trim(f.grupo_comercial_id), '')::text as grupo_comercial_id,
            pm.grupo_mix,
            trim(f.produto_id)::text as produto_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_total, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_pedido_item as f
        inner join produtos_mix as pm on pm.produto_id = trim(f.produto_id)
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
            nullif(trim(f.grupo_comercial_id), ''), pm.grupo_mix,
            trim(f.produto_id), nullif(trim(f.vendedor_metricas_id), '')
    ),
    vendas_bloqueadas_faturadas as (
        select
            p.filial_id,
            p.pedido_id,
            p.data_emissao,
            p.grupo_comercial_id,
            pm.grupo_mix,
            trim(f.produto_id)::text as produto_id,
            nullif(trim(f.vendedor_metricas_id), '')::text as vendedor_id,
            sum(coalesce(f.valor_bruto_item, 0))::numeric as valor_bruto_elegivel
        from comercial_marts.fct_faturamento_item as f
        inner join produtos_mix as pm on pm.produto_id = trim(f.produto_id)
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
            pm.grupo_mix, trim(f.produto_id), nullif(trim(f.vendedor_metricas_id), '')
    ),
    vendas_brutas as (
        select * from vendas_nao_bloqueadas
        union all
        select * from vendas_bloqueadas_faturadas
    ),
    vendas_por_produto_vendedor as (
        select
            v.filial_id,
            v.pedido_id,
            v.data_emissao,
            v.grupo_comercial_id,
            v.grupo_mix,
            v.produto_id,
            v.vendedor_id,
            sum(v.valor_bruto_elegivel)::numeric as valor_bruto_elegivel
        from vendas_brutas as v
        group by
            v.filial_id, v.pedido_id, v.data_emissao, v.grupo_comercial_id,
            v.grupo_mix, v.produto_id, v.vendedor_id
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
        from vendas_por_produto_vendedor as v
        left join vendedores_dim as vd on vd.vendedor_id = v.vendedor_id
        where v.valor_bruto_elegivel > 0
          and v.grupo_comercial_id is not null
    ),
    eventos as (
        select
            a.grupo_comercial_id,
            a.data_emissao,
            a.grupo_mix,
            string_agg(distinct a.produto_id, ' · ' order by a.produto_id)::text as produtos,
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
            sum(a.valor_bruto_elegivel)::numeric as valor_linha_elegivel,
            count(distinct a.vendedor_id) as quantidade_vendedores,
            bool_or(a.vendedor_id is null) as tem_vendedor_ausente,
            bool_and(a.mapeamento_unico and a.segmento_campanha is not null) as mapeamento_valido,
            count(distinct a.segmento_campanha) as quantidade_segmentos,
            bool_or(a.is_regiao_participante) as tem_regiao_participante,
            bool_and(a.is_regiao_participante) as todas_regioes_participantes
        from alocacoes as a
        group by a.grupo_comercial_id, a.data_emissao, a.grupo_mix
    ),
    primeira_compra_linha as (
        select
            e.grupo_comercial_id,
            e.grupo_mix,
            min(e.data_emissao)::date as data_primeira_compra
        from eventos as e
        group by e.grupo_comercial_id, e.grupo_mix
    ),
    candidatos as (
        select
            e.*,
            g.nome_grupo_comercial,
            ka.grupo_comercial_id is not null as is_ka,
            dp.grupo_comercial_id is not null as tem_data_pendente,
            dv.grupo_comercial_id is not null as tem_devolucao_sem_produto,
            case
                when e.segmento = 'Construção' and e.grupo_mix = 'Hydrofix' then 3000
                when e.segmento = 'Construção' and e.grupo_mix = 'Grelha + Porta Grelha' then 6000
                when e.segmento = 'Construção' and e.grupo_mix = 'Suporte de Bancada' then 9000
                when e.segmento = 'Canais' and e.grupo_mix = 'Suporte de Bancada' then 1000
                when e.segmento = 'Canais' and e.grupo_mix = 'Grelha + Porta Grelha' then 1000
                when e.segmento = 'Canais' and e.grupo_mix = 'CPP 009' then 2200
            end::numeric as valor_minimo,
            row_number() over (
                partition by e.grupo_comercial_id, e.grupo_mix
                order by e.data_emissao
            ) as ordem_campanha
        from eventos as e
        inner join primeira_compra_linha as p
          on p.grupo_comercial_id = e.grupo_comercial_id
         and p.grupo_mix = e.grupo_mix
        inner join grupos_dim as g on g.grupo_comercial_id = e.grupo_comercial_id
        left join grupos_ka as ka on ka.grupo_comercial_id = e.grupo_comercial_id
        left join grupos_com_data_pendente as dp on dp.grupo_comercial_id = e.grupo_comercial_id
        left join grupos_com_devolucao_sem_produto as dv
          on dv.grupo_comercial_id = e.grupo_comercial_id
        where e.data_emissao >= date '2026-09-01'
          and e.data_emissao < date '2027-01-01'
          and (
              p_competencia is null
              or (
                  e.data_emissao >= p_competencia
                  and e.data_emissao < (p_competencia + interval '1 month')::date
              )
          )
          and (
              e.data_emissao = p.data_primeira_compra
              or dp.grupo_comercial_id is not null
              or dv.grupo_comercial_id is not null
          )
          and e.tem_regiao_participante
    ),
    primeiras as (
        select * from candidatos where ordem_campanha = 1
    )
    select
        p.grupo_comercial_id,
        p.nome_grupo_comercial,
        p.data_emissao as data_expansao,
        p.grupo_mix,
        p.produtos,
        p.pedidos,
        p.quantidade_pedidos,
        p.vendedores,
        coalesce(p.regioes, '')::text as regioes,
        p.segmento,
        p.valor_linha_elegivel,
        p.valor_minimo,
        p.quantidade_vendedores,
        case
            when p.is_ka then 'Sem XP: cliente KA'
            when p.tem_data_pendente then 'Pendente: data histórica ausente'
            when p.tem_devolucao_sem_produto then 'Pendente: devolução sem produto'
            when p.valor_minimo is null then 'Sem XP: família fora do segmento'
            when p.valor_linha_elegivel < p.valor_minimo then 'Sem XP: abaixo do mínimo'
            when p.tem_vendedor_ausente then 'Pendente: vendedor não identificado'
            when p.quantidade_vendedores not in (1, 2) then 'Pendente: quantidade de vendedores'
            when not p.mapeamento_valido then 'Pendente: região ou segmento'
            when p.quantidade_segmentos <> 1 then 'Pendente: segmentos divergentes'
            when not p.todas_regioes_participantes then 'Pendente: região sem meta'
            when p.quantidade_vendedores = 1 then 'Confirmado: integral'
            else 'Confirmado: divisão 50/50'
        end::text as situacao_evento,
        case
            when not p.is_ka
             and not p.tem_data_pendente
             and not p.tem_devolucao_sem_produto
             and p.valor_minimo is not null
             and p.valor_linha_elegivel >= p.valor_minimo
             and not p.tem_vendedor_ausente
             and p.quantidade_vendedores in (1, 2)
             and p.mapeamento_valido
             and p.quantidade_segmentos = 1
             and p.todas_regioes_participantes
            then 10 else 0
        end::numeric as xp_evento,
        case
            when not p.is_ka
             and not p.tem_data_pendente
             and not p.tem_devolucao_sem_produto
             and p.valor_minimo is not null
             and p.valor_linha_elegivel >= p.valor_minimo
             and not p.tem_vendedor_ausente
             and p.quantidade_vendedores in (1, 2)
             and p.mapeamento_valido
             and p.quantidade_segmentos = 1
             and p.todas_regioes_participantes
            then 10.0 / p.quantidade_vendedores else 0
        end::numeric as xp_por_vendedor
    from primeiras as p
    order by p.data_emissao, p.nome_grupo_comercial, p.grupo_mix;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_mix_produtos(date)
    from public, anon;
grant execute on function public.campanha_polar_carregar_mix_produtos(date)
    to authenticated;

commit;
