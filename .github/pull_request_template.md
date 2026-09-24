## Objetivo

Descreva a mudança e o resultado esperado.

## Escopo e risco

- [ ] Mudança restrita ao Power BI Platform.
- [ ] Risco classificado (1 leitura/diagnóstico, 2 reversível/controlado, 3 administrativo/produção/irreversível).
- [ ] Nenhum segredo, credencial, dado pessoal ou arquivo binário Power BI foi versionado.
- [ ] Não há dependência acidental de ReqSys, BACEN ou infraestrutura transversal.

## Evidência

- SHA testado:
- Ambiente:
- `correlation_id`/run:
- Caso positivo:
- Controle negativo:
- Leitura independente/efeito observado:
- Replay/idempotência, quando aplicável:

## Validação

- [ ] `python -m unittest discover -s tests -v`
- [ ] `python scripts/validate_powerbi_repo.py .`
- [ ] E2E no maior escopo executável quando houver mudança funcional.
- [ ] Evidência pertence ao HEAD atual da PR.
- [ ] Dependência externa não validada está registrada como bloqueio, sem falso positivo.

## Governança

- [ ] Actions externas permanecem allowlisted e fixadas por SHA completo.
- [ ] Permissões dos workflows permanecem mínimas.
- [ ] Documentação e critérios de aceite foram atualizados quando necessário.
