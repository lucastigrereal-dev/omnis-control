$ErrorActionPreference = "Continue"
$pattern = "secret\|token=\|api_key=\|password=\|OAuthReal\|publish_real\|send_real\|deploy_real"
grep -r $pattern src/ --include="*.py"
