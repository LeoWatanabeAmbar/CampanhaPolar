# Documentação do Campanha Polar

A documentação vigente começa no [Manual do projeto](manual/README.md). Ele consolida regras, exceções, arquitetura, dados, segurança, operação, implantação, testes e pendências com base no código atual.

Para leitura executiva, navegação no navegador ou impressão, abra também a [documentação em HTML](projeto.html).

## Manual vigente

| Documento | Conteúdo |
| --- | --- |
| [Índice e estado do projeto](manual/README.md) | escopo, status e mapa do repositório |
| [Regras de negócio](manual/01-regras-de-negocio.md) | elegibilidade, indicadores, XP, budget, níveis e prêmios |
| [Arquitetura e contratos](manual/02-arquitetura-dados-contratos.md) | componentes, fontes, RPCs, grãos e páginas |
| [Operação e segurança](manual/03-operacao-seguranca-deploy.md) | configuração, permissões, banco, deploy e diagnóstico |
| [Exceções e pendências](manual/04-excecoes-divergencias-pendencias.md) | casos de borda, divergências, riscos e decisões abertas |
| [Testes e rastreabilidade](manual/05-testes-rastreabilidade.md) | cobertura, limites e checklist de aceite |

## Anexos de contexto e levantamento

Os arquivos abaixo preservam a origem das decisões e detalhes de análise. Alguns contêm fotografias históricas ou perguntas antigas; consulte o manual para saber o status atual.

### Contexto e regulamento

- [Contexto da Polar](contexto/contextoPolar.md)
- [Objetivo do painel](contexto/objetivo.md)
- [Regulamento original](contexto/RegrasPolar.pdf)
- [Regras detalhadas da campanha](regras/regrasCampanha.md)
- [Interpretação de negócio](regras/regraNegocio.md)

### Dados e cálculos

- [Vendas](dados/dadoVenda.md)
- [Metas](dados/dadoMeta.md)
- [Calendário](dados/calendarioCampanha.md)
- [Elegibilidade financeira](dados/elegibilidadeVendas.md)
- [Clientes e produtos](dados/dadoCliente.md)
- [Enquadramento dos pedidos](dados/dadoEnquadramento.md)
- [Budget anual](dados/dadoBudget.md)
- [Adiantamento](dados/dadoAdiantamento.md)
- [Grupos KA](dados/dadoKA.md)
- [Visão de clientes novos](dados/visaoClientesNovos.md)
- [Visão de clientes reativados](dados/visaoClientesReativados.md)
- [Visão de mix](dados/visaoMixProdutos.md)

### Fotografias históricas

- [Prévia de clientes](dados/previaClientes.md)
- [Prévia de mix](dados/previaMix.md)
- CSVs e JSONs em `docs/dados` associados a essas prévias

### Arquitetura e publicação

- [Estrutura original](arquitetura/estrutura.md)
- [Deploy no Streamlit Community Cloud](arquitetura/deployStreamlitCloud.md)

## Regra de atualização

Não acrescente novas decisões apenas a uma prévia ou a um comentário de código. Atualize o manual, a implementação, os testes e, quando necessário, a migration do banco na mesma entrega.
