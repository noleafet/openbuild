Write-Host "Asking Podman to resolve all nested variables and extensions..." -ForegroundColor Cyan

# 1. Instruct podman compose to natively flatten the configuration
$resolvedConfig = podman compose -f .\build.yml config 2>$null

if ($resolvedConfig) {
    # Split the fully expanded YAML string into lines
    $configLines = $resolvedConfig -split "`n"
    
    foreach ($line in $configLines) {
        # Catch lines matching the flattened absolute source output format
        if ($line -like "*source:*") {
            # Safely split by space or colon to extract the path string
            $parts = $line -split "source:\s*"
            if ($parts.Count -ge 2) {
                $rawPath = $parts[1].Trim()
                
                # Strip out any potential wrapping quotes
                $rawPath = $rawPath -replace "^['`"]|['`"]$" , ""
                
                # Check if it resolves to a local absolute Windows path (e.g. D:\)
                if ($rawPath -match "^[a-zA-Z]:") {
                    
                    # Create the host folder instantly before the container run starts
                    if (-not (Test-Path $rawPath)) {
                        New-Item -ItemType Directory $rawPath -Force | Out-Null
                        Write-Host "✅ Auto-created folder: $rawPath" -ForegroundColor Green
                    }
                }
            }
        }
    }
} else {
    Write-Warning "Podman config processing failed. Verify your environment paths manually."
}

# 2. Complete execution sequence normally
Write-Host "Launching Containers..." -ForegroundColor Cyan
podman compose -f .\build.yml up -d
