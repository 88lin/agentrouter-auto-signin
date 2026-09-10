# 🚀 AgentRouter 每日自动签到（GitHub Actions 版）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Check-in](https://github.com/88lin/agentrouter-auto-checkin/actions/workflows/checkin.yml/badge.svg)](https://github.com/88lin/agentrouter-auto-checkin/actions/workflows/checkin.yml)

用 GitHub Actions 跑 AgentRouter 的每日签到：**不需要本地开机、不需要常驻进程**。
配好 Secrets，之后每天自动登录、自动触发签到、自动查余额，结果推送到微信。

> 多账号 · 代理自动探测 · PushPlus 通知 · 结果表格化 · 零硬编码凭据

---

## ⚠️ 先看这一条：必须自备代理

AgentRouter 使用阿里云 WAF，**会拦截机房 / 云服务器出口 IP**。
GitHub Actions 的托管运行器正是机房 IP，因此：

- ❌ **不配置代理，签到一定失败**。会在连接探测阶段直接报
  `connection failed via direct: /api/status blocked by Aliyun WAF`。
- ✅ 必须通过 `AR_PROXIES` 提供一个**非机房出口**的代理（家宽、移动网络、原生住宅 IP 等）。
- ✅ 或者改用你自己的机器做 **self-hosted runner**（见文末），那就等价于本地运行，无需代理。

这不是配置错误，是站点风控策略。本项目已用真实 Actions 运行验证过这一点。

---

## 📖 它是怎么工作的

AgentRouter 的**登录动作本身就会触发当日签到**，不需要单独的签到接口。整个流程只有三步：

| 步骤 | 接口 | 作用 |
| --- | --- | --- |
| 1️⃣ 探测出口 | `GET /api/status` | 按「配置顺序 → 直连」依次试探，确认哪个网络出口能访问站点 |
| 2️⃣ 登录签到 | `POST /api/user/login` | 每个账号使用**独立 Session** 登录，登录成功即完成签到 |
| 3️⃣ 查询余额 | `GET /api/user/self` | 读取 `quota`，按 `500000 quota = 1 美元` 换算，并推送通知 |

任何一个账号失败都不会影响其他账号；余额查询失败也**不会**把已完成的签到改判为失败。

---

## ✨ 特性

- **零本地依赖**：签到跑在 GitHub Actions 上，你的电脑不用开机。
- **零硬编码**：账号密码、代理、Token 全部来自环境变量 / Secrets，仓库文件可放心公开。
- **多账号支持**：一个账号一行，或直接丢一个 JSON 数组。
- **代理自动探测**：支持 `socks5://`、`socks5h://`、`http://`，按顺序试，最后才试直连。
- **自动脱敏**：日志、错误信息、通知里账号只显示前 4 位，密码 / 代理凭据自动替换为 `***`。
- **自带诊断模式**：一条命令测出哪个代理出口可用，不用反复改工作流试错。
- **可读结果**：Actions 页面直接生成结果表格（Step Summary），不必翻日志。
- **微信推送**：可选接入 PushPlus，签到完成推一条 HTML 汇总消息。
- **规范退出码**：`0` 全部成功、`1` 部分失败、`2` 全部失败，失败会在 Actions 里标红提醒。

---

## 🚀 快速开始

### 第 1 步：Fork 本仓库

点右上角 **Fork**，得到你自己的副本（例如 `你的用户名/agentrouter-auto-checkin`）。

> 💡 不想让仓库出现在自己主页上，可在 Fork 后到 Settings 里改成 Private。GitHub Actions 在私有仓库也有免费额度。

### 第 2 步：配置 Secrets

进入你 Fork 后的仓库 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**。

