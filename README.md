# 🚀 AgentRouter 每日自动签到（GitHub Actions 版）

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Check-in](https://github.com/88lin/agentrouter-auto-checkin/actions/workflows/checkin.yml/badge.svg)](https://github.com/88lin/agentrouter-auto-checkin/actions/workflows/checkin.yml)

用 GitHub Actions 免费跑 AgentRouter 的每日签到：**不需要服务器、不需要本地开机、不需要常驻进程**。
配好一次 Secrets，之后每天自动登录、自动触发签到、自动查余额，结果推送到微信。

> 多账号 · SOCKS5 代理自动探测 · PushPlus 通知 · 结果表格化 · 零硬编码凭据

---

## 📖 它是怎么工作的

AgentRouter 的**登录动作本身就会触发当日签到**，不需要单独的签到接口。所以整个流程只有三步：

| 步骤 | 接口 | 作用 |
| --- | --- | --- |
| 1️⃣ 探测出口 | `GET /api/status` | 按「配置顺序 → 直连」依次试探，确认哪个网络出口能访问站点 |
| 2️⃣ 登录签到 | `POST /api/user/login` | 每个账号使用**独立 Session** 登录，登录成功即完成签到 |
| 3️⃣ 查询余额 | `GET /api/user/self` | 读取 `quota`，按 `500000 quota = 1 美元` 换算，并推送通知 |

任何一个账号失败都不会影响其他账号；余额查询失败也**不会**把已完成的签到改判为失败。

---

## ✨ 特性

- **零服务器**：完全跑在 GitHub Actions 的免费额度内，每次运行不到 1 分钟。
- **零硬编码**：账号密码、代理、Token 全部来自环境变量 / Secrets，仓库文件可以放心公开。
- **多账号支持**：一个账号一行，或直接丢一个 JSON 数组。
- **代理自动探测**：支持 `socks5://`、`socks5h://`、`http://`，按顺序试，最后才试直连。
- **自动脱敏**：日志、错误信息、通知里账号只显示前 4 位，密码 / 代理凭据自动替换为 `***`。
- **可读结果**：Actions 页面直接生成结果表格（Step Summary），不必翻日志。
- **微信推送**：可选接入 PushPlus，签到完成推一条 HTML 汇总消息。
- **规范退出码**：`0` 全部成功、`1` 部分失败、`2` 全部失败，失败会在 Actions 里标红提醒。

---

## 🚀 快速开始

### 第 1 步：Fork 本仓库

点右上角 **Fork**，得到你自己的副本（例如 `你的用户名/agentrouter-auto-checkin`）。

> 💡 如果你不想让仓库出现在自己的主页上，也可以在 Fork 后到 Settings 里改成 Private。
> GitHub Actions 在私有仓库同样有免费额度，签到功能不受影响。

### 第 2 步：配置 Secrets

进入你 Fork 后的仓库 → **Settings** → **Secrets and variables** → **Actions** → 点 **New repository secret**。

至少添加这一条：

| Secret 名称 | 是否必填 | 值 |
| --- | --- | --- |
| `AR_ACCOUNTS` | ✅ 必填 | 每行一个账号，格式 `用户名:密码`。例如两行：<br>`me@example.com:my-password`<br>`other@example.com:another-password` |

其余为可选：

| Secret 名称 | 是否必填 | 说明 |
| --- | --- | --- |
| `PUSHPLUS_TOKEN` | 可选 | 微信推送。留空则不推送，签到照常执行 |
| `PUSHPLUS_TOPIC` | 可选 | PushPlus 群组编码，想推送给群组时填写 |
| `AR_PROXIES` | 可选 | 代理列表，换行或逗号分隔，例如 `socks5://user:pass@1.2.3.4:1080` |
| `AR_ACCOUNTS_JSON` | 可选 | JSON 数组写法，优先级高于 `AR_ACCOUNTS`，适合密码含特殊字符的场景 |

> ⚠️ **密码里包含冒号也没关系**——脚本只在**第一个冒号**处分割，冒号之后的内容整体视为密码。
> 如果你的密码以空格开头或结尾，请改用 `AR_ACCOUNTS_JSON` 以避免被自动去空格。

### 第 3 步：启用 Actions 并试跑一次

1. 进入 **Actions** 标签页，若提示需要启用，点 **I understand my workflows, go ahead and enable them**。
2. 左侧选择 **AgentRouter 每日签到** → 右侧 **Run workflow** → **Run workflow**。
3. 打开这次运行记录，确认每一步都是绿色 ✅，并查看 **Summary** 里的结果表格。

跑通之后就不用管了，定时任务会自己执行。

---

## ⚙️ 全部可选配置

除账号之外的所有参数都有合理默认值，不配置也能跑。想覆盖默认值时，在
**Settings → Secrets and variables → Actions → Variables 标签页** 新建 Repository variable：

| 变量名 | 默认值 | 说明 |
| --- | --- | --- |
| `AR_BASE_URL` | `https://agentrouter.org` | 站点地址。国内访问受限时可换成站点提供的备用域名 |
| `PUSHPLUS_TITLE` | `AgentRouter 签到通知` | 推送标题 |
| `PUSHPLUS_TEMPLATE` | `html` | 推送模板，支持 `html` / `txt` / `markdown` / `json` |
| `AR_REQUEST_TIMEOUT` | `25` | 单次请求超时（秒） |
| `AR_PUSHPLUS_TIMEOUT` | `15` | PushPlus 请求超时（秒） |

---

## 🌐 关于网络出口与代理

GitHub Actions 的机器在海外，大多数情况下**可以直连**，因此 `AR_PROXIES` 留空即可。

脚本的探测顺序是：**你配置的代理（按填写顺序）→ 直连**，第一个 `GET /api/status`
返回 `success: true` 的出口会被选中，后续所有账号复用这个出口。

支持的代理写法：

```text
socks5://用户名:密码@代理地址:端口     # 自动转换为 socks5h://，DNS 也走代理
socks5h://用户名:密码@代理地址:端口
http://用户名:密码@代理地址:端口
```

如果出现 `blocked by Aliyun WAF` 或 `returned a non-JSON response`，通常说明当前出口被站点风控拦截，
换一个代理出口即可。

---

## 🖥️ 本地运行

脚本不依赖 GitHub 环境，本地同样可以跑。

```bash
python -m pip install -r requirements.txt

# Linux / macOS
export AR_ACCOUNTS="me@example.com:my-password"
export PUSHPLUS_TOKEN="你的token"

# Windows PowerShell
# $env:AR_ACCOUNTS="me@example.com:my-password"

python agentrouter_checkin.py
```

想放服务器上定时执行，用 crontab 即可（示例：每天 08:10）:

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
2026-09-11 08:10:04 [INFO] testing AgentRouter connection via direct
2026-09-11 08:10:05 [INFO] connection available via direct
2026-09-11 08:10:06 [INFO] login successful: me@*****
2026-09-11 08:10:07 [INFO] 签到完成：成功 2 / 共 2，总余额 $24.68
```

**Actions 页面**会生成结果表格，**微信**会收到一条 PushPlus 汇总消息。

---

## ⏰ 关于定时

- GitHub Actions 的 `cron` 使用 **UTC 时间**。仓库内默认配置了两个时间点，分别对应北京时间 **08:10** 和 **14:10**，第二个是兜底：GitHub 在高负载时段可能延迟甚至丢弃定时任务，多跑一次能显著提高签到成功率（重复登录不会造成问题，第二次会显示"今日已签到"）。
- 想改时间，编辑 `.github/workflows/checkin.yml` 里的 `cron` 即可。北京时间减去 8 小时就是 UTC 时间。
- **公开仓库的定时工作流在 60 天无提交活动后会被自动停用**，届时 GitHub 会发邮件提醒。到 Actions 页面点一下 Enable 即可恢复，或者随手提交一次改动。

---

## ❓ 常见问题

**Q：会泄露我的账号密码吗？**
不会。本仓库不含任何凭据，账号只存在于你仓库的 Secrets 里，GitHub 会对其做加密存储和日志自动打码。脚本内部还有一层 `safe_error()`
清洗，会把密码、Token、代理凭据从异常信息中替换为 `***`。

**Q：Fork 之后改成了 Private，为什么 Actions 不跑了？**
私有仓库的 Actions 需要消耗额度（免费账户每月 2000 分钟）。本工作流每次运行不到 1 分钟，日常使用完全够用。若额度耗尽，需升级计划或改回 Public。

**Q：签到结果显示"今日已签到"是失败吗？**
不是。说明当天已经通过其他方式签到过了，属于正常状态，余额会照常显示。

**Q：登录失败提示"用户名或密码错误"？**
AgentRouter 要求先绑定邮箱并重置密码，再使用**邮箱 + 密码**登录。请确认 `AR_ACCOUNTS` 里填的是邮箱而非用户名。

**Q：站点接口变了怎么办？**
脚本基于公开的前端接口，站点升级后可能需要同步调整。欢迎提 Issue，或自行修改 `agentrouter_checkin.py`。

---

## ⚠️ 免责声明

- 本项目是社区脚本，**与 AgentRouter 官方无关**，仅用于自动完成个人账号的日常登录，省去手动操作。
- 请自行确认使用行为符合站点服务条款，因使用本脚本产生的账号风险由使用者自行承担。
- 请勿将本项目用于批量注册、薅羊毛或其他违反站点规则的行为。

## 📄 License

[MIT](./LICENSE) © 2026 88lin
