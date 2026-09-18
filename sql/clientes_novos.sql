-- FUNÇÃO: identifica a primeira compra elegível de cada grupo comercial.
-- JANELA HISTÓRICA: janeiro/2022 em diante; CAMPANHA: setembro-dezembro/2026.
-- SAÍDA: uma linha por vendedor participante do evento diário, permitindo 10 XP
-- integrais para um vendedor ou duas parcelas de 5 XP para dois vendedores.
begin;

drop function if exists public.campanha_polar_carregar_clientes_novos(date);

create or replace function public.campanha_polar_carregar_clientes_novos(p_competencia date)
returns table (
    grupo_comercial_id text,
    nome_grupo_comercial text,
    data_primeira_compra date,
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
    -- 1. Resolve nome, região e segmento somente quando o cadastro do vendedor
    -- é unívoco; ambiguidades não são escolhidas arbitrariamente.
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
    -- 2. A dimensão valida a identidade do grupo e fornece o nome de exibição.
    grupos_dim as (
        select
            trim(g.grupo_comercial_id)::text as grupo_comercial_id,
            max(trim(g.nome_grupo_comercial))::text as nome_grupo_comercial
        from comercial_marts.dim_grupo_comercial as g
        where nullif(trim(g.grupo_comercial_id), '') is not null
        group by trim(g.grupo_comercial_id)
    ),
    -- 3. Usa a fotografia corrente do bloqueio financeiro por cliente/loja.
    clientes_bloqueados as (
        select distinct trim(i.cliente_loja_id)::text as cliente_loja_id
        from comercial_marts.vw_clientes_inadimplentes as i
        where nullif(trim(i.cliente_loja_id), '') is not null
    ),
    -- 4. Preserva data, cliente e grupo no grão físico do pedido para relacionar
    -- posteriormente faturamento e devolução sem multiplicar itens.
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
    -- 5. Qualquer compra histórica elegível sem data impede afirmar que a compra
    -- observada é realmente a primeira do grupo.
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
    -- 6a. Não bloqueados entram pelo valor bruto já alocado ao vendedor.
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
    -- 6b. Bloqueados entram somente pelo faturamento válido encontrado.
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
    -- 7. Uma nota só é vinculada quando identifica um único pedido para o mesmo
    -- vendedor; vínculos ambíguos são tratados na CTE de pendências.
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
    -- 8. Se uma devolução do grupo não puder ser ligada de forma inequívoca, o
    -- grupo é retirado da conclusão automática de novidade.
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
    -- 9. Soma apenas devoluções já alocadas ao vendedor e vinculadas ao pedido.
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
    -- 10. Um pedido totalmente devolvido deixa de formar evento histórico.
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
    -- 11. Acrescenta região, segmento e participação por meta à venda líquida.
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
    -- 12. Todos os pedidos do mesmo grupo na mesma data formam um único evento.
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
    -- 13. Mantém uma linha de evidência por vendedor para exibição e rateio.
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
    -- 14. A menor data elegível desde 2022 define a novidade do grupo.
    primeira_compra as (
        select e.grupo_comercial_id, min(e.data_emissao)::date as data_primeira_compra
        from eventos as e
        group by e.grupo_comercial_id
    ),
    -- 15. Restringe a primeira compra à campanha e remove casos cuja história
    -- não pode ser concluída com segurança.
    novos as (
        select e.*
        from eventos as e
        inner join primeira_compra as p
          on p.grupo_comercial_id = e.grupo_comercial_id
         and p.data_primeira_compra = e.data_emissao
        inner join grupos_dim as g on g.grupo_comercial_id = e.grupo_comercial_id
        left join grupos_com_data_pendente as dp on dp.grupo_comercial_id = e.grupo_comercial_id
        left join grupos_com_devolucao_pendente as dv on dv.grupo_comercial_id = e.grupo_comercial_id
        where e.data_emissao >= date '2026-09-01'
          and e.data_emissao < date '2027-01-01'
          and (
              p_competencia is null
              or (
                  e.data_emissao >= p_competencia
                  and e.data_emissao < (p_competencia + interval '1 month')::date
              )
          )
          and e.tem_regiao_participante
          and dp.grupo_comercial_id is null
          and dv.grupo_comercial_id is null
    )
    select
        n.grupo_comercial_id,
        g.nome_grupo_comercial,
        n.data_emissao as data_primeira_compra,
        d.pedidos,
        d.vendedor,
        d.regiao,
        n.segmento,
        -- O motivo é calculado no grão do evento e repetido nas linhas de cada
        -- vendedor para que a interface consiga explicar a atribuição.
        case
            when n.tem_vendedor_ausente then 'Pendente: vendedor não identificado'
            when n.quantidade_vendedores not in (1, 2) then 'Pendente: quantidade de vendedores'
            when not n.mapeamento_valido then 'Pendente: região ou segmento'
            when n.quantidade_segmentos <> 1 then 'Pendente: segmentos divergentes'
            when not n.todas_regioes_participantes then 'Pendente: região sem meta'
            when n.quantidade_vendedores = 1 then 'Integral'
            else 'Divisão 50/50'
        end::text as situacao_atribuicao,
        case
            when not n.tem_vendedor_ausente
             and n.quantidade_vendedores in (1, 2)
             and n.mapeamento_valido
             and n.quantidade_segmentos = 1
             and n.todas_regioes_participantes
            then 10.0 / n.quantidade_vendedores else 0
        end::numeric as xp
    from novos as n
    inner join grupos_dim as g on g.grupo_comercial_id = n.grupo_comercial_id
    inner join detalhes as d
      on d.grupo_comercial_id = n.grupo_comercial_id
     and d.data_emissao = n.data_emissao
    order by n.data_emissao, g.nome_grupo_comercial, d.vendedor, d.regiao;
end;
$$;

revoke all privileges on function public.campanha_polar_carregar_clientes_novos(date)
    from public, anon;
grant execute on function public.campanha_polar_carregar_clientes_novos(date)
    to authenticated;

commit;

notify pgrst, 'reload schema';
