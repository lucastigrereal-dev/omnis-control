# CCOS pre_tool_use_guard.ps1
# Blocks dangerous commands before execution

param($tool_name, $tool_input)

$blocked_patterns = @(
    'rm -rf',
    'Remove-Item -Recurse',
    'git reset --hard',
    'git clean -fd',
    'docker compose down',
    'docker rm',
    'docker rmi'
)

$blocked_paths = @(
    '\.env',
    'secrets/',
    '\.key$',
    '\.pem$',
    'credentials\.json',
    'exports/',
    'data/.*\.jsonl'
)

foreach ($pattern in $blocked_patterns) {
    if ($tool_input -match $pattern) {
        Write-Warning "BLOCKED: Command matches dangerous pattern: $pattern"
        exit 1
    }
}

foreach ($path_pattern in $blocked_paths) {
    if ($tool_input -match $path_pattern) {
        Write-Warning "BLOCKED: Path matches forbidden pattern: $path_pattern"
        exit 1
    }
}
