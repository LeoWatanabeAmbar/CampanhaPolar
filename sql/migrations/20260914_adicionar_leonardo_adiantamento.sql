-- Para bancos que já receberam a versão original de adiantamento_meta.sql.
-- Preserva os registros e o histórico, ampliando as contas autorizadas.
begin;
alter table comercial_marts.campanha_polar_adiantamento
    drop constraint if exists campanha_polar_adiantamento_atualizado_por_check;
alter table comercial_marts.campanha_polar_adiantamento
    add constraint campanha_polar_adiantamento_atualizado_por_check
    check (atualizado_por in ('lais.vendrasco@ambar.tech', 'leonardo.watanabe@ambar.tech'));

alter table comercial_marts.campanha_polar_adiantamento_historico
    drop constraint if exists campanha_polar_adiantamento_historico_alterado_por_check;
alter table comercial_marts.campanha_polar_adiantamento_historico
    add constraint campanha_polar_adiantamento_historico_alterado_por_check
    check (alterado_por in ('lais.vendrasco@ambar.tech', 'leonardo.watanabe@ambar.tech'));
commit;
