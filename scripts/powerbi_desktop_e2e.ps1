param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("download", "install", "open")]
    [string]$Mode,
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
$statePath = Join-Path $evidenceDir "state.json"
$installerPath = Join-Path $env:RUNNER_TEMP "PBIDesktopSetup_x64.exe"

New-Item -ItemType Directory -Force -Path $evidenceDir | Out-Null

function Read-State {
    if (Test-Path -LiteralPath $statePath) {
        return Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
    }
    return [pscustomobject]@{
        installer_sha256 = $null
        installed_version = $null
        installer_completion_mode = $null
        installer_exit_code = $null
    }
}

function Write-State([object]$State) {
    $State | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Write-Evidence(
    [string]$Status,
    [string]$FailureStage,
    [bool]$ProcessStarted = $false,
    [bool]$ProcessResponding = $false,
    [bool]$SemanticEngineStarted = $false,
    [bool]$WindowTitlePresent = $false,
    [int]$LocalSettingsCount = 0,
    [int]$CacheAbfCount = 0,
    [bool]$RepoCleanAfterOpen = $false
) {
    $state = Read-State
    $evidence = [ordered]@{
        schema_version = "1.0"
        status = $Status
        failure_stage = $FailureStage
        correlation_id = $CorrelationId
        github_sha = $ExpectedSha
        runner_os = $env:RUNNER_OS
        installer = [ordered]@{
            source_host = "download.microsoft.com"
            expected_version_prefix = $expectedVersionPrefix
            observed_sha256 = $state.installer_sha256
            completion_mode = $state.installer_completion_mode
            exit_code = $state.installer_exit_code
        }
        powerbi = [ordered]@{
            installed_version = $state.installed_version
            process_started = $ProcessStarted
            process_responding = $ProcessResponding
            semantic_engine_started = $SemanticEngineStarted
            window_title_present = $WindowTitlePresent
        }
        project = [ordered]@{
            path = $projectRelative
            local_settings_created_count = $LocalSettingsCount
            cache_abf_created_count = $CacheAbfCount
            repository_clean_after_open = $RepoCleanAfterOpen
        }
        production_touched = $false
        secrets_read = $false
    }
    $evidence | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
}

function Assert-ImmutableCheckout {
    Push-Location $repoRoot
    try {
        $actualSha = (& git rev-parse HEAD).Trim()
        if ($LASTEXITCODE -ne 0 -or $actualSha -ne $ExpectedSha) {
            throw "expected_sha_mismatch"
        }
        if (-not (Test-Path -LiteralPath $projectPath -PathType Leaf)) {
            throw "starter_pbip_missing"
        }
    }
    finally {
        Pop-Location
    }
}

function Find-PowerBIExecutable {
    $candidate = Join-Path $env:ProgramFiles "Microsoft Power BI Desktop\bin\PBIDesktop.exe"
    if (Test-Path -LiteralPath $candidate -PathType Leaf) {
        return $candidate
    }
    return Get-ChildItem -LiteralPath $env:ProgramFiles -Filter "PBIDesktop.exe" -Recurse -File -ErrorAction SilentlyContinue |
        Select-Object -First 1 -ExpandProperty FullName
}

try {
    Assert-ImmutableCheckout

    if ($Mode -eq "download") {
        Write-Host "POWERBI_E2E_STAGE=download_started"
        & curl.exe --fail --location --retry 2 --connect-timeout 30 --max-time 240 --output $installerPath $installerUrl
        if ($LASTEXITCODE -ne 0) {
            throw "installer_download_failed"
        }
        $installer = Get-Item -LiteralPath $installerPath
        if ($installer.Length -lt 500MB) {
            throw "installer_size_invalid"
        }
        $state = Read-State
        $state.installer_sha256 = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        Write-State $state
        Write-Host "POWERBI_E2E_STAGE=download_completed"
        exit 0
    }

    if ($Mode -eq "install") {
        Write-Host "POWERBI_E2E_STAGE=install_started"
        if (-not (Test-Path -LiteralPath $installerPath -PathType Leaf)) {
            throw "installer_missing"
        }
        $state = Read-State
        $observedHash = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        if (-not $state.installer_sha256 -or $observedHash -ne $state.installer_sha256) {
            throw "installer_hash_changed"
        }

        $installStartedAt = Get-Date
        $install = Start-Process -FilePath $installerPath -ArgumentList @(
            "-quiet",
            "-norestart",
            "ACCEPT_EULA=1",
            "ENABLECXP=0",
            "INSTALLDESKTOPSHORTCUT=0",
            "DISABLE_UPDATE_NOTIFICATION=1"
        ) -PassThru

        $installDeadline = $installStartedAt.AddSeconds(480)
        $stableExecutableSince = $null
        $completionMode = $null
        $installerExitCode = $null

        do {
            Start-Sleep -Seconds 5
            $install.Refresh()

            if ($install.HasExited) {
                $installerExitCode = $install.ExitCode
                if ($installerExitCode -notin @(0, 3010)) {
                    throw "installer_exit_code_invalid"
                }
                $completionMode = "process_exit"
                break
            }

            $candidateExe = Find-PowerBIExecutable
            if ($candidateExe) {
                $candidateVersion = (Get-Item -LiteralPath $candidateExe).VersionInfo.ProductVersion
                if ($candidateVersion.StartsWith($expectedVersionPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
                    if (-not $stableExecutableSince) {
                        $stableExecutableSince = Get-Date
                    }
                    elseif (((Get-Date) - $stableExecutableSince).TotalSeconds -ge 30) {
                        $completionMode = "executable_stable_while_bootstrapper_running"
                        break
                    }
                }
                else {
                    $stableExecutableSince = $null
                }
            }
            else {
                $stableExecutableSince = $null
            }

            Write-Host "POWERBI_E2E_INSTALL installer_running=$(-not $install.HasExited) executable_stable=$([bool]$stableExecutableSince)"
        } while ((Get-Date) -lt $installDeadline)

        if (-not $completionMode) {
            Stop-Process -Id $install.Id -Force -ErrorAction SilentlyContinue
            throw "installer_timeout"
        }

        if ($completionMode -eq "executable_stable_while_bootstrapper_running") {
            Get-Process -Name "PBIDesktopSetup_x64" -ErrorAction SilentlyContinue |
                Stop-Process -Force -ErrorAction SilentlyContinue
        }

        $powerBiExe = Find-PowerBIExecutable
        if (-not $powerBiExe) {
            throw "powerbi_executable_not_found"
        }
        $installedVersion = (Get-Item -LiteralPath $powerBiExe).VersionInfo.ProductVersion
        if (-not $installedVersion.StartsWith($expectedVersionPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "powerbi_version_mismatch"
        }
        $state.installed_version = $installedVersion
        $state.installer_completion_mode = $completionMode
        $state.installer_exit_code = $installerExitCode
        Write-State $state
        Write-Host "POWERBI_E2E_INSTALL_COMPLETION=$completionMode"
        Write-Host "POWERBI_E2E_STAGE=install_completed"
        exit 0
    }

    Write-Host "POWERBI_E2E_STAGE=open_started"
    $powerBiExe = Find-PowerBIExecutable
    if (-not $powerBiExe) {
        throw "powerbi_executable_not_found"
    }
    $state = Read-State
    $installedVersion = (Get-Item -LiteralPath $powerBiExe).VersionInfo.ProductVersion
    if (-not $state.installed_version -or $installedVersion -ne $state.installed_version) {
        throw "installed_version_changed"
    }

    $preexistingLocalSettings = @(
        Get-ChildItem -LiteralPath (Split-Path $projectPath) -Recurse -Filter "localSettings.json" -ErrorAction SilentlyContinue
    )
    if ($preexistingLocalSettings.Count -ne 0) {
        throw "preexisting_local_state"
    }

    $launchAt = Get-Date
    $desktopProcesses = @()
    $processStarted = $false
    $processResponding = $false
    $semanticEngineStarted = $false
    $windowTitlePresent = $false
    $localSettingsCount = 0
    $cacheAbfCount = 0
    $repoCleanAfterOpen = $false

    try {
        Start-Process -FilePath $powerBiExe -ArgumentList @($projectPath) | Out-Null
        $processStarted = $true
        $deadline = (Get-Date).AddSeconds(150)
        $nextProgress = Get-Date

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

            if ((Get-Date) -ge $nextProgress) {
                Write-Host "POWERBI_E2E_OPEN responding=$processResponding semantic=$semanticEngineStarted localSettings=$localSettingsCount"
                $nextProgress = (Get-Date).AddSeconds(30)
            }

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

        Push-Location $repoRoot
        try {
            $gitStatus = @(& git status --porcelain --untracked-files=all)
            if ($LASTEXITCODE -ne 0) {
                throw "git_status_failed"
            }
            $repoCleanAfterOpen = $gitStatus.Count -eq 0
        }
        finally {
            Pop-Location
        }
        if (-not $repoCleanAfterOpen) {
            throw "powerbi_open_mutated_source"
        }

        $successParams = @{
            Status = "success"
            FailureStage = $null
            ProcessStarted = $processStarted
            ProcessResponding = $processResponding
            SemanticEngineStarted = $semanticEngineStarted
            WindowTitlePresent = $windowTitlePresent
            LocalSettingsCount = $localSettingsCount
            CacheAbfCount = $cacheAbfCount
            RepoCleanAfterOpen = $repoCleanAfterOpen
        }
        Write-Evidence @successParams
        Write-Host "POWERBI_DESKTOP_E2E_OK"
        Write-Host "POWERBI_E2E_STAGE=open_completed"
    }
    finally {
        @($desktopProcesses) | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
catch {
    $failureStage = if ($Mode -eq "open") { "open_pbip" } else { "$Mode-powerbi-desktop" }
    Write-Evidence -Status "failed" -FailureStage $failureStage
    Write-Error "POWERBI_DESKTOP_E2E_FAILED mode=$Mode stage=$failureStage reason=$($_.Exception.Message)"
    exit 1
}
