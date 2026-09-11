#Requires -Version 5.1
<#
    AgentRouter 自动签到 · Windows 一键安装
    ------------------------------------------------------------------
    在仓库目录下执行：

        powershell -ExecutionPolicy Bypass -File .\install-windows.ps1

    想自己指定起点时间 / 间隔就加参数：

        powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -StartTime 00:17 -IntervalMinutes 30

    它会建好一个计划任务（用 pythonw.exe 静默运行，不弹窗口）：

        AgentRouterAutoSignin   每 30 分钟跑一次

    为什么是「每 30 分钟」而不是「每天一两次」：
    脚本会把「今天已经签成了」记进 checkin.state，当天后续的运行读到它就直接
    退出，连站点都不碰——所以成功那天站点只被登录 1 次。只有还没签成时才会
    真的去登录，等于失败每 30 分钟自动重试一次。

    之所以要这么绕，是因为 Windows 计划任务**不会按退出码重试**：
    RestartCount 只管「任务启动不起来」，任务跑完了返回失败它是不管的
    （实测：动作退出码 2，配 RestartCount=2/间隔 1 分钟，等 2.5 分钟一次都没重跑）。

    不指定起点时间时，脚本会随机挑一分钟。如果所有人都用同一个写死的时间，
    就会在那一刻集体涌向站点；各装各的时间天然错峰。

    卸载：
        Unregister-ScheduledTask -TaskName "AgentRouterAutoSignin" -Confirm:$false
#>

param(
    # 默认随机挑一分钟，让不同用户的任务天然错开，别都挤在整点。
    [string]$StartTime = ("00:{0:D2}" -f (Get-Random -Minimum 0 -Maximum 60)),
    [int]$IntervalMinutes = 30
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------- 手动覆盖
# 自动探测失败时，把下面两项填成完整路径再重跑本脚本。
# 注意：这两项默认是空串，必须判空之后再 Test-Path，
# 否则 PowerShell 5.1 会崩在 Test-Path 的参数校验上。
$ManualPythonw = ""   # 例如 C:\Python313\pythonw.exe
$ManualScript  = ""   # 例如 C:\Users\You\tools\agentrouter-auto-signin\signin.py

$TaskDaily = "AgentRouterAutoSignin"
# 旧版本装过的第二个任务；下面会顺手清掉，避免升级后两个任务并存。
$TaskLegacyRetry = "AgentRouterRetrySignin"

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
    # 原生命令往 stderr 写内容时，配合全局 Stop 策略在部分 PowerShell 版本上
    # 会被引擎当成错误抛出，这里临时降为 Continue，只信任退出码。
    $prevPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $Python -c "import requests" 2>$null | Out-Null
    $requestsReady = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prevPreference

    if (-not $requestsReady) {
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
if ($StartTime -notmatch '^([01]\d|2[0-3]):[0-5]\d$') {
    throw "时间格式不对：'$StartTime'。请用 24 小时制 HH:mm，例如 00:17。"
}
if ($IntervalMinutes -lt 5 -or $IntervalMinutes -gt 720) {
    throw "-IntervalMinutes 应在 5~720 之间（当前 $IntervalMinutes）。"
}

# 每日触发 + 重复间隔：New-ScheduledTaskTrigger 不能一次同时给出这两者，
# 所以先单独造一个带 Repetition 的「一次性」触发器，再把它的 Repetition
# 嫁接到每日触发器上。这是 PowerShell 5.1 下可用的写法。
$trigger = New-ScheduledTaskTrigger -Daily -At $StartTime
$repeat  = New-ScheduledTaskTrigger -Once -At $StartTime `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes) `
    -RepetitionDuration (New-TimeSpan -Hours 23 -Minutes 55)
$trigger.Repetition = $repeat.Repetition

Register-ScheduledTask -TaskName $TaskDaily -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null

# 旧版本装的是「早晚各一次」两个任务，升级后把多余那个清掉。
if (Get-ScheduledTask -TaskName $TaskLegacyRetry -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskLegacyRetry -Confirm:$false
    Write-Host "      已清理旧版本的 $TaskLegacyRetry 任务" -ForegroundColor DarkGray
}

Write-Host "[4/4] 计划任务已注册" -ForegroundColor Green
Write-Host ""
Write-Host "任务清单" -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

$task = Get-ScheduledTask -TaskName $TaskDaily
$info = Get-ScheduledTaskInfo -TaskName $TaskDaily
$next = if ($info.NextRunTime) { $info.NextRunTime } else { "-" }
Write-Host ("  {0,-24} {1,-10} 下次运行：{2}" -f $task.TaskName, $task.State, $next)

Write-Host ""
Write-Host ("每 {0} 分钟跑一次（起点 {1}）。签成功那天，当天后续的运行会读到状态文件" -f $IntervalMinutes, $StartTime) -ForegroundColor Cyan
Write-Host "直接退出、连站点都不碰；只有还没签成时才真的去登录——等于失败自动重试。" -ForegroundColor Cyan
Write-Host ""
Write-Host "任务还开了「错过后尽快补跑」：关机错过的话，下次开机登录后会自动补上。" -ForegroundColor Cyan
Write-Host ""
Write-Host ("想换起点时间或间隔，加参数重跑即可：") -ForegroundColor Cyan
Write-Host "  .\install-windows.ps1 -StartTime 00:17 -IntervalMinutes 30" -ForegroundColor DarkGray
Write-Host ""
Write-Host "查看日志" -ForegroundColor Cyan
Write-Host "  Get-Content checkin.log -Tail 5    # 每行一条 JSON" -ForegroundColor DarkGray
Write-Host ""
Write-Host "先手动跑一次确认能签上（有输出，便于排查）：" -ForegroundColor Cyan
Write-Host "  python signin.py auto" -ForegroundColor DarkGray
Write-Host "只想确认站点是否可达：" -ForegroundColor Cyan
Write-Host "  python signin.py diagnose" -ForegroundColor DarkGray
Write-Host ""
Write-Host "卸载" -ForegroundColor Cyan
Write-Host "  Unregister-ScheduledTask -TaskName `"$TaskDaily`" -Confirm:`$false" -ForegroundColor DarkGray
Write-Host ""
