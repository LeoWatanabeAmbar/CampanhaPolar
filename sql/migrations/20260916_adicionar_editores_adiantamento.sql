-- Amplia as contas autorizadas a editar o adiantamento sem perder os registros existentes.
-- Execute uma vez no SQL Editor do Supabase em instalações já configuradas.
-- Atualiza três pontos inseparáveis: constraints do estado/histórico e a
-- allowlist da função de escrita. A autorização continua baseada no JWT.
begin;

alter table comercial_marts.campanha_polar_adiantamento
    drop constraint if exists campanha_polar_adiantamento_atualizado_por_check;
alter table comercial_marts.campanha_polar_adiantamento
    add constraint campanha_polar_adiantamento_atualizado_por_check
    check (atualizado_por in ('lais.vendrasco@ambar.tech', 'leonardo.watanabe@ambar.tech', 'jorge.castro@ambar.tech', 'anyelle.santos@ambar.tech', 'luis.oliveira@ambar.tech'));

alter table comercial_marts.campanha_polar_adiantamento_historico
    drop constraint if exists campanha_polar_adiantamento_historico_alterado_por_check;
alter table comercial_marts.campanha_polar_adiantamento_historico
    add constraint campanha_polar_adiantamento_historico_alterado_por_check
    check (alterado_por in ('lais.vendrasco@ambar.tech', 'leonardo.watanabe@ambar.tech', 'jorge.castro@ambar.tech', 'anyelle.santos@ambar.tech', 'luis.oliveira@ambar.tech'));

