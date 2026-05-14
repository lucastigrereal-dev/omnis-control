# OMNIS Core Rules

## Identity
OMNIS is a local-first agentic operating system for content operations.
It is NOT KRATOS (frontend), NOT Aurora (interpreter), NOT Akasha (memory).

## Absolute rules
1. dry_run=True as universal default
2. No real action without explicit approval
3. No reading .env or secrets/
4. No writing to exports/ or data runtime
5. No push without authorization
6. No merge without full test suite passing
7. No destructive command (rm -rf, reset --hard, clean -fd)
8. P = product feature. CCOS = development infrastructure.
