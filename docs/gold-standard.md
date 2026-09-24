# Padrão ouro — Power BI Platform

## Objetivo

Definir critérios verificáveis para considerar o repositório tecnicamente endurecido sem confundir qualidade estrutural com validação funcional de dependências externas.

## Matriz de qualidade

| Controle | Critério |
| --- | --- |
| Fonte versionável | PBIP/PBIR/TMDL em texto; `.pbix` e `.pbit` rejeitados |
| Estado local | `.pbi/localSettings.json` e `.pbi/cache.abf` nunca versionados |
| CI estrutural | checkout do SHA alvo, testes unitários e validador fail-closed |
| Cadeia de suprimentos | actions externas allowlisted e fixadas por SHA completo |
| Permissões | workflows somente leitura salvo necessidade explicitamente revisada |
| Atualização | Dependabot para GitHub Actions |
| E2E | Power BI Desktop real, evidência sanitizada e vinculada ao SHA |
| Falso positivo | pré-condição, caso positivo, controle negativo e leitura independente quando aplicável |
| Segredos | fora do Git, logs e artifacts |
| Fronteira | sem acoplamento a ReqSys/BACEN/infra transversal |
| Governança | PR com objetivo, risco, evidência e validação explícitos |

## Demand Tracker

O modo Demo possui validação estrutural e abertura real do PBIP no Power BI Desktop.

O modo `Postgres` só pode ser classificado como validado após o E2E real descrito na issue #14, incluindo:

- runtime TODO Global DEV ativo no PC24x7;
- PostgreSQL somente em loopback;
- refresh real;
- leitura de demanda conhecida/`correlation_id`;
- controle negativo de exposição externa;
- replay sem duplicidade;
- evidência no mesmo host, ambiente e SHA.

Até isso ocorrer, qualidade estrutural e E2E Desktop não devem ser usados para afirmar validação da integração PostgreSQL.

## Proteção da main

A configuração administrativa da branch é um gate separado do código. O alvo recomendado é exigir PR e checks obrigatórios, bloquear force-push/exclusão e aplicar as proteções também a administradores quando a política do repositório assim determinar.

Esse controle só é considerado ativo após revalidação independente de `protected=true`/ruleset equivalente; documentação não substitui a configuração do GitHub.

## Critério de conclusão

O repositório atinge padrão ouro quando todos os controles de código/governança acima estão verdes no HEAD corrente, a integração externa aplicável foi validada sem falso positivo e os gates administrativos exigidos estão realmente ativos.
