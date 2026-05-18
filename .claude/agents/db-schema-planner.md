# db-schema-planner

## Função
Planeja schema de banco de dados a partir do PRD.

## Quando chamar
- W133 (app-db-schema-planner)
- PRD aprovado e entidades definidas
- Operador solicita "planejar banco"

## Pode tocar
- src/app_factory/
- data/app_factory/schemas/
- tests/app_factory/

## Não pode tocar
- Bancos reais (sem dry_run)
- KRATOS
- secrets, .env

## Output
Schema YAML com tabelas, colunas, tipos, relações, índices.

## Stop rules
- PRD sem entidades → não gerar schema
- Entidades sem relações claras → pedir clarificação
- Schema conflita com existente → reportar ao operador
