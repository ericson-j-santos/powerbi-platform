# Contribuição

## Fluxo

1. Parta da `main` atual.
2. Use branch dedicada.
3. Faça a menor mudança tecnicamente correta.
4. Execute os testes e o validador do repositório.
5. Para mudança funcional, execute E2E no maior escopo disponível.
6. Abra PR com evidência vinculada ao HEAD atual.
7. Não trate CI verde isolado como prova de efeito funcional.

## Validações mínimas

```bash
python -m unittest discover -s tests -v
python scripts/validate_powerbi_repo.py .
```

Mudanças em PBIP/template devem preservar versionamento textual e os contratos de PBIP/PBIR/TMDL. Mudanças em workflows devem manter permissões mínimas e actions externas fixadas por SHA completo.

## Fronteira

Este repositório é exclusivo da plataforma Power BI. Lógica específica de produto e infraestrutura transversal devem permanecer nos repositórios consumidores/canônicos correspondentes.