| Secret 名称 | 是否必填 | 值 |
| --- | --- | --- |
| `AR_ACCOUNTS` | ✅ 必填 | 每行一个账号，格式 `用户名:密码`。例如两行：<br>`me@example.com:my-password`<br>`other@example.com:another-password` |
| `AR_PROXIES` | ✅ 必填（见上文） | 代理列表，换行或逗号分隔，例如 `socks5://user:pass@1.2.3.4:1080` |
| `PUSHPLUS_TOKEN` | 可选 | 微信推送。留空则不推送，签到照常执行 |
| `PUSHPLUS_TOPIC` | 可选 | PushPlus 群组编码，想推送给群组时填写 |
| `AR_ACCOUNTS_JSON` | 可选 | JSON 数组写法，优先级高于 `AR_ACCOUNTS`，适合密码含首尾空格的场景 |

> ⚠️ **密码里包含冒号也没关系**——脚本只在**第一个冒号**处分割，冒号之后的内容整体视为密码。
> 但账号行的首尾空格会被去掉，密码若以空格开头或结尾，请改用 `AR_ACCOUNTS_JSON`。

### 第 3 步：先诊断出口，再跑签到

在本地或 Actions 上跑一次诊断，确认哪个出口可用：

```bash
python agentrouter_checkin.py --diagnose
```

输出示例：

```text
OK    your-proxy.example.com:1080
FAIL  direct  /api/status blocked by Aliyun WAF
```

看到至少一个 `OK` 之后再正式签到。然后在仓库 **Actions** 标签页：
左侧选 **AgentRouter 每日签到** → 右侧 **Run workflow** → 确认每一步都是绿色 ✅，
并查看 **Summary** 里的结果表格。

---

## ⚙️ 全部可选配置

除账号和代理之外，其余参数都有默认值，不配置也能跑。想覆盖默认值时，在
**Settings → Secrets and variables → Actions → Variables 标签页** 新建 Repository variable：

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `AR_BASE_URL` | `https://agentrouter.org` | 站点地址，一般不需要改 |
| `PUSHPLUS_TITLE` | `AgentRouter 签到通知` | 推送标题 |
| `PUSHPLUS_TEMPLATE` | `html` | 推送模板，支持 `html` / `txt` / `markdown` / `json` |
| `AR_REQUEST_TIMEOUT` | `25` | 单次请求超时（秒） |
| `AR_PUSHPLUS_TIMEOUT` | `15` | PushPlus 请求超时（秒） |

---

## 🌐 关于代理

脚本的探测顺序是：**你配置的代理（按填写顺序）→ 直连**，第一个 `GET /api/status`
返回 `success: true` 的出口会被选中，后续所有账号复用这个出口。

支持的写法：

```text
socks5://用户名:密码@代理地址:端口     # 自动转换为 socks5h://，DNS 也走代理
socks5h://用户名:密码@代理地址:端口
http://用户名:密码@代理地址:端口
```

排查思路：

| 现象 | 原因 |
| --- | --- |
| `blocked by Aliyun WAF` | 该出口是机房 IP，被风控。换住宅 / 家宽出口 |
| `returned a non-JSON response` | 出口被上游网关拦截，或被中间设备改写响应 |
| `returned HTTP 403 / 429` | 出口被限流，脚本会继续尝试下一个出口 |
| `ProxyError` / timeout | 代理地址、端口或账密错误 |

---

## 🖥️ 本地 / 自建运行

脚本不依赖 GitHub 环境，本地同样可以跑（本地通常是家宽出口，直连往往就能成功）。

```bash
python -m pip install -r requirements.txt

# Linux / macOS
export AR_ACCOUNTS="me@example.com:my-password"
export PUSHPLUS_TOKEN="你的token"

# Windows PowerShell
# $env:AR_ACCOUNTS="me@example.com:my-password"

python agentrouter_checkin.py
```

**self-hosted runner**：如果你有一台常开的机器或国内 VPS，把它注册为 runner 并把
`.github/workflows/checkin.yml` 里的 `runs-on: ubuntu-latest` 改成 `runs-on: self-hosted`，
就能既享受 Actions 的定时调度、又避开机房 IP 风控。