-- Recriar o corpo garante que chamadas diretas à Data API respeitem a mesma
-- lista de editores exibida pelo Streamlit.
create or replace function public.campanha_polar_salvar_adiantamento(
    p_competencia date,
    p_registros jsonb
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
    v_email text := lower(trim(coalesce((select auth.jwt()) ->> 'email', '')));
    v_usuario_id uuid := (select auth.uid());
    v_item jsonb;
    v_regiao text;
    v_observacao text;
    v_versao_enviada integer;
    v_versao_atual integer;
    v_anterior comercial_marts.campanha_polar_adiantamento%rowtype;
    v_existe boolean;
    v_valores_anteriores jsonb;
    v_valores_novos jsonb;
    v_agora timestamptz;
    v_alterados integer := 0;
begin
    if v_usuario_id is null then
        raise exception 'AUTH_REQUIRED' using errcode = '42501';
    end if;
    if v_email not in ('lais.vendrasco@ambar.tech', 'leonardo.watanabe@ambar.tech', 'jorge.castro@ambar.tech', 'anyelle.santos@ambar.tech', 'luis.oliveira@ambar.tech') then
        raise exception 'PERMISSION_DENIED' using errcode = '42501';
    end if;
    if p_competencia is null
       or p_competencia <> date_trunc('month', p_competencia)::date
       or extract(year from p_competencia) <> 2026
       or extract(month from p_competencia) not in (9, 10, 11, 12) then
        raise exception 'INVALID_MONTH' using errcode = '22023';
    end if;
    if jsonb_typeof(p_registros) is distinct from 'array' then
        raise exception 'INVALID_ROWS' using errcode = '22023';
    end if;
    if exists (
        select 1
        from jsonb_array_elements(p_registros) as elemento(valor)
        group by elemento.valor ->> 'regiao'
        having count(*) > 1
    ) then
        raise exception 'INVALID_DUPLICATE_REGION' using errcode = '22023';
    end if;

    -- Valida o lote inteiro antes de iniciar as gravações.
    for v_item in select value from jsonb_array_elements(p_registros)
    loop
        if jsonb_typeof(v_item) is distinct from 'object'
           or jsonb_typeof(v_item -> 'regiao') is distinct from 'string'
           or jsonb_typeof(v_item -> 'semana_1_32') is distinct from 'boolean'
           or jsonb_typeof(v_item -> 'semana_2_56') is distinct from 'boolean'
           or jsonb_typeof(v_item -> 'semana_3_80') is distinct from 'boolean'
           or jsonb_typeof(v_item -> 'observacao') is distinct from 'string'
           or jsonb_typeof(v_item -> 'versao') is distinct from 'number'
           or (v_item ->> 'versao') !~ '^[0-9]+$' then
            raise exception 'INVALID_ROW' using errcode = '22023';
        end if;

        v_regiao := v_item ->> 'regiao';
        v_observacao := v_item ->> 'observacao';
        if v_regiao = '' or v_regiao <> trim(v_regiao) or length(v_observacao) > 2000 then
            raise exception 'INVALID_ROW' using errcode = '22023';
        end if;
        if not exists (
            select 1
            from comercial_marts.metas_comerciais as m
            where m.data = p_competencia
              and m.meta > 0
              and trim(m.regiao) = v_regiao
              and upper(trim(m.time)) in ('CANAIS', 'TIME NORTE', 'TIME SUL')
        ) then
            raise exception 'INVALID_REGION' using errcode = '22023';
        end if;
    end loop;

    for v_item in select value from jsonb_array_elements(p_registros)
    loop
        v_regiao := v_item ->> 'regiao';
        v_observacao := v_item ->> 'observacao';
        v_versao_enviada := (v_item ->> 'versao')::integer;
        v_valores_novos := jsonb_build_object(
            'semana_1_32', (v_item ->> 'semana_1_32')::boolean,
            'semana_2_56', (v_item ->> 'semana_2_56')::boolean,
            'semana_3_80', (v_item ->> 'semana_3_80')::boolean,
            'observacao', v_observacao
        );

        select *
        into v_anterior
        from comercial_marts.campanha_polar_adiantamento as a
        where a.competencia = p_competencia and a.regiao = v_regiao
        for update;
        v_existe := found;

        if v_existe then
            v_versao_atual := v_anterior.versao;
        else
            v_versao_atual := 0;
        end if;

        if v_versao_enviada <> v_versao_atual then
            raise exception 'CONCURRENT_CHANGE' using errcode = '40001';
        end if;

        if v_existe then
            v_valores_anteriores := jsonb_build_object(
                'semana_1_32', v_anterior.semana_1_32,
                'semana_2_56', v_anterior.semana_2_56,
                'semana_3_80', v_anterior.semana_3_80,
                'observacao', v_anterior.observacao
            );
            if v_valores_anteriores = v_valores_novos then
                continue;
            end if;
        else
            v_valores_anteriores := null;
        end if;

        v_agora := clock_timestamp();
        if v_existe then
            update comercial_marts.campanha_polar_adiantamento
            set semana_1_32 = (v_item ->> 'semana_1_32')::boolean,
                semana_2_56 = (v_item ->> 'semana_2_56')::boolean,
                semana_3_80 = (v_item ->> 'semana_3_80')::boolean,
                observacao = v_observacao,
                versao = v_anterior.versao + 1,
                atualizado_em = v_agora,
                atualizado_por = v_email,
                usuario_id = v_usuario_id::text
            where competencia = p_competencia
              and regiao = v_regiao
              and versao = v_anterior.versao;
            if not found then
                raise exception 'CONCURRENT_CHANGE' using errcode = '40001';
            end if;
        else
            insert into comercial_marts.campanha_polar_adiantamento (
                competencia, regiao, semana_1_32, semana_2_56, semana_3_80,
                observacao, versao, atualizado_em, atualizado_por, usuario_id
            ) values (
                p_competencia, v_regiao,
                (v_item ->> 'semana_1_32')::boolean,
                (v_item ->> 'semana_2_56')::boolean,
                (v_item ->> 'semana_3_80')::boolean,
                v_observacao, 1, v_agora, v_email, v_usuario_id::text
            );
        end if;

        insert into comercial_marts.campanha_polar_adiantamento_historico (
            competencia, regiao, versao, anterior, novo,
            alterado_em, alterado_por, usuario_id
        ) values (
            p_competencia, v_regiao,
            case when v_existe then v_anterior.versao + 1 else 1 end,
            v_valores_anteriores, v_valores_novos,
            v_agora, v_email, v_usuario_id::text
        );
        v_alterados := v_alterados + 1;
    end loop;

    return v_alterados;
exception
    when unique_violation then
        raise exception 'CONCURRENT_CHANGE' using errcode = '40001';
end;
$$;

revoke all on function public.campanha_polar_salvar_adiantamento(date, jsonb)
    from public, anon;
grant execute on function public.campanha_polar_salvar_adiantamento(date, jsonb)
    to authenticated;

commit;
