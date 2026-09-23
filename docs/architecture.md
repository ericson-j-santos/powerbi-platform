# Arquitetura do Power BI Platform

## Princípio

O repositório fornece capacidades reutilizáveis de Power BI. Produtos consumidores mantêm suas regras de negócio e apenas reutilizam padrões e componentes compartilhados.

## Estrutura alvo

```text
powerbi-platform/
├── projects/            # projetos PBIP de referência/reutilizáveis
├── shared/
│   ├── dax/             # padrões e medidas genéricas
│   ├── power-query/     # funções e consultas M reutilizáveis
│   └── themes/          # temas e identidade visual parametrizável
├── templates/           # templates de novos projetos Power BI
├── scripts/             # automações específicas do ciclo Power BI
└── docs/                # arquitetura, convenções e uso
```

## Fronteira de responsabilidade

### Pertence aqui

- componentes genéricos de Power BI;
- convenções de modelagem;
- templates reutilizáveis;
- temas;
- funções M;
- padrões DAX;
- automações de publicação/validação estritamente relacionadas a Power BI.

### Permanece no consumidor

- regras de negócio;
- credenciais e segredos;
- dados;
- parâmetros exclusivos de um ambiente/produto;
- integrações que só fazem sentido para um único sistema.

## Estratégia de consumo

Priorizar componentes versionados e templates. Evitar copiar código sem origem/versionamento. Quando um componente ganhar uso em dois ou mais projetos, promovê-lo para `shared/`.