想用 crontab 定时（示例：每天 08:10）：

```cron
10 8 * * * cd /path/to/repo && /usr/bin/python3 agentrouter_checkin.py >> checkin.log 2>&1
```

---

## 📊 运行结果

**标准输出**是机器可读的 JSON，一行一个账号：

```json
{"account": "me@*****", "checked_in": true, "balance_usd": 12.34, "error": "", "warning": ""}
```

**标准错误**是带北京时间戳的可读日志：

```text
2026-09-11 08:10:03 [INFO] AgentRouter 签到开始，共 2 个账号
2026-09-11 08:10:04 [INFO] testing AgentRouter connection via my-proxy.example.com:1080
2026-09-11 08:10:05 [INFO] connection available via my-proxy.example.com:1080
2026-09-11 08:10:06 [INFO] login successful: me@*****
2026-09-11 08:10:07 [INFO] 签到完成：成功 2 / 共 2，总余额 $24.68
```

---

## ⏰ 关于定时

- GitHub Actions 的 `cron` 使用 **UTC 时间**。仓库默认配置了两个时间点，对应北京时间 **08:10** 和 **14:10**；第二个是兜底——GitHub 在高负载时段可能延迟甚至丢弃定时任务，多跑一次能提高成功率（重复登录不会出问题，第二次会显示"今日已签到"）。
- 想改时间，编辑 `.github/workflows/checkin.yml` 里的 `cron`。北京时间减 8 小时即 UTC 时间。
- **公开仓库的定时工作流在 60 天无提交活动后会被自动停用**，GitHub 会发邮件提醒，到 Actions 页面点 Enable 即可恢复。

---

## ❓ 常见问题

**Q：Actions 一直报 `blocked by Aliyun WAF`，是我的配置错了吗？**
不是。这是站点风控拦截机房 IP 的正常结果。按上文配置 `AR_PROXIES` 即可。

**Q：会泄露我的账号密码吗？**
不会。仓库不含任何凭据，账号只存在于你仓库的 Secrets 里，GitHub 会加密存储并自动打码日志
（本项目的实测日志中 `AR_ACCOUNTS` 显示为 `***`）。脚本内部还有一层 `safe_error()`
清洗，会把长度 ≥ 4 的密码、Token、代理凭据从异常信息中替换为 `***`。

**Q：Fork 之后改成了 Private，为什么 Actions 不跑了？**
私有仓库的 Actions 会消耗额度（免费账户 2000 分钟/月）。本工作流每次运行不到 1 分钟，日常够用。
额度耗尽需升级计划或改回 Public。

**Q：结果显示"今日已签到"，是失败吗？**
不是。说明当天已经签到过了，属于正常状态，余额会照常显示。

**Q：登录失败提示"用户名或密码错误"？**
AgentRouter 要求先绑定邮箱并重置密码，再使用**邮箱 + 密码**登录，请确认 `AR_ACCOUNTS` 里填的是邮箱。

**Q：能不能换一个"国内可访问"的镜像域名来绕开 WAF？**
不建议。这类镜像域名来源不明，把 `AR_BASE_URL` 指过去等于**把账号密码直接交给第三方**。
要么用自己可控的代理，要么用 self-hosted runner。

**Q：站点接口变了怎么办？**
脚本基于公开的前端接口，站点升级后可能需要同步调整。欢迎提 Issue，或自行修改 `agentrouter_checkin.py`。

---

## ⚠️ 免责声明

- 本项目是社区脚本，**与 AgentRouter 官方无关**，仅用于自动完成个人账号的日常登录，省去手动操作。
- 请自行确认使用行为符合站点服务条款，因使用本脚本产生的账号风险由使用者自行承担。
- 请勿将本项目用于批量注册、薅羊毛或其他违反站点规则的行为。

## 📄 License

[MIT](./LICENSE) © 2026 88lin
