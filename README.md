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

## Início rápido

Gere um projeto a partir do starter canônico:

```bash
python scripts/new_powerbi_project.py --name SalesAnalytics --output projects/SalesAnalytics
python scripts/validate_powerbi_repo.py projects/SalesAnalytics
```

O nome técnico aceita letras, números e `_`, deve começar por letra e não pode ser um nome reservado do Windows. O gerador não sobrescreve destinos existentes.

## Estado

- starter PBIP/PBIR/TMDL validado estruturalmente;
- abertura real validada em Power BI Desktop por E2E Windows efêmero;
- gerador reutilizável coberto por testes positivos, negativos e E2E do projeto gerado.
