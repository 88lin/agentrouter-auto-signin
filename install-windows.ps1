#Requires -Version 5.1
<#
    AgentRouter 自动签到 · Windows 一键安装
    ------------------------------------------------------------------
    在仓库目录下执行：

        powershell -ExecutionPolicy Bypass -File .\install-windows.ps1

    它会自动建好两个计划任务（都用 pythonw.exe 静默运行，不弹窗口）：

        AgentRouterAutoSignin   每天 08:10   签到 + 查余额 + 通知
        AgentRouterRetrySignin  每天 20:10   兜底重试

    为什么要有第二个任务：站点没有公开每日签到的重置时点，而且电脑可能
    在早上没开机。脚本本身幂等，重复运行只会显示「今日已签到」，
    多跑一次是为了兜住重置时点不确定和错过开机这两种情况。

    卸载：
        Unregister-ScheduledTask -TaskName "AgentRouterAutoSignin" -Confirm:$false
        Unregister-ScheduledTask -TaskName "AgentRouterRetrySignin" -Confirm:$false
#>

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------- 手动覆盖
# 自动探测失败时，把下面两项填成完整路径再重跑本脚本。
# 注意：这两项默认是空串，必须判空之后再 Test-Path，
# 否则 PowerShell 5.1 会崩在 Test-Path 的参数校验上。
$ManualPythonw = ""   # 例如 C:\Python313\pythonw.exe
$ManualScript  = ""   # 例如 C:\Users\You\tools\agentrouter-auto-signin\signin.py

$TaskDaily = "AgentRouterAutoSignin"
$TaskRetry = "AgentRouterRetrySignin"

function Resolve-Pythonw {
    if ($ManualPythonw) {
        if (-not (Test-Path -LiteralPath $ManualPythonw)) {
            throw "`$ManualPythonw 指向的文件不存在：$ManualPythonw"
        }
        return $ManualPythonw
    }

    # 1) 优先问 py 启动器，它知道真实的安装位置
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($py) {
        $probe = & $py.Source -3 -c "import os,sys;print(os.path.join(sys.base_prefix,'pythonw.exe'))" 2>$null
        if ($probe) {
            $candidate = $probe.Trim()
            if ($candidate -and (Test-Path -LiteralPath $candidate)) { return $candidate }
        }
    }

    # 2) PATH 里直接有 pythonw.exe
    $cmd = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    # 3) PATH 里有 python.exe，同目录应该有 pythonw.exe
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($cmd) {
        $candidate = Join-Path (Split-Path -Parent $cmd.Source) "pythonw.exe"
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }

    return $null
}

Write-Host ""
Write-Host "AgentRouter 自动签到 · 安装程序" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

# ---------------------------------------------------------------- 定位脚本
if ($ManualScript) {
    if (-not (Test-Path -LiteralPath $ManualScript)) {
        throw "`$ManualScript 指向的文件不存在：$ManualScript"
    }
    $ScriptPath = $ManualScript
} else {
    $ScriptPath = Join-Path $PSScriptRoot "signin.py"
}

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "找不到 signin.py（预期位置：$ScriptPath）。请把本脚本放在仓库目录下执行，或设置 `$ManualScript。"
}
Write-Host "[1/4] 脚本位置：" -NoNewline
Write-Host $ScriptPath -ForegroundColor Green

# ---------------------------------------------------------------- 检查配置
$ConfigPath = Join-Path (Split-Path -Parent $ScriptPath) "config.json"
if (Test-Path -LiteralPath $ConfigPath) {
    Write-Host "[2/4] 配置文件：" -NoNewline
    Write-Host $ConfigPath -ForegroundColor Green
} else {
    Write-Host "[2/4] 未找到 config.json" -ForegroundColor Yellow
    Write-Host "      请先复制 config.example.json 为 config.json，填好账号密码后再重跑本脚本。" -ForegroundColor Yellow
    Write-Host "      命令：Copy-Item config.example.json config.json" -ForegroundColor DarkGray
    exit 1
}

# ---------------------------------------------------------------- 定位 Python
$Pythonw = Resolve-Pythonw
if (-not $Pythonw) {
    Write-Host ""
    Write-Host "没有找到 pythonw.exe。" -ForegroundColor Red
    Write-Host "请先安装 Python 3（安装时勾选 Add python.exe to PATH），" -ForegroundColor Yellow
    Write-Host "或编辑本脚本顶部的 `$ManualPythonw 填成完整路径后重跑。" -ForegroundColor Yellow
    exit 1
}
Write-Host "[3/4] Pythonw：" -NoNewline
Write-Host $Pythonw -ForegroundColor Green

# ---------------------------------------------------------------- 检查依赖
$Python = Join-Path (Split-Path -Parent $Pythonw) "python.exe"
if (Test-Path -LiteralPath $Python) {
    & $Python -c "import requests" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "缺少依赖 requests。" -ForegroundColor Red
        Write-Host "请先在仓库目录执行：" -ForegroundColor Yellow
        Write-Host "    & `"$Python`" -m pip install -r requirements.txt" -ForegroundColor DarkGray
        Write-Host "装好后重跑本脚本。" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "      依赖检查通过（requests 可用）" -ForegroundColor DarkGray
}

# ---------------------------------------------------------------- 注册任务
$action = New-ScheduledTaskAction `
    -Execute $Pythonw `
    -Argument "`"$ScriptPath`" silent" `
    -WorkingDirectory (Split-Path -Parent $ScriptPath)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

# StartWhenAvailable：关机错过的任务会在下次开机后补跑。
$triggerDaily = New-ScheduledTaskTrigger -Daily -At "08:10"
$triggerRetry = New-ScheduledTaskTrigger -Daily -At "20:10"

Register-ScheduledTask -TaskName $TaskDaily -Action $action -Trigger $triggerDaily -Settings $settings -Force | Out-Null
Register-ScheduledTask -TaskName $TaskRetry -Action $action -Trigger $triggerRetry -Settings $settings -Force | Out-Null

Write-Host "[4/4] 计划任务已注册" -ForegroundColor Green
Write-Host ""
Write-Host "任务清单" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

foreach ($name in @($TaskDaily, $TaskRetry)) {
    $task = Get-ScheduledTask -TaskName $name
    $info = Get-ScheduledTaskInfo -TaskName $name
    $next = if ($info.NextRunTime) { $info.NextRunTime } else { "-" }
    Write-Host ("  {0,-24} {1,-10} 下次运行：{2}" -f $task.TaskName, $task.State, $next)
}

Write-Host ""
Write-Host "查看日志" -ForegroundColor Cyan
Write-Host "  Get-Content checkin.log -Tail 5    # 每行一条 JSON" -ForegroundColor DarkGray
Write-Host ""
Write-Host "先手动跑一次确认能签上（有输出，便于排查）：" -ForegroundColor Cyan
Write-Host "  python signin.py auto" -ForegroundColor DarkGray
Write-Host "只想测网络出口：" -ForegroundColor Cyan
Write-Host "  python signin.py diagnose" -ForegroundColor DarkGray
Write-Host ""
Write-Host "卸载" -ForegroundColor Cyan
Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskDaily`" -Confirm:`$false" -ForegroundColor DarkGray
Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskRetry`" -Confirm:`$false" -ForegroundColor DarkGray
Write-Host ""
