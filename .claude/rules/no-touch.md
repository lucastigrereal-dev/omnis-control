# No-Touch Zones

## Never read
- .env
- .env.*
- secrets/
- *.key
- *.pem
- credentials.json

## Never write
- exports/
- data/**/*.jsonl (runtime data)

## Never execute
- rm -rf
- Remove-Item -Recurse
- git reset --hard
- git clean -fd
- docker compose down
- docker rm / docker rmi

## Never do without approval
- git push
- git merge (non-ff)
- git rebase
- API calls to external services
- OAuth flows
- Real publish/send/deploy
