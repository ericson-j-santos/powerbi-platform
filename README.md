# Power BI Platform

Repositório compartilhado para ativos, padrões e componentes reutilizáveis de Power BI.

## Escopo

Este repositório trata exclusivamente da plataforma Power BI e dos artefatos reutilizáveis associados.

Inclui:

- projetos Power BI Project (`.pbip`);
- modelos semânticos e convenções;
- medidas e padrões DAX;
- consultas e funções Power Query/M;
- temas e componentes visuais reutilizáveis;
- parâmetros e configurações por ambiente;
- scripts de automação específicos do ciclo de vida Power BI;
- documentação e templates reutilizáveis.

Não inclui:

- regras de negócio específicas de produtos consumidores;
- infraestrutura geral de CI/CD;
- frameworks genéricos de E2E;
- componentes exclusivos do ReqSys, BACEN ou de outro produto.

## Objetivo

Permitir que diferentes projetos consumam uma base comum de Power BI sem duplicar padrões, scripts e componentes.

## Estado

Base operacional ativa e validada por CI estrutural e E2E em Power BI Desktop real.

- projetos PBIP e modelo semântico versionados como texto;
- geração de novos projetos com validação fail-closed;
- workflows com permissões somente leitura e checkout por SHA alvo;
- E2E do template e do Demand Tracker vinculados ao SHA executado;
- hardening de governança e cadeia de suprimentos documentado em `docs/gold-standard.md`.

A leitura real do TODO Global via PostgreSQL permanece rastreada separadamente na issue #14 e não é inferida a partir do E2E em modo Demo.
