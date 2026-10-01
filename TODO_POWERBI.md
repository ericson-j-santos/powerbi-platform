# TODO operacional — Power BI Platform

## Estado em 2026-10-01

- [x] Corrigir falsos negativos do validador Windows.
- [x] Publicar a branch e abrir o PR [#22](https://github.com/ericson-j-santos/powerbi-platform/pull/22).
- [x] Validar localmente: `34 passed` e `POWERBI_REPO_VALIDATION_OK`.
- [x] Confirmar autenticação GitHub e branch remota.
- [ ] Resolver o E2E real do Power BI Desktop no PR #22.
  - Bloqueio atual: o instalador Microsoft entregue pela URL fixa não corresponde ao prefixo esperado `2.157.1354`.
  - Próxima ação: confirmar a versão suportada, atualizar URL/prefixo/hash de forma coordenada e reexecutar a CI.
- [ ] Ativar proteção administrativa da `main` (issue #16).
  - Requer permissão administrativa no repositório.
  - Validar required checks reais, pull request obrigatório, bloqueio de force-push e exclusão.
- [ ] Validar DemandTracker com PostgreSQL real do TODO Global (issue #14).
  - Depende do runtime `DESKTOP-PDQK954` e das issues #4/#7 do repositório `desktop-pc24x7-runtime`.
  - Exige evidência de refresh real, demanda conhecida, controle negativo de exposição e replay sem duplicação.
- [ ] Revisar PRs Dependabot #18 e #20 após estabilizar o gate do Desktop.

## Critério de encerramento

Encerrar somente quando o PR #22 estiver validado, a proteção da `main` estiver confirmada por leitura independente e o E2E PostgreSQL tiver evidência real vinculada a host, ambiente, SHA e correlation ID.
