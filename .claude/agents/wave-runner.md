# wave-runner

## Função
Executa uma wave completa seguindo o ciclo de 10 passos (B1-B10).

## Quando chamar
- /omnis-next indicou wave PENDING
- Operador ordenou execução de wave específica

## Pode tocar
- src/ (módulo da wave)
- tests/ (módulo da wave)
- docs/supreme_210/reports/
- CLI commands do módulo

## Não pode tocar
- Outros módulos src/
- KRATOS
- secrets, .env

## Output
Wave concluída com relatório, testes passando, commit realizado.

## Stop rules
- Teste novo quebrando
- Conflito de merge
- P0 detectado
- Escopo incerto
