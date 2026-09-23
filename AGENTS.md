# AGENTS.md

Este repositório é dedicado exclusivamente à plataforma Power BI.

## Fonte canônica de regras

Antes de trabalho técnico, consulte a branch `main` de:

- `ericson-j-santos/chatgpt-operational-rules/README.md`
- `ericson-j-santos/chatgpt-operational-rules/AGENTS.md`
- regras aplicáveis em `rules/`
- regra específica deste projeto, quando existir em `projects/`

## Escopo local

Permitido neste repositório:

- projetos `.pbip`;
- modelos semânticos;
- DAX;
- Power Query/M;
- temas;
- parâmetros;
- automações específicas de Power BI;
- templates e documentação reutilizáveis.

Fora de escopo:

- regras de negócio específicas dos projetos consumidores;
- framework genérico de E2E;
- infraestrutura transversal de engenharia;
- componentes exclusivos de ReqSys, BACEN ou outro produto.

## Reutilização

Componentes compartilhados devem permanecer desacoplados de consumidores específicos. Configurações específicas de cada produto devem ficar no repositório consumidor sempre que possível.
