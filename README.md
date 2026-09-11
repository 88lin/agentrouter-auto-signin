<div align="center">

<img src="assets/cover.jpg" alt="agentrouter-auto-signin —— AgentRouter 每日自动签到脚本" width="100%">

# 🚀 agentrouter-auto-signin

**每天自动完成 AgentRouter 签到，并把余额查回给你**

[![License: MIT](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20macOS%20%7C%20Linux-F43F5E?style=flat&logo=windows&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)]()
[![Stars](https://img.shields.io/github/stars/88lin/agentrouter-auto-signin?style=flat&logo=github&logoColor=white&color=F59E0B)](https://github.com/88lin/agentrouter-auto-signin/stargazers)

</div>

AgentRouter 每天签到能领 $25 额度，但得你自己记着去登录一次——忘一天，就少一天。

**这个脚本替你记。** 挂进系统定时任务后，它每天自动登录一次完成签到，顺手把余额查回来，
结果写成一行 JSON。装完就可以忘掉它，想确认的时候看一眼日志就行。

> **为什么是「登录」而不是「签到」**：AgentRouter 没有独立的签到接口，
> **登录动作本身就会触发当日签到**。所以脚本要做的事，就是每天替你登录一次。

**放心挂着跑**

- 单个 Python 文件，只依赖 `requests`，读得完也改得动
- 全程在你自己电脑上跑，账号只写在本机 `config.json`，仓库里没有任何凭据
- 日志里账号只留前 4 位（`alic*****`），报错信息里的密码会被替换成 `***`

**装一次就不用再管**

- Win / macOS / Linux 都能挂定时任务，静默无窗口，不打扰你
- **错过了会自动补签**：关机、睡眠、早上忘开电脑，三种情况都兜得住
- 一天只算一次积分，多跑几次既不会重复领，也不会出错
- 多账号各用独立会话，一个失败不影响其他
- 瞬时故障（被风控拦、站点 5xx）自动重试一次，不为一次抽风白丢一天

**出问题看得懂**

- 结果是一行 JSON：`result` 给脚本判断，`report` 是一句给人看的话
- 失败会明确区分**密码错**、**出口 IP 被风控**、**网络不通**——而不是笼统一句「签到失败」
- 拿不准就跑 `python signin.py diagnose`，它只探测站点、不碰你的账号

> 👤 作者：[88lin](https://github.com/88lin) · 📦 仓库：[github.com/88lin/agentrouter-auto-signin](https://github.com/88lin/agentrouter-auto-signin)

## 💖 赞助商

<table>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://agentrouter.org/register?aff=ugVO"><img src="https://cdn.jsdmirror.com/gh/88lin/picx-images-hosting@master/90C5FAD072EA247822CB88BB32512A41.webp" alt="Agent Router" width="150"></a>
</td>
<td valign="middle"><b><a href="https://agentrouter.org/register?aff=ugVO">Agent Router</a></b>&nbsp;是免费公益大模型API平台，支持GPT-5.6、claude-opus-5、glm-5.3、deepseek-v4-flash等主流模型，国内直连。注册送＄175（每日签到得＄25，被邀得＄50），支持GitHub/LinuxDo登录。</td>
</tr>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://anyrouter.top/register?aff=woX5"><img src="https://cdn.jsdmirror.com/gh/88lin/picx-images-hosting@master/微信图片_20260907170036_114_2.webp" alt="Any Router" width="150"></a>
</td>
<td valign="middle"><b><a href="https://anyrouter.top/register?aff=woX5">Any Router</a></b>&nbsp;是免费公益大模型API平台，可用GPT-6-astra、claude-fable-5.1等顶级模型。被邀得＄50，每日签到随机额度。</td>
</tr>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://www.sheapi.top/sign-up?aff=MvcR"><img src="https://cdn.jsdmirror.com/gh/88lin/picx-images-hosting@master/ScreenShot_2026-08-06_174058_726.webp" alt="SheApi" width="150"></a>
</td>
<td valign="middle"><b><a href="https://www.sheapi.top/sign-up?aff=MvcR">SheApi</a></b>&nbsp;是一家可靠高效的 API 中转服务提供商，主要提供 Claude Code、Codex 等主流模型的高稳定中转能力，Codex 倍率补贴低至 0.08，GPT-Image-2生图每张0.04。受邀注册送$1 体验金，每日签到还可领取专属免费额度。</td>
</tr>
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://www.workbuddy.cn/events/invite?inviteCode=w0x2ic45z"><img src="https://download.codebuddy.cn/web/workbuddy/0bebf86e38e7d71ff0c313d661e7753ff996c54e/assets/workbuddy-logo-WhgOvEF7.png" alt="WorkBuddy" width="150"></a>
</td>
<td valign="middle"><b><a href="https://www.workbuddy.cn/events/invite?inviteCode=w0x2ic45z">WorkBuddy</a></b>&nbsp;是腾讯出品的全能 AI 工作台，是中国最受欢迎的效率 AI 智能体服务，说出要求、开始执行任务、交付完整成果。其中Hy4模型限时免费使用，注册即可获取2000积分，每月再赠送500积分，可用Kimi-K3、GLM-5.3等模型。</td>
</tr>
</table>

---

## 📋 前置条件

- 已注册 [AgentRouter](https://agentrouter.org/register?aff=ugVO)
- ✅ **账号已绑定邮箱，并用「邮箱 + 密码」登录过一次**（必须）
- 本机有 **Python 3.8+**

绑定邮箱的步骤：

1. 在站点**绑定邮箱**
2. **退出登录**
3. 点「**忘记密码**」重新设置一次密码
4. 之后用**邮箱 + 密码**登录

> [!IMPORTANT]
> 站点支持 GitHub / LinuxDo 登录，但脚本走的是**邮箱 + 密码**。没做上面这四步，
> 登录会一直失败（报 `AUTH_ERROR`）。

---

## 🚀 快速开始

两条路，选一条走完就行。

| | 适合谁 | 花多久 |
|---|---|---|
| **🤖 懒人一键** | 手边有 WorkBuddy、Zcode 这类国产 AI 助手 | 发一段话，全程不用自己敲命令 |
| **⌨️ 手动安装** | 想自己掌握每一步，或者手边没有 AI 助手 | 约 3 分钟 |

### 🤖 懒人一键

**先决定密码怎么给**：直接填进下面的提示词最省事，但它会留在对话记录里；介意的话就照
提示词下面那条注记改一句话，让 AI 停下来等你自己填。

然后把下面**整段**发给你的 AI 助手：

```text
帮我在本机装好这个 AgentRouter 每日自动签到脚本：
https://github.com/88lin/agentrouter-auto-signin

请按顺序做完，哪一步失败就停下来告诉我，不要跳过：

1. clone 仓库，进入目录，执行 python -m pip install -r requirements.txt
2. 复制 config.example.json 为 config.json，填入我的账号：
   邮箱 = ___
   密码 = ___
3. 执行 python signin.py diagnose，确认站点可达
4. 执行 python signin.py auto，确认输出里 "result" 是 "OK"、report 里报出了余额
5. 按我的系统挂上定时任务，每 30 分钟跑一次 `signin.py silent`：
   · Windows：执行 install-windows.ps1（不加参数它会自动随机挑起点时间）
   · macOS：参照 agentrouter-auto-signin.plist.example 配 launchd
   · Linux：按 README 的 Linux 段落写 crontab
6. 最后把第 4 步的完整输出、以及定时任务的下次运行时间一起发给我
```

> [!TIP]
> **不想把密码交给 AI**：把第 2 步整句换成「复制 config.example.json 为 config.json，
> 然后停下来让我自己填账号」。填好后再让它接着做第 3 步。

### ⌨️ 手动安装

```bash
git clone https://github.com/88lin/agentrouter-auto-signin.git
cd agentrouter-auto-signin

python -m pip install -r requirements.txt
cp config.example.json config.json      # Windows: Copy-Item config.example.json config.json
```

编辑 `config.json`，只填账号就够了：

```json
{
  "accounts": [
    { "username": "your-email@example.com", "password": "your-password" }
  ]
}
```

跑两条命令验证：

```bash
python signin.py diagnose     # 先确认站点可达，看到 OK 就行
python signin.py auto         # 正式签到
```

看到 `"result": "OK"`、`report` 里报出余额，就通了。接着往下挂[定时任务](#-挂上定时任务)。

---

## 🌐 站点域名

站点有两个官方域名，脚本默认用**新域名**，国内访问较稳定：

| 域名 | 说明 |
|---|---|
| `https://ps.air-outer.com` | 新域名，**脚本默认使用** |
| `https://agentrouter.org` | 旧域名，同样可用 |

想改用旧域名，改 `config.json` 的 `base_url` 即可：

```json
{ "base_url": "https://agentrouter.org" }
```

也可以用环境变量临时覆盖：`AGENTROUTER_BASE_URL=https://agentrouter.org`。

---

## ⏰ 挂上定时任务

**每 30 分钟跑一次就行**，不用你挑时间点。

听着很勤，其实站点每天只被登录 **1 次**：脚本会把「今天已经签成了」记进
`checkin.state`，当天后续的运行读到它就**直接退出，连站点都不碰**。
只有还没签成时才真的去登录——也就是说，**失败会每 30 分钟自动重试，成功就彻底歇着**。

```text
成功那天                          失败那天
09:00  跑 → 成功，记下状态         09:00  跑 → 断网，失败
09:30  跑 → 立刻退出（不联网）      09:30  跑 → 重试，还是失败
10:00  跑 → 立刻退出               10:00  跑 → 成功，记下状态
 ...   （当天剩下全是空转）         10:30  跑 → 立刻退出
```

> 签到**按北京时间自然日计算，每天 00:00 重置**，一天只算一次，重复运行不加积分。
> 脚本也按北京时间判断「今天」，跨时区用也不会判错。

### 🤔 为什么不用「失败后自动重试」那种设置

因为系统根本不提供。Windows 计划任务的「失败后重启」（`RestartCount`）**只管
「任务启动不起来」，不管「任务跑完了返回失败」**——实测：动作以退出码 2 结束，
配好 `RestartCount=2`、间隔 1 分钟，等 2.5 分钟一次都没重跑。
launchd 和 cron 同样没有按退出码重试的机制。

所以只能反过来做：**让任务跑得勤一点，由脚本自己判断今天还需不需要签**。
状态文件就是干这个的。

### 📌 关机、休眠会不会漏

不会：

| 平台 | 机制 |
|---|---|
| 🪟 Windows | 任务开了 `StartWhenAvailable`，关机错过的话下次开机登录后补上；之后每 30 分钟继续 |
| 🍎 macOS | `StartInterval` 每 30 分钟一次 + `RunAtLoad` 开机登录立刻跑一次 |
| 🐧 Linux | cron `*/30` + 一条 `@reboot`（普通 cron 不补跑错过的任务，所以 `@reboot` 是必要的）|

因为是每 30 分钟滚动重试，只要机器当天有开过一会儿，就能签上。

### 🪟 Windows

在仓库目录下执行一条命令，任务会自动建好（用 `pythonw.exe`，无窗口、零打扰）：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

| 任务 | 频率 | 干什么 |
|---|---|---|
| `AgentRouterAutoSignin` | 每 30 分钟 | 当天没签成才真去签，签成过就立刻退出 |

**起点时间默认随机挑一分钟**（`00:xx`），不同用户天然错开。想自己定：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1 -StartTime 00:17 -IntervalMinutes 30
```

装完会打印实际用的起点时间和下次运行时间。查看日志 `Get-Content checkin.log -Tail 5`。

> 只有一个任务。如果你装过早期版本的两个任务（`AgentRouterRetrySignin`），重跑安装脚本会自动清掉多余那个。

> [!NOTE]
> 任务以「当前用户登录时运行」注册，不需要管理员权限、也不用存密码。所以补跑发生在
> **下次开机并登录之后**——这也是它不加 `-User`/密码的原因。

卸载：

```powershell
Unregister-ScheduledTask -TaskName "AgentRouterAutoSignin" -Confirm:$false
```

### 🍎 macOS

```bash
which python3                                    # 记下输出，编辑模板时要用
mkdir -p ~/Library/LaunchAgents
cp agentrouter-auto-signin.plist.example ~/Library/LaunchAgents/agentrouter-auto-signin.plist
# 编辑该文件：把两处 /PATH/TO/agentrouter-auto-signin 换成脚本目录的绝对路径；
# 若 which python3 的输出不是 /usr/bin/python3，把 ProgramArguments 第一项也一并替换：
launchctl bootout gui/$(id -u)/agentrouter-auto-signin 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/agentrouter-auto-signin.plist
```

> [!WARNING]
> 两个坑踩中都是「任务静默失败、日志空空」：
> 1. **别想当然填 `/usr/bin/python3`**——没装 Xcode Command Line Tools 时它只是占位壳子，launchd 里跑直接失败，错误只进 `.err`。Homebrew 装的通常在 `/opt/homebrew/bin/python3`，一律以 `which python3` 为准。
> 2. **脚本别放在 `~/Documents`、`~/Desktop`、`~/Downloads`**——macOS 隐私保护（TCC）会拦截后台进程读取，报 `Operation not permitted`。

### 🐧 Linux

```cron
@reboot      sleep 60 && cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
13,43 * * * * cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
```

第二行是每 30 分钟一次。`13,43` 是随手挑的分钟——**换成你自己的两个数**（相差 30 即可，比如 `06,36`），
别都用 `0,30`，不然大家全卡在整点和半点。
第一行是开机后立刻补一次：`sleep 60` 等网络就绪。普通 cron 不补跑错过的任务，所以这一行是必要的。

---

## 🛠️ 子命令

```bash
python signin.py            # 等同 auto
python signin.py auto       # 立刻签到 + 查余额，结果打到 stdout（手动用）
python signin.py silent     # 给定时任务用：当天已签成过就跳过，否则签到并写 checkin.log
python signin.py diagnose   # 只确认站点是否可达，不登录任何账号
python signin.py --help     # 看用法
```

> [!NOTE]
> `auto` 和 `silent` 的区别不只是输出位置：**`silent` 会看状态文件**（当天签过就跳过），
> `auto` 不看也不写——你手动敲了就是要它跑。所以想强制再签一次，用 `auto`。

> [!NOTE]
> 没有「只查余额不签到」这个模式——想拿余额就必须登录，而登录就等于签到。

---

## ⚙️ 配置

`config.json` 放在脚本同目录（可从 `config.example.json` 复制）。表里的字段都能被对应的环境变量覆盖，环境变量优先级更高。

| 字段 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `accounts` | `AGENTROUTER_ACCOUNTS`<br>`AGENTROUTER_ACCOUNTS_JSON` | 无（必填） | 账号数组，**最多 10 个** |
| `base_url` | `AGENTROUTER_BASE_URL` | `https://ps.air-outer.com` | 站点域名，两个官方域名二选一，详见「站点域名」 |
| `request_timeout` | `AGENTROUTER_REQUEST_TIMEOUT` | `25` | 单次请求超时（秒），夹到 5–120 |
| `budget_seconds` | `AGENTROUTER_BUDGET_SECONDS` | `300` | 单次运行总预算（秒），夹到 30–540 |

下面两项**只认环境变量**，写进 `config.json` 不生效（它们要在读配置之前就定下来）：

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `AGENTROUTER_CONFIG` | 脚本同目录 `config.json` | 指定配置文件路径 |
| `AGENTROUTER_LOG` | 脚本同目录 `checkin.log` | 指定日志文件路径，目录不存在会自动创建 |
| `AGENTROUTER_STATE` | 脚本同目录 `checkin.state` | 指定状态文件路径（记「今天签过没」） |

状态文件只是省请求的优化：删掉、损坏都不影响签到，最多当天多签一次（幂等，不会重复计分）。

数值项写错不会让脚本崩：会回退成默认值，并在输出里附一条 `config_warning` 说明是哪一项。

账号也能用环境变量给（两种写法，`AGENTROUTER_ACCOUNTS_JSON` 优先）：

```bash
# 每行一个 邮箱:密码。只在第一个冒号处分割，密码里有冒号也没关系
export AGENTROUTER_ACCOUNTS="alice@qq.com:pw-1234
bob@163.com:pw:with:colons"
```

```bash
# 密码首尾带空格时用这个，避免被自动去空格
export AGENTROUTER_ACCOUNTS_JSON='[{"username":"alice@qq.com","password":" pw 1234 "}]'
```

**网络不用配置**：脚本没有代理项，跟随系统网络环境。

---

## 📊 输出结果

`auto` 打到屏幕、`silent` 追加到 `checkin.log`，都是每行一条 JSON：

```json
{"time": "2026-09-11 08:10:04", "result": "OK", "report": "签到成功 1 个账号，总余额 $25.86", "accounts": [{"account": "alic*****", "checked_in": true, "balance_usd": 25.86, "error": "", "warning": ""}], "total_balance_usd": 25.86}
```

```text
[2026-09-11 08:10:04] {"time": "...", "result": "OK", "report": "..."}     # silent 模式多一个时间戳前缀
```

| `result` | 含义 | 退出码 |
|---|---|:--:|
| `OK` | 登录并签到成功，余额已查回 | 0 |
| `PARTIAL` | 多账号里有一部分失败 | 1 |
| `AUTH_ERROR` | 账号或密码不对 | 2 |
| `NO_EXIT` | 被站点风控拦截，当前出口 IP 被拦 | 2 |
| `NETWORK` | 连不上站点 | 2 |
| `TIMEOUT` | 已达时间预算 | 2 |
| `CONFIG_ERROR` | 配置有问题 | 2 |
| `ERROR` | 其他异常 | 2 |

`accounts` 里每一项的字段：

| 字段 | 说明 |
|---|---|
| `account` | 脱敏后的账号，只留前 4 位 |
| `balance_usd` | 该账号折算后的美元余额 |
| `error` | 失败原因，非空即视为这个账号失败 |
| `warning` | 签到成功但余额没查到时的提示，**不影响成败判定** |
| `checked_in` | 站点返回的原始值，恒为 `true`，判断不出是否当天首次签到，仅作数据保留 |

> 整个运行受「时间预算」约束（默认 300 秒）：网络严重超时时不会让请求逐个挂死把定时任务拖到被系统强杀，而是主动收尾并把已成功的部分如实记下来。

---

## 它是怎么跑的

| 步骤 | 接口 | 作用 |
|:---:|---|---|
| 1️⃣ | `GET /api/status` | 确认站点可达，同时读出余额换算单位 `quota_per_unit` |
| 2️⃣ | `POST /api/user/login` | 每个账号独立会话登录，登录成功即完成签到 |
| 3️⃣ | `GET /api/user/self` | 带 `New-API-User` 头读 `quota`，按 `quota_per_unit` 折算美元 |

几个接口细节，写在了代码注释里，也值得知道：

1. **登录失败也返回 HTTP 200**，必须看响应体的 `success` 字段——按状态码判断会误判。
2. `quota_per_unit` 从接口读，不写死。站点哪天改比例，余额不会算错。
3. 密码错误和账号被封禁返回**同一句话**（「用户名或密码错误，或用户已被封禁」），站点不区分。
4. 登录响应里的 `quota` 恒为 `0`，不能用——真实余额只在 `/api/user/self` 里。同理 `checked_in` 恒为 `true`，判断不出是否当天首次签到，所以成功一律报 `OK`。
5. **只有瞬时故障会重试**（被 WAF 拦、5xx、响应不是 JSON），最多重试一次、间隔 3 秒。密码错误这类业务失败不重试，不会拿你的账号去反复试密码。
6. 多账号之间隔 2 秒再登录下一个，避免一串请求被风控当成异常流量。

---

## 🧪 排错

| 现象 | 处理 |
|---|---|
| `AUTH_ERROR` | 确认填的是**邮箱**，且已按「前置条件」绑定邮箱并重置过密码。⚠️ 改好密码后**手动跑一次 `python signin.py auto`，或删掉 `checkin.state`**——当天一旦判定密码错就会被记为「到此为止」，定时任务会一直跳过到次日 |
| `NO_EXIT` | 当前出口 IP 被站点风控拦了（WAF 挑战页或 403），站点本身是通的。**换个网络环境**再试，别去查断网/DNS |
| `NETWORK` | 真的连不上站点：断网、DNS 异常、被本地防火墙拦截。可试试换另一个官方域名（见「站点域名」） |
| `TIMEOUT` | 网络严重超时，已成功的部分照常记录，剩余项等下次定时任务重试 |
| `CONFIG_ERROR` | 没建 `config.json`、没填账号、`base_url` 不是 https、**账号超过 10 个**等，报错信息里会写明是哪一项 |
| `ERROR` | 其他异常，`report` 里有摘要，`error_type` 里是异常类型 |
| 输出里有 `config_warning` | 配置项写错被回退成默认值了（比如 `request_timeout` 填了非数字），照着提示改 `config.json` |
| 提示缺少 `requests` | 先在仓库目录跑 `python -m pip install -r requirements.txt` |
| 任务没跑 | Win：`Get-ScheduledTaskInfo -TaskName "AgentRouterAutoSignin"` 看 `LastTaskResult`；macOS：先看 `/tmp/agentrouter-auto-signin.err` |
| `checkin.log` 是空的 | 只有 `silent` 模式才写日志，手动跑 `auto` 的结果只打到屏幕 |

**拿不准就先跑 `python signin.py diagnose`**：它只探测站点、不碰你的账号，会直接告诉你是可达、被 WAF 拦（`NO_EXIT`），还是网络不通（`NETWORK`）。

---

## 🔐 安全与隐私

- 仓库不含、不内嵌、不传输任何第三方密钥；账号密码只在你本机的 `config.json` 里
- `config.json` 已在 `.gitignore` 中——**别把它提交到任何仓库**，也别贴到聊天记录里
- 日志里账号只保留前 4 位（`alic*****`），这是数据结构层面的硬约束，不靠调用方自觉
- 异常信息里出现的密码会被替换为 `***`
- 只重试瞬时故障；密码错误不会被重试，不存在拿你的账号反复试密码
- 脚本只作用于**你自己的**账号

## ⚠️ 合规与免责

本工具面向**个人真实使用**：帮你别漏签、顺手看余额。请照站点的[使用规范](https://ps.air-outer.com/docs/terms.html)来用，别用于多账号批量刷额度、倒卖账号或其他违规行为——脚本也把账号数**硬限制在 10 个以内**，就是不想给这类用途留口子。

两点值得知道：

- **光签到不用，额度可能被收回。** 规范里写了，资源按「真实、持续使用」动态调整，长期不产生真实调用的账号可能被缩减。签到保住的是「别漏领」，替不了实际使用。
- 具体条款以[官方页面](https://ps.air-outer.com/docs/terms.html)当前内容为准，它会不时修订。

> [!WARNING]
> 本项目为**非官方**工具，与 AgentRouter 无任何隶属关系。接口来自站点前端，可能随时变动且不另行通知。使用风险自负。

---

<div align="center">

**如果这脚本对你有用，顺手[点个 ⭐ Star](https://github.com/88lin/agentrouter-auto-signin)**

站点改接口、脚本悄悄失灵时，你能一秒翻回这里。

</div>

## 📄 协议

[MIT](LICENSE) © 2026 [88lin](https://github.com/88lin) · 仓库：[github.com/88lin/agentrouter-auto-signin](https://github.com/88lin/agentrouter-auto-signin)
