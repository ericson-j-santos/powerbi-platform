# Convenções

## Projetos

- Preferir Power BI Project (`.pbip`) para permitir versionamento textual.
- Não versionar arquivos binários `.pbix` ou `.pbit` como fonte principal.
- Manter nomes estáveis e descritivos para tabelas, medidas, parâmetros e consultas.

## DAX

- Medidas compartilhadas devem ser genéricas e documentar dependências.
- Evitar referência a nomes específicos de produtos em `shared/dax`.
- Mudanças que alterem semântica devem registrar impacto esperado.

## Power Query/M

- Funções compartilhadas devem receber parâmetros explícitos.
- Não embutir credenciais, tokens, caminhos pessoais ou URLs privadas.
- Separar parâmetros de ambiente da lógica reutilizável.

## Ambientes

- DEV/HML/STG/PROD devem variar por configuração/parâmetro, não por duplicação de lógica.
- Segredos nunca devem ser versionados.

## Reutilização

Um componente é candidato a `shared/` quando:
1. é independente de regra de negócio específica; e
2. pode ser consumido por mais de um projeto sem cópia ou adaptação estrutural.
