-- Aplique em instalações existentes para permitir até 60 segundos às consultas analíticas.
-- O limite fica restrito às três funções da campanha e não altera as demais chamadas da Data API.
-- ALTER FUNCTION preserva o corpo e muda somente a configuração de execução.
begin;

alter function public.campanha_polar_carregar_clientes_novos(date)
    set statement_timeout = '60s';
alter function public.campanha_polar_carregar_clientes_reativados(date)
    set statement_timeout = '60s';
alter function public.campanha_polar_carregar_mix_produtos(date)
    set statement_timeout = '60s';

commit;

notify pgrst, 'reload schema';
