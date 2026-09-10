<div align="center">

<img src="assets/cover.svg" alt="agentrouter-auto-signin —— AgentRouter 每日自动签到脚本" width="100%">

# 🚀 agentrouter-auto-signin

**每天自动完成 AgentRouter 签到，并把余额查回给你**

[![License: MIT](https://img.shields.io/badge/License-MIT-8B5CF6?style=flat&logo=opensourceinitiative&logoColor=white)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Win%20%7C%20macOS%20%7C%20Linux-F43F5E?style=flat&logo=windows&logoColor=white)]()
[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat&logo=python&logoColor=white)]()
[![Stars](https://img.shields.io/github/stars/88lin/agentrouter-auto-signin?style=flat&logo=github&logoColor=white&color=F59E0B)](https://github.com/88lin/agentrouter-auto-signin/stargazers)

</div>

AgentRouter 的签到没有独立接口——**登录动作本身就会触发当日签到**。这个脚本就是每天帮你登录一次：顺带把余额查回来，结果落成一行 JSON 或写进日志。

- 只在本机跑，配置留在你自己的 `config.json` 里，仓库不含任何凭据
- 脚本没有代理配置项，跟随系统网络环境；打不开站点时开 Clash 的 **TUN 模式**即可
- 幂等：重复运行不会多领（实测连跑两次余额不变），多跑几次没有副作用
- 支持多账号，每个账号独立会话，一个失败不影响其他
- 结果一行 JSON：`result` 给程序看，`report` 给人看

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

## 快速开始

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

然后跑一次：

```bash
python signin.py diagnose     # 先确认站点可达，看到 OK 就行
python signin.py auto         # 正式签到
```

看到 `"result": "OK"`、`report` 里报出余额，就通了。之后挂上定时任务即可。

**前提**：账号要**绑定邮箱并重置过一次密码**。站点支持 GitHub / LinuxDo 登录，但脚本走的是邮箱 + 密码。

---

## 挂上定时任务

脚本每天会建两个任务，时间分别是 **08:10** 和 **20:10**。

> **每日签到在凌晨 00:00 重置到第二天**，且一天只算一次——重复运行不加积分。
>
> 那为什么跑两次？**08:10 那次签当天**；**20:10 是兜底**，专门应付早上电脑没开机的情况。多跑一次成本几乎为零，但能避免整天漏签。

### 🪟 Windows

在仓库目录下执行一条命令，任务会自动建好（用 `pythonw.exe`，无窗口、零打扰）：

```powershell
powershell -ExecutionPolicy Bypass -File .\install-windows.ps1
```

| 任务 | 频率 | 干什么 |
|---|---|---|
| `AgentRouterAutoSignin` | 每天 08:10 | 签到 + 查余额，静默写 `checkin.log` |
| `AgentRouterRetrySignin` | 每天 20:10 | 兜底重试 |

装完会打印下次运行时间。查看日志 `Get-Content checkin.log -Tail 5`。

卸载：

```powershell
Unregister-ScheduledTask -TaskName "AgentRouterAutoSignin" -Confirm:$false
Unregister-ScheduledTask -TaskName "AgentRouterRetrySignin" -Confirm:$false
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
10 8 * * *  cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
10 20 * * * cd /path/to/agentrouter-auto-signin && /usr/bin/python3 signin.py silent
```

---

## 子命令

```bash
python signin.py            # 等同 auto
python signin.py auto       # 签到 + 查余额，结果打到 stdout
python signin.py silent     # 同上，但结果写入 checkin.log（配合定时任务）
python signin.py diagnose   # 只确认站点是否可达，不登录任何账号
python signin.py --help     # 看用法
```

> [!NOTE]
> 没有「只查余额不签到」这个模式——想拿余额就必须登录，而登录就等于签到。

---

## 配置

`config.json` 放在脚本同目录（可从 `config.example.json` 复制）。每一项都能被环境变量覆盖，环境变量优先级更高。

| 字段 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `accounts` | `AGENTROUTER_ACCOUNTS`<br>`AGENTROUTER_ACCOUNTS_JSON` | 无（必填） | 账号数组 |
| `base_url` | `AGENTROUTER_BASE_URL` | `https://agentrouter.org` | 站点地址，一般不用改 |
| `request_timeout` | `AGENTROUTER_REQUEST_TIMEOUT` | `25` | 单次请求超时（秒），夹到 5–120 |
| `budget_seconds` | `AGENTROUTER_BUDGET_SECONDS` | `300` | 单次运行总预算（秒），夹到 30–540 |
| — | `AGENTROUTER_CONFIG` | 脚本同目录 `config.json` | 指定配置文件路径 |
| — | `AGENTROUTER_LOG` | 脚本同目录 `checkin.log` | 指定日志文件路径 |

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

**网络：脚本里没有任何代理配置项**，它会跟随你系统的网络环境，不用也不能在这里配。

如果你的网络打不开 agentrouter.org，**开 Clash 的 TUN 模式**就好——TUN 在网络层接管流量，脚本完全无感知，不需要改任何配置。

> [!IMPORTANT]
> 站点用阿里云 WAF 拦**机房 / 脏的公共出口 IP**。所以能不能连上取决于**出口 IP 的类型，而不是"用没用代理"**：
> 住宅 / 家宽节点完全正常，机房节点容易被拦（实测 GitHub Actions 的机房 IP 必被拦，住宅出口正常）。
> 如果你报 `NO_EXIT`，换一个住宅出口的节点试试，而不是关掉代理。

---

## 输出结果

`auto` 打到屏幕、`silent` 追加到 `checkin.log`，都是每行一条 JSON：

```json
{"time": "2026-09-11 08:10:04", "result": "OK", "report": "签到成功 1 个账号，总余额 $25.00", "accounts": [{"account": "alic*****", "checked_in": true, "balance_usd": 25.0, "error": "", "warning": ""}], "total_balance_usd": 25.0}
```

```text
[2026-09-11 08:10:04] {"time": "...", "result": "OK", "report": "..."}     # silent 模式多一个时间戳前缀
```

| `result` | 含义 | 退出码 |
|---|---|:--:|
| `OK` | 登录并签到成功，余额已查回 | 0 |
| `PARTIAL` | 多账号里有一部分失败 | 1 |
| `AUTH_ERROR` | 账号或密码不对 | 2 |
| `NO_EXIT` | 站点返回了 WAF 拦截页 | 2 |
| `NETWORK` | 连不上站点 | 2 |
| `TIMEOUT` | 已达时间预算 | 2 |
| `CONFIG_ERROR` | 配置有问题 | 2 |
| `ERROR` | 其他异常 | 2 |

> 没有「今日已签到」这个状态码：实测站点每次登录都返回 `checked_in: true`，
> 据此判断不出当天是不是第一次签，硬分只会得到假结论。所以成功一律是 `OK`，
> 签到本身由服务端按天判定，重复运行不会多领。

> 整个运行受「时间预算」约束（默认 300 秒）：网络严重超时时不会让请求逐个挂死把定时任务拖到被系统强杀，而是主动收尾并把已成功的部分如实记下来。

---

## 它是怎么跑的

| 步骤 | 接口 | 作用 |
|:---:|---|---|
| 1️⃣ | `GET /api/status` | 确认站点可达，同时读出余额换算单位 `quota_per_unit` |
| 2️⃣ | `POST /api/user/login` | 每个账号独立会话登录，登录成功即完成签到 |
| 3️⃣ | `GET /api/user/self` | 带 `New-API-User` 头读 `quota`，按 `quota_per_unit` 折算美元 |

四个接口细节，写在了代码注释里，也值得知道：

1. **登录失败也返回 HTTP 200**，必须看响应体的 `success` 字段——按状态码判断会误判。
2. `quota_per_unit` 从接口读，不写死。站点哪天改比例，余额不会算错。
3. 密码错误和账号被封禁返回**同一句话**（「用户名或密码错误，或用户已被封禁」），站点不区分。
4. 登录响应里的 `quota` 恒为 `0`，不能用——真实余额只在 `/api/user/self` 里。同理 `checked_in` 恒为 `true`，也判断不出是否当天首次签到。

---

## 排错

| 现象 | 处理 |
|---|---|
| `AUTH_ERROR` | 确认填的是**邮箱**，且已在站点绑定邮箱并重置过密码 |
| `NO_EXIT` | 站点返回了 WAF 拦截页，通常是当前出口 IP 是机房 / 脏 IP 被风控。换一个住宅出口的节点再试；跑 `diagnose` 可确认是哪一类失败 |
| `NETWORK` | 连不上站点：断网、DNS 异常、被本地防火墙拦截 |
| `TIMEOUT` | 网络严重超时，已成功的部分照常记录，剩余项下次再试 |
| `CONFIG_ERROR` | 没建 `config.json`、没填账号、`base_url` 不是 https 等，报错信息里会写明是哪一项 |
| `ERROR` | 其他异常，`report` 里有摘要，`error_type` 里是异常类型 |
| 提示缺少 `requests` | 先在仓库目录跑 `python -m pip install -r requirements.txt` |
| 任务没跑 | Win：`Get-ScheduledTaskInfo -TaskName "AgentRouterAutoSignin"` 看 `LastTaskResult`；macOS：先看 `/tmp/agentrouter-auto-signin.err` |
| `checkin.log` 是空的 | 只有 `silent` 模式才写日志，手动跑 `auto` 的结果只打到屏幕 |

**拿不准就先跑 `python signin.py diagnose`**，它会直接告诉你站点是否可达、是不是被 WAF 拦，绝大多数问题在这一步就能定位。

---

## 几句提醒

- **连不上站点时，看的是出口 IP 类型，不是有没有开代理。** 站点拦的是机房 / 脏的公共 IP；住宅 / 家宽出口完全正常。打不开就开 TUN 换到你的住宅节点，别反过来关掉它。
- 重复运行是安全的：签到一天只算一次，**凌晨 00:00 重置到第二天**，多跑不加积分。
- 账号只在你本机的 `config.json`，且已被 `.gitignore` 排除——别把它提交到任何仓库，也别贴到聊天记录里。日志里账号只保留前 4 位（`alic*****`）。
- 余额查不到只记 `warning`，不会把已经完成的签到改判为失败。

## 免责声明

> [!WARNING]
> 本项目为**非官方**工具，与 AgentRouter 无任何隶属关系。接口来自站点前端，仅供个人自动化使用。使用风险自负；接口可能随时变动且不另行通知。请遵守站点服务条款，不要用于批量注册、薅羊毛或其他违反规则的行为。

---

<div align="center">

**如果这脚本对你有用，顺手[点个 ⭐ Star](https://github.com/88lin/agentrouter-auto-signin)**

站点改接口、脚本悄悄失灵时，你能一秒翻回这里。

</div>

## 协议

[MIT](LICENSE) © 2026 [88lin](https://github.com/88lin)
