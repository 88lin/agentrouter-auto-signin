<div align="center">

<img src="assets/cover.svg" alt="agentrouter-auto-signin —— AgentRouter 每日自动签到脚本" width="100%">

# 🚀 agentrouter-auto-signin

**自动完成 AgentRouter 每日签到的小脚本**

[![License: MIT](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20macOS%20%7C%20Linux-F43F5E?style=flat&logo=windows&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)]()
[![Stars](https://img.shields.io/github/stars/88lin/agentrouter-auto-signin?style=flat&logo=github&logoColor=white&color=F59E0B)](https://github.com/88lin/agentrouter-auto-signin/stargazers)
[![Author](https://img.shields.io/badge/Author-88lin-10B981?style=flat&logo=github&logoColor=white)](https://github.com/88lin)

</div>

> 一个自包含的 Python 脚本，每天自动登录 AgentRouter、触发当日签到、查回余额，可选推送到微信。
> 配置只放在本机的 `config.json` 里，仓库不含任何凭据，可安全分享。
>
> 👤 作者：[88lin](https://github.com/88lin) · 📦 仓库：[github.com/88lin/agentrouter-auto-signin](https://github.com/88lin/agentrouter-auto-signin)

> [!TIP]
> **⭐ 顺手点个 Star 再往下看**——AgentRouter 的签到接口来自站点前端，站点改一版它就可能失效，修复都会第一时间推到这里。Star 一下，等哪天签到莫名其妙断了，你能一秒翻回这个仓库。

> [!IMPORTANT]
> **本项目只支持在本机运行**，不提供 GitHub Actions 方案。原因是 AgentRouter 使用阿里云 WAF，会拦截机房 / 云服务器出口 IP——跑在 GitHub 托管运行器上必然被拦，配代理又得是住宅出口，绕的弯不值得。本机（家宽）一般可以直接连通。

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
<tr>
<td width="180" align="center" valign="middle">
  <a href="https://api.justwoker.icu/register?aff=wpiO"><img src="https://cdn.jsdmirror.com/gh/88lin/picx-images-hosting@master/ScreenShot_2026-09-01_130420_632.webp" alt="JustDoWork" width="150"></a>
</td>
<td valign="middle"><b><a href="https://api.justwoker.icu/register?aff=wpiO">JustDoWork</a></b>&nbsp;是免费公益大模型API平台，可用Claude Opus 5 模型。注册送＄100（每日签到得＄30左右），支持GitHub登录。</td>
</tr>
</table>

---

## ✨ 特性

| | 特性 |
|:---:|---|
| 🔐 | **无内置凭据** —— 仓库不含任何账号密码，配置只在你本机的 `config.json` 里 |
| ♻️ | **幂等安全** —— 签到由登录动作触发，重复运行只会显示「今日已签到」，不会多领 |
| 👥 | **多账号** —— 每个账号独立 Session，互不串号，一个失败不影响其他 |
| 🌐 | **出口自动探测** —— 按配置顺序试代理，最后试直连；自动识别被 WAF 拦截的情况 |
| 🧮 | **余额自动换算** —— 从站点 `/api/status` 读取 `quota_per_unit`，站点改比例也不会算错 |
| 🩺 | **诊断模式** —— `diagnose` 一条命令测出哪个出口可用，不用盲猜 |
| 📣 | **一行 JSON** —— `result` 给程序看，`report` 给人看，便于接任何汇报方式 |
| 💬 | **微信推送** —— 可选接入 PushPlus，签到完推一条 HTML 汇总 |
| ⏰ | **双定时模式** —— AI 自动化（跨平台）或系统级静默（Win 一键脚本 / macOS launchd / Linux cron） |
| 🛡️ | **异常不静默吞** —— 任何异常都会落成一条结果记录，不会悄悄消失 |
| 🕵️ | **自动脱敏** —— 日志与通知里账号只留前 4 位，密码 / 代理凭据替换为 `***` |

---

## 📋 前置条件

- ✅ 已注册 [AgentRouter](https://agentrouter.org/register?aff=ugVO)
- ✅ **账号已绑定邮箱并设置过密码** —— 站点支持 GitHub / LinuxDo 登录，但脚本走的是邮箱 + 密码，所以必须先绑定邮箱并重置一次密码
- ✅ 本机有 **Python 3.8+**（实测 3.13）
- ⬜ 可选：装了 `git` 可直接 `clone`；没有就 **Code → Download ZIP** 解压，效果一样

---

## 🚀 快速开始

**第 1 步 · 拿到脚本**

```bash
git clone https://github.com/88lin/agentrouter-auto-signin.git
cd agentrouter-auto-signin
```

**第 2 步 · 装依赖、写配置**

```bash
python -m pip install -r requirements.txt
cp config.example.json config.json      # Windows: Copy-Item config.example.json config.json
```

编辑 `config.json`，至少填好账号：

```json
{
  "accounts": [
    { "username": "your-email@example.com", "password": "your-password" }
  ]
}
```

**第 3 步 · 先测出口，再签一次**

```bash
python signin.py diagnose     # 看哪个出口能连上站点，看到 OK 就行
python signin.py auto         # 正式签到
```

看到 `"result": "OK"` 或 `"ALREADY"`、`report` 里报出余额，就说明跑通了。之后按下面的定时章节挂上系统计划任务即可。

> [!TIP]
> **懒人一键**：把仓库链接丢给 WorkBuddy——
> `帮我 clone 这个仓库，装好依赖、按 config.example.json 建好 config.json（账号是 xxx），并用 install-windows.ps1 配好每天自动签到：https://github.com/88lin/agentrouter-auto-signin`
> 它会自己 clone、装依赖、建配置、注册计划任务。

---

## ⏰ 每日定时自动化

### 模式对比

| 对比项 | 模式 A：AI 自动化 | 模式 B：系统级静默 ⭐ |
|:---:|---|---|
| **平台** | 🌐 Win / macOS / Linux | 🪟 Win / 🍎 macOS / 🐧 Linux |
| **原理** | WorkBuddy 自动化触发 → AI 跑脚本 → 模型汇报 | 系统定时器直接跑脚本 → 写日志文件 |
| **Token 消耗** | 每次消耗一次模型调用 | **零** |
| **聊天记录** | 每次一条 | **零** |
| **可靠性** | 依赖模型可用性 | 纯系统级，更可靠 |
| **日志** | 在聊天记录里 | 独立日志文件 `checkin.log` |
| **关机错过** | 错过就错过 | Win 可设「错过后下次启动补跑」 |
| **设置难度** | 中 | Win 低（一条命令）／ macOS、Linux 中（改模板） |

> [!NOTE]
> 两种模式都用 `silent` 子命令最省事：它把结果写进 `checkin.log` 而不是 stdout，配合 `pythonw.exe`（Windows）或 launchd 重定向实现完全静默。

### 模式 A：AI 自动化（跨平台）

适合不想碰系统计划任务的人，代价是每次运行消耗一次模型调用。

在 WorkBuddy 新建自动化：

- **名称**：AgentRouter 每日签到
- **计划**：每天 08:10
- **提示词**：

  ```text
  运行 <python> <signin.py 的绝对路径> auto，
  把命令输出的 JSON 里 report 字段的内容，直接一句话汇报给我。
  若 result 不是 OK 或 ALREADY，额外提醒我处理。
  ```

> `<python>` 填你机器上的 Python 3 命令名：macOS / Linux 通常是 `python3`，Windows 通常是 `python`。拿不准就各跑一次 `python3 --version`、`python --version`，哪个有输出用哪个。

### 模式 B：系统级静默（推荐）

#### 🪟 Windows · 任务计划程序

在仓库目录下运行：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

它会自动建好两个任务（都用 `pythonw.exe`，零 Token、无窗口）：

| 任务 | 频率 | 干什么 |
|---|---|---|
| `AgentRouterAutoSignin` | 每天 08:10 | 签到 + 查余额 + 通知，静默写 `checkin.log` |
| `AgentRouterRetrySignin` | 每天 20:10 | 兜底重试 |

> [!NOTE]
> **为什么要两个任务**：站点没有公开每日签到的重置时点，而电脑也可能在早上没开机。脚本是幂等的，重复运行只会显示「今日已签到」，所以多跑一次是为了兜住「重置时点不确定」和「错过开机」这两种情况，成本几乎为零。

卸载：

```powershell
Unregister-ScheduledTask -TaskName "AgentRouterAutoSignin" -Confirm:$false
Unregister-ScheduledTask -TaskName "AgentRouterRetrySignin" -Confirm:$false
```

查看日志：

```powershell
Get-Content checkin.log -Tail 5
```

日志格式（每行一条 JSON）：

```text
[2026-09-11 08:10:04] {"time": "2026-09-11 08:10:04", "result": "OK", "report": "签到成功 1 个账号，总余额 $25.00", ...}
```

#### 🍎 macOS · launchd

```bash
which python3                                    # 记下输出，编辑模板时要填
mkdir -p ~/Library/LaunchAgents
cp agentrouter-auto-signin.plist.example ~/Library/LaunchAgents/agentrouter-auto-signin.plist
# 编辑该文件：把两处 /PATH/TO/agentrouter-auto-signin 换成脚本目录的绝对路径；
# 若 which python3 的输出不是 /usr/bin/python3，把 ProgramArguments 第一项也一并替换：
launchctl bootout gui/$(id -u)/agentrouter-auto-signin 2>/dev/null
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/agentrouter-auto-signin.plist
```

日志在 `/tmp/agentrouter-auto-signin.out`；跑不起来时先看 `/tmp/agentrouter-auto-signin.err`。
卸载：`launchctl bootout gui/$(id -u)/agentrouter-auto-signin`

> [!WARNING]
> macOS 上有两个坑，踩中都是「任务静默失败、日志空空如也」：
>
> 1. **别想当然填 `/usr/bin/python3`**——没装 Xcode Command Line Tools 时它只是个占位壳子，命令行里跑会弹安装框，**launchd 里跑直接失败**，错误只进 `.err`。Homebrew 装的通常在 `/opt/homebrew/bin/python3`，一律以 `which python3` 的实际输出为准。
> 2. **脚本不要放在 `~/Documents`、`~/Desktop`、`~/Downloads` 下**——macOS 隐私保护（TCC）会拦截后台进程读取这些目录，报 `Operation not permitted`。推荐放 `~/Library/Application Support/` 或任意普通目录。

#### 🐧 Linux · cron

```cron
10 8 * * *  cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
10 20 * * * cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
```

---

## 🛠️ 手动运行

```bash
python signin.py            # 等同 auto
python signin.py auto       # 签到 + 查余额 + 通知，结果打到 stdout
python signin.py silent     # 同上，但结果写入 checkin.log
python signin.py diagnose   # 只探测网络出口，不登录任何账号
python signin.py --help     # 看用法
```

> [!NOTE]
> 不支持「只查余额不签到」——AgentRouter 的签到是由登录动作触发的，想拿余额就必须登录，登录就等于签到。查询接口一律是只读的，不会重复发放积分。

---

## ⚙️ 工作原理

AgentRouter 基于 New-API 类后端，**登录动作本身就会触发当日签到**，没有独立的签到接口。所以流程只有三步：

| 步骤 | 接口 | 作用 |
|:---:|---|---|
| 1️⃣ 探测出口 | `GET /api/status` | 按「配置的代理 → 直连」依次试探，确认哪个出口能访问站点，同时读出 `quota_per_unit` |
| 2️⃣ 登录签到 | `POST /api/user/login` | 每个账号用独立 Session 登录，登录成功即完成签到 |
| 3️⃣ 查询余额 | `GET /api/user/self` | 带 `New-API-User` 请求头读取 `quota`，按 `quota_per_unit` 折算成美元 |

> [!NOTE]
> **登录失败也返回 HTTP 200**，必须靠响应体的 `success` 字段判断——按状态码判断会误判。失败时 `message` 通常是「用户名或密码错误，或用户已被封禁」。
>
> 余额查询失败只记 `warning`，不会把已经完成的签到改判为失败。
>
> 整个运行受「时间预算」约束（默认 300 秒）：代理挂掉时不会让请求逐个超时把计划任务拖到被系统强杀，而是主动收尾并如实记录。

---

## 🔧 配置

配置写在脚本同目录的 `config.json`（可从 `config.example.json` 复制）。所有字段都可以被环境变量覆盖——环境变量优先级更高，适合临时调试或不想落盘密码的场景。

| `config.json` 字段 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `base_url` | `AGENTROUTER_BASE_URL` | `https://agentrouter.org` | 站点地址，一般不用改 |
| `accounts` | `AGENTROUTER_ACCOUNTS`<br>`AGENTROUTER_ACCOUNTS_JSON` | 无（必填） | 账号数组。环境变量写法见下 |
| `proxies` | `AGENTROUTER_PROXIES` | `[]` | 代理列表，留空即直连 |
| `pushplus.token` | `PUSHPLUS_TOKEN` | `""` | 留空则不推送，签到照常执行 |
| `pushplus.topic` | `PUSHPLUS_TOPIC` | `""` | PushPlus 群组编码，可选 |
| `pushplus.title` | — | `AgentRouter 签到通知` | 推送标题 |
| `pushplus.template` | — | `html` | 推送模板，支持 `html` / `txt` / `markdown` / `json` |
| `request_timeout` | `AGENTROUTER_REQUEST_TIMEOUT` | `25` | 单次请求超时（秒），夹到 5–120 |
| `pushplus_timeout` | `AGENTROUTER_PUSHPLUS_TIMEOUT` | `15` | 推送请求超时（秒），夹到 5–60 |
| `budget_seconds` | `AGENTROUTER_BUDGET_SECONDS` | `300` | 单次运行总预算（秒），夹到 30–540 |
| — | `AGENTROUTER_CONFIG` | 脚本同目录 `config.json` | 指定配置文件路径 |
| — | `AGENTROUTER_LOG` | 脚本同目录 `checkin.log` | 指定日志文件路径 |

**账号的两种环境变量写法**（二选一，`AGENTROUTER_ACCOUNTS_JSON` 优先）：

```bash
# 多行：每行一个 邮箱:密码。只在第一个冒号处分割，密码里有冒号也没关系。
export AGENTROUTER_ACCOUNTS="alice@qq.com:pw-1234
bob@163.com:pw:with:colons"
```

```bash
# JSON：密码含首尾空格时用这个，避免被自动去空格
export AGENTROUTER_ACCOUNTS_JSON='[{"username":"alice@qq.com","password":" pw 1234 "}]'
```

**代理写法**（`proxies` 数组或 `AGENTROUTER_PROXIES`，换行 / 逗号 / 分号都行）：

```text
socks5://用户名:密码@代理地址:端口     # 自动转成 socks5h://，DNS 也走代理
socks5h://用户名:密码@代理地址:端口
http://用户名:密码@代理地址:端口
```

> [!NOTE]
> 如果本机直连不通、需要用 Clash 之类，填 `socks5://127.0.0.1:7890` 即可——Clash 的 `mixed-port` 默认同时接受 HTTP 和 SOCKS5，`http://127.0.0.1:7890` 也是合法的。`requirements.txt` 里的 `requests[socks]` 已经包含 SOCKS 支持。
>
> 就算直连可用，把代理填在前面也无妨：脚本按顺序试，第一个能用的会被选中。

---

## 🧪 排错

| `result` / 现象 | 含义与处理 |
|---|---|
| `OK` | 本次触发了新签到，一切正常 |
| `ALREADY` | 今天已经签过了，属正常状态，余额照常显示 |
| `AUTH_ERROR` | 账号或密码不对。确认填的是**邮箱**，且已在站点绑定邮箱并重置过密码。注意站点不区分「密码错」和「账号被封禁」 |
| `NO_EXIT` | 所有出口都被 WAF 拦截。换一个非机房的代理出口；或确认本机网络是否被限制 |
| `NETWORK` | 连接层面就不通——断网、DNS 异常、代理地址/端口/账密错误 |
| `TIMEOUT` | 已达时间预算。通常是网络严重超时，已成功的部分照常记录，剩余项下次再试 |
| `CONFIG_ERROR` | 配置问题：没建 `config.json`、没填账号、`base_url` 不是 https 等。错误信息里会说明具体是哪一项 |
| `ERROR` | 其他异常。`report` 里带异常摘要，`error_type` 里是异常类型 |
| `ProxyError` / 连接超时 | 代理填写有误，或代理进程没在跑 |
| `返回的不是 JSON` | 出口被中间设备改写响应，换出口 |
| 提示缺少 `requests` | 先在仓库目录执行 `python -m pip install -r requirements.txt` |
| 计划任务没跑 | Windows 用 `Get-ScheduledTaskInfo -TaskName "AgentRouterAutoSignin"` 看 `LastTaskResult`；macOS 先看 `/tmp/agentrouter-auto-signin.err` |
| `checkin.log` 是空的 | 只有 `silent` 模式才写日志。手动跑 `auto` 的结果只打到屏幕 |

**先跑 `python signin.py diagnose`**，它能一次性告诉你每个出口的真实状态，绝大多数问题在这一步就能定位。

---

## 🔐 安全与隐私

- 仓库不含、不内嵌、不传输任何第三方凭据；账号密码只存在于**你自己本机**的 `config.json` 里
- `config.json` 已在 `.gitignore` 中——**别把它提交到任何仓库**，也别贴到聊天记录里
- 日志与通知里账号只保留前 4 位（`alic*****`）；发生异常时，脚本会把密码、PushPlus Token、代理账密从错误信息里替换成 `***`（只替换长度 ≥ 4 的片段，避免误伤正常文本）
- 脚本只作用于**你自己的**账号，可安全 fork、分享

---

## ⚠️ 免责声明

> [!WARNING]
> 本项目为**非官方**工具，与 AgentRouter 无任何隶属关系。签到相关的接口来自站点前端，仅供个人自动化使用。使用风险自负；接口可能随时变动且不另行通知。请遵守站点服务条款，不要用于批量注册、薅羊毛或其他违反站点规则的行为。

---

## 📊 Star History

> 等 star 攒起来之后再补这块曲线图（需要额外配置 `STAR_HISTORY_TOKEN` 并跑一次 Actions）。
> 现在先把位置留给一句话：

<div align="center">

**看到这儿了，说明这脚本大概率对你有用 —— 那就[点个 ⭐ Star](https://github.com/88lin/agentrouter-auto-signin) 吧**

一秒的事，却能在站点改接口、脚本悄悄失灵时，让你还找得到回来的路。

</div>

---

## 📄 协议

[MIT](LICENSE) © 2026 [88lin](https://github.com/88lin)
