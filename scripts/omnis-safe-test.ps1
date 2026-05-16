param(
  [string]$Module = ""
)

$ErrorActionPreference = "Stop"

if ($Module -and (Test-Path "tests/$Module")) {
  python -m pytest "tests/$Module" --import-mode=importlib -p no:warnings -v
} else {
  python -m pytest tests/ --import-mode=importlib -p no:warnings -q
}
