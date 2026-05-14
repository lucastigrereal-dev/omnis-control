# CCOS import_guard.ps1
# Scans for forbidden patterns in source files

param($file_path)

$forbidden = @(
    'secret',
    'token\s*=',
    'api_key\s*=',
    'password\s*=',
    'OAuthReal',
    'publish_real',
    'send_real',
    'deploy_real',
    'os\.environ\[',
    'openai\.',
    'requests\.post',
    'requests\.get'
)

if (-not $file_path) {
    $files = Get-ChildItem -Path "src/" -Recurse -Include "*.py"
} else {
    $files = @(Get-Item $file_path)
}

foreach ($f in $files) {
    $content = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    foreach ($pattern in $forbidden) {
        if ($content -match $pattern) {
            Write-Warning "FORBIDDEN PATTERN in $($f.Name): matched '$pattern'"
        }
    }
}
