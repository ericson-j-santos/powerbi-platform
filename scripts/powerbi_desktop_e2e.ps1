param(
    [Parameter(Mandatory = $true)]
    [string]$ExpectedSha,
    [Parameter(Mandatory = $true)]
    [string]$CorrelationId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$installerUrl = "https://download.microsoft.com/download/8/8/0/880bca75-79dd-466a-927d-1abf1f5454b0/PBIDesktopSetup_x64.exe"
$expectedVersionPrefix = "2.157.1354"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectRelative = "templates/pbip-starter/Starter.pbip"
$projectPath = Join-Path $repoRoot $projectRelative
$evidenceDir = Join-Path $env:RUNNER_TEMP "powerbi-desktop-e2e"
$evidencePath = Join-Path $evidenceDir "evidence.json"
$installerPath = Join-Path $env:RUNNER_TEMP "PBIDesktopSetup_x64.exe"

$status = "failed"
$failureStage = "preflight"
$installerSha256 = $null
$installedVersion = $null
$processStarted = $false
$processResponding = $false
$semanticEngineStarted = $false
$windowTitlePresent = $false
$localSettingsCount = 0
$cacheAbfCount = 0
$repoCleanAfterOpen = $false
$desktopProcesses = @()

New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

try {
    Push-Location $repoRoot

    $actualSha = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $actualSha -ne $ExpectedSha) {
        throw "expected_sha_mismatch"
    }
    if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
        throw "starter_pbip_missing"
    }

    $preexistingLocalSettings = @(
        Get-ChildItem -LiteralPath (Split-Path $projectPath) -Recurse -Filter "localSettings.json" -ErrorAction SilentlyContinue
    )
    if ($preexistingLocalSettings.Count -ne 0) {
        throw "preexisting_local_state"
    }

    $failureStage = "download_installer"
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
    $installer = Get-Item -LiteralPath $installerPath
    if ($installer.Length -lt 500MB) {
        throw "installer_size_invalid"
    }
    $installerSha256 = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()

    $failureStage = "install_powerbi_desktop"
    $install = Start-Process -FilePath $installerPath -ArgumentList @(
        "-quiet",
        "-norestart",
        "ACCEPT_EULA=1",
        "ENABLECXP=0",
        "INSTALLDESKTOPSHORTCUT=0",
        "DISABLE_UPDATE_NOTIFICATION=1"
    ) -PassThru -Wait
    if ($install.ExitCode -notin @(0, 3010)) {
        throw "installer_exit_code_invalid"
    }

    $failureStage = "locate_powerbi_desktop"
    $candidate = Join-Path $env:ProgramFiles "Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        $powerBiExe = $candidate
    }
    else {
        $powerBiExe = Get-ChildItem -LiteralPath $env:ProgramFiles -Filter "PBIDesktop.exe" -Recurse -File -ErrorAction SilentlyContinue |
            Select-Object -First 1 -ExpandProperty FullName
    }
    if (-not $powerBiExe) {
        throw "powerbi_executable_not_found"
    }

    $installedVersion = (Get-Item -LiteralPath $powerBiExe).VersionInfo.ProductVersion
    if (-not $installedVersion.StartsWith($expectedVersionPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "powerbi_version_mismatch"
    }

    $failureStage = "open_pbip"
    $launchAt = Get-Date
    Start-Process -FilePath $powerBiExe -ArgumentList @($projectPath) | Out-Null
    $processStarted = $true

    $deadline = (Get-Date).AddSeconds(150)
    do {
        Start-Sleep -Seconds 5
        $desktopProcesses = @(
            Get-Process -Name "PBIDesktop" -ErrorAction SilentlyContinue |
                Where-Object { $_.StartTime -ge $launchAt.AddSeconds(-5) }
        )
        $responsiveProcesses = @($desktopProcesses | Where-Object { $_.Responding })
        $semanticProcesses = @(
            Get-Process -Name "msmdsrv" -ErrorAction SilentlyContinue |
                Where-Object { $_.StartTime -ge $launchAt.AddSeconds(-5) }
        )
        $localSettings = @(
            Get-ChildItem -LiteralPath (Split-Path $projectPath) -Recurse -Filter "localSettings.json" -ErrorAction SilentlyContinue
        )
        $cacheFiles = @(
            Get-ChildItem -LiteralPath (Split-Path $projectPath) -Recurse -Filter "cache.abf" -ErrorAction SilentlyContinue
        )

        $processResponding = $responsiveProcesses.Count -gt 0
        $semanticEngineStarted = $semanticProcesses.Count -gt 0
        $windowTitlePresent = @(
            $responsiveProcesses | Where-Object { -not [string]::IsNullOrWhiteSpace($_.MainWindowTitle) }
        ).Count -gt 0
        $localSettingsCount = $localSettings.Count
        $cacheAbfCount = $cacheFiles.Count

        if ($processResponding -and $semanticEngineStarted -and $localSettingsCount -gt 0) {
            break
        }
        if ($desktopProcesses.Count -eq 0 -and (Get-Date) -gt $launchAt.AddSeconds(20)) {
            break
        }
    } while ((Get-Date) -lt $deadline)

    if (-not $processResponding) {
        throw "powerbi_process_not_responding"
    }
    if (-not $semanticEngineStarted) {
        throw "semantic_engine_not_started"
    }
    if ($localSettingsCount -eq 0) {
        throw "pbip_local_state_not_created"
    }

    $failureStage = "source_integrity"
    $gitStatus = @(& git status --porcelain --untracked-files=all)
    if ($LASTEXITCODE -ne 0) {
        throw "git_status_failed"
    }
    $repoCleanAfterOpen = $gitStatus.Count -eq 0
    if (-not $repoCleanAfterOpen) {
        throw "powerbi_open_mutated_source"
    }

    $status = "success"
    $failureStage = $null
}
catch {
    if ([string]::IsNullOrWhiteSpace($failureStage)) {
        $failureStage = "unknown"
    }
}
finally {
    try {
        @($desktopProcesses) | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        # Ephemeral runner cleanup is authoritative; cleanup errors do not overwrite E2E evidence.
    }

    $evidence = [ordered]@{
        schema_version = "1.0"
        status = $status
        failure_stage = $failureStage
        correlation_id = $CorrelationId
        github_sha = $ExpectedSha
        runner_os = $env:RUNNER_OS
        installer = [ordered]@{
            source_host = "download.microsoft.com"
            expected_version_prefix = $expectedVersionPrefix
            observed_sha256 = $installerSha256
        }
        powerbi = [ordered]@{
            installed_version = $installedVersion
            process_started = $processStarted
            process_responding = $processResponding
            semantic_engine_started = $semanticEngineStarted
            window_title_present = $windowTitlePresent
        }
        project = [ordered]@{
            path = $projectRelative
            local_settings_created_count = $localSettingsCount
            cache_abf_created_count = $cacheAbfCount
            repository_clean_after_open = $repoCleanAfterOpen
        }
        production_touched = $false
        secrets_read = $false
    }

    $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
    Pop-Location -ErrorAction SilentlyContinue
}

if ($status -ne "success") {
    Write-Error "POWERBI_DESKTOP_E2E_FAILED stage=$failureStage"
    exit 1
}

Write-Host "POWERBI_DESKTOP_E2E_OK"
Write-Host "evidence=$evidencePath"
