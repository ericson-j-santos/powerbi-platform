# Processamento incremental Power BI (exemplos desacoplados)

**Escopo:** Power Query M e medidas DAX reutilizáveis. Não modifica modelos publicados.

## Power Query M

1. No Power BI Desktop, criar parâmetros `RangeStart` e `RangeEnd` do tipo **Data/Hora**.
2. Configurar `ServidorSql` e `BancoSql` por parâmetro/ambiente; não inserir credenciais ou servidor privado no repositório.
3. Adaptar `dbo.FatoMovimento`, `DataMovimento`, `DataAlteracao`, `IdMovimento` e `Valor` para os campos reais.
4. Selecionar `shared/power-query/incremental_sqlserver_datetime.m`. A condição é `>= RangeStart` e `< RangeEnd`.
5. Conferir `query folding` e configurar política de atualização incremental no modelo semântico; só publicar mediante validação do consumidor.
6. Se a origem usa chave `AAAAMMDD`, usar a variante `_chave_aaaammdd.m` somente com limites à meia-noite.

**Riscos:** o primeiro refresh carrega partições históricas. Detecção de alterações precisa de coluna de auditoria, normalmente diferente da chave de partição. Exclusões físicas e alterações em períodos já arquivados podem não ser capturadas: requer reconciliação ou CDC.

## DAX

`shared/dax/incremental_analise.dax` é uma **consulta DAX** de demonstração. Pode ser executada na Exibição de Consulta DAX após adequar os nomes das tabelas e criar/validar calendário contínuo com relacionamento ativo. DAX não registra checkpoint nem substitui o refresh incremental.

## Verificação

`tests/test_incremental_shared_contract.py` cobre 3 contratos estáticos, testados em workspace isolado. Ainda **não** executado no Power BI Desktop, Power BI Service ou SIIAC oficial. Não declarar deploy/E2E.

Issue canônica: https://github.com/ericson-j-santos/powerbi-platform/issues/29
Fonte: https://learn.microsoft.com/pt-br/power-bi/connect-data/incremental-refresh-configure
Regras SHA: `58dcd4200f412a866278027ba9e433439a03f3b3`.
