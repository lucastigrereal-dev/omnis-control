# security-guardian

## When to use
- Any module dealing with credentials, OAuth, tokens
- Any module with external actions (publish, send, deploy)
- Before any commit that touches auth or external APIs

## Checks
1. No hardcoded secrets, tokens, passwords
2. No real API calls (only MockAdapter)
3. No .env reading in source code
4. No OAuth real flow (only skeleton/contract)
5. dry_run=True on all external adapters
6. Approval gate on all potentially destructive actions

## Forbidden patterns
- `os.environ['SECRET']`, `os.environ['TOKEN']`
- `requests.post(url, ...)` without mock guard
- `openai.api_key =` without mock
- Hardcoded URLs for external services

## Output
- PASS: no security issues
- FLAG: potential risk, review needed
- BLOCK: must fix before proceeding

## Checklist
- [ ] No secrets in code
- [ ] No real API calls
- [ ] All external adapters are mock or dry-run
- [ ] Approval gates present for destructive actions
- [ ] No .env access in source
