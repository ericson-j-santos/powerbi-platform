# Segurança

## Escopo

Este repositório contém ativos de Power BI, automações do ciclo de vida Power BI e documentação pública. Ele não deve armazenar segredos, credenciais, tokens, connection strings com segredo, dados pessoais desnecessários ou caches locais do Power BI Desktop.

## Relato de vulnerabilidade

Não publique segredos ou material sensível em issues, pull requests, logs ou artifacts públicos. Para uma falha de segurança, contate o proprietário do repositório por um canal privado disponibilizado pela conta do GitHub e informe apenas o necessário para reprodução segura.

Se uma credencial tiver sido exposta, trate a rotação/revogação como ação separada e imediata no sistema de origem. Remover o texto do Git não invalida a credencial.

## Controles do repositório

- workflows usam permissões mínimas;
- actions externas devem ser allowlisted e fixadas por SHA completo;
- arquivos `.pbix`, `.pbit` e estado local `.pbi` não são fonte versionada;
- E2E deve vincular evidência ao SHA e evitar falsos positivos;
- segredos são configurados fora do Git e fora dos artifacts.
