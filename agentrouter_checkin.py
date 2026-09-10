#!/usr/bin/env python3
"""AgentRouter 每日自动签到（GitHub Actions 版）。

脚本核心流程：

1. 读取环境变量中的配置（账号、代理、PushPlus Token）。
2. 依次尝试配置的代理，最后再尝试直连。
3. 调用 ``GET /api/status``，确认当前网络出口可以访问 AgentRouter。
4. 逐个账号创建独立 Session，调用 ``POST /api/user/login`` 登录。
5. AgentRouter 的登录动作本身会触发每日签到，不需要额外调用签到接口。
6. 调用 ``GET /api/user/self`` 查询最新余额。
7. 把所有账号结果汇总成一条 PushPlus 通知，并写入 GitHub Step Summary。

与"把配置写在文件顶部"的版本相比，这里的配置全部来自环境变量，
因此本文件可以安全地公开分享，不会泄露任何账号或凭据。

日志写到标准错误，机器可读的 JSON 结果写到标准输出，
这样可以分别被 GitHub Actions 日志和后续步骤消费。

退出码：
    0  全部账号签到成功
    1  部分账号失败
    2  全部账号失败，或找不到可用网络出口
"""

from __future__ import annotations

import html
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Iterable
from urllib.parse import urlsplit

try:
    import requests
    from requests import Response, Session
except ImportError:  # pragma: no cover - 只在依赖缺失时触发
    print(
        '缺少依赖，请先安装：'
        'python3 -m pip install "requests[socks]>=2.28.0"',
        file=sys.stderr,
    )
    raise


# ============================================================================
# 配置区域（全部来自环境变量，可安全公开本文件）
# ============================================================================
#
# 需要配置的环境变量：
#
#   AR_ACCOUNTS      必填。多行文本，每行一个账号，格式：用户名:密码
#                    密码中可以包含冒号，脚本只在第一个冒号处分割。
#   AR_ACCOUNTS_JSON 可选。JSON 数组，优先级高于 AR_ACCOUNTS。
#                    格式：[{"username": "...", "password": "..."}]
#   AR_BASE_URL      可选。站点地址，默认 https://agentrouter.org
#   AR_PROXIES       可选。多行或逗号分隔的代理列表，留空表示直连。
#   PUSHPLUS_TOKEN   可选。留空则跳过通知，签到流程照常执行。
#   PUSHPLUS_TOPIC   可选。PushPlus 群组编码。
#
# 在 GitHub 上，AR_ACCOUNTS / AR_PROXIES / PUSHPLUS_TOKEN 应配置为
# Repository secrets，不要写进仓库文件。


def _env(name: str, default: str = "") -> str:
    """读取环境变量，空字符串视为未设置。"""

    value = os.environ.get(name)
    if value is None:
        return default
    value = value.strip()
    return value or default


def load_accounts() -> list[dict[str, str]]:
    """从环境变量解析账号列表。

    优先使用 ``AR_ACCOUNTS_JSON``（JSON 数组），否则回退到 ``AR_ACCOUNTS``
    （每行一个 ``用户名:密码``）。空行和以 ``#`` 开头的行会被忽略。

    只在第一个冒号处分割，因此密码中出现冒号不会产生解析歧义。
    """

    raw_json = _env("AR_ACCOUNTS_JSON")
    if raw_json:
        try:
            payload = json.loads(raw_json)
        except ValueError as exc:
            raise ValueError("AR_ACCOUNTS_JSON 不是合法的 JSON") from exc
        if not isinstance(payload, list):
            raise ValueError("AR_ACCOUNTS_JSON 必须是 JSON 数组")
        accounts: list[dict[str, str]] = []
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise ValueError(f"AR_ACCOUNTS_JSON 第 {index} 项必须是对象")
            accounts.append(
                {
                    "username": str(item.get("username", "")).strip(),
                    "password": str(item.get("password", "")),
                }
            )
        return accounts

    raw_text = os.environ.get("AR_ACCOUNTS", "")
    accounts = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(
                f"AR_ACCOUNTS 第 {line_number} 行缺少冒号，格式应为 用户名:密码"
            )
        username, password = line.split(":", 1)
        accounts.append({"username": username.strip(), "password": password})
    return accounts


def load_proxies() -> list[str]:
    """从环境变量解析代理列表，兼容换行、逗号和分号分隔。"""

    raw = os.environ.get("AR_PROXIES", "")
    if not raw.strip():
        return []
    normalized = raw.replace(";", "\n").replace(",", "\n")
    return [item.strip() for item in normalized.splitlines() if item.strip()]


BASE_URL = _env("AR_BASE_URL", "https://agentrouter.org").rstrip("/")
ACCOUNTS = load_accounts()
PROXIES = load_proxies()

PUSHPLUS_TOKEN = _env("PUSHPLUS_TOKEN")
PUSHPLUS_TOPIC = _env("PUSHPLUS_TOPIC")
PUSHPLUS_TITLE = _env("PUSHPLUS_TITLE", "AgentRouter 签到通知")
PUSHPLUS_TEMPLATE = _env("PUSHPLUS_TEMPLATE", "html")

# AgentRouter 请求的最长等待时间，单位为秒。连接和读取共用该值。
REQUEST_TIMEOUT = int(_env("AR_REQUEST_TIMEOUT", "25"))

# PushPlus 请求的最长等待时间，单位为秒。
PUSHPLUS_TIMEOUT = int(_env("AR_PUSHPLUS_TIMEOUT", "15"))

# AgentRouter 的 quota 与美元余额之间的换算单位。
# 原项目使用的换算规则是：500000 quota = 1 美元。
QUOTA_PER_USD = 500000


# ============================================================================
# 日志和结果数据结构
# ============================================================================

# 通知和日志日期统一使用北京时间（UTC+8），与每天的签到日对应。
BEIJING_TZ = timezone(timedelta(hours=8))


class BeijingFormatter(logging.Formatter):
    """把日志时间格式化为北京时间。

    运行环境可能是 UTC（GitHub Actions）或任何其他时区。为了让定时签到
    日志更容易和每天的签到日期对应，这里不依赖本地时区，统一转换为 UTC+8。
    """

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        current = datetime.fromtimestamp(record.created, BEIJING_TZ)
        return current.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
for handler in logging.getLogger().handlers:
    handler.setFormatter(
        BeijingFormatter("%(asctime)s [%(levelname)s] %(message)s")
    )
log = logging.getLogger("agentrouter")


@dataclass
class AccountResult:
    """保存单个账号的签到结果。

    account:
        脱敏后的用户名，只用于日志、终端输出和 PushPlus 通知。
    checked_in:
        True 表示这次登录触发了新签到；False 表示今天已经签到。
    balance_usd:
        根据 quota 换算出的美元余额。
    error:
        登录或签到失败原因。非空时，当前账号视为失败。
    warning:
        签到成功后查询余额遇到的问题。warning 不会把签到本身判为失败。
    """

    account: str
    checked_in: bool = False
    balance_usd: float = 0.0
    error: str = ""
    warning: str = ""


class UpstreamError(Exception):
    """表示 AgentRouter HTTP 响应或响应格式异常。"""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        # retryable 表示这类错误是否值得换下一个代理重新尝试。
        self.retryable = retryable


# ============================================================================
# 通用辅助函数
# ============================================================================

def mask_account(username: str) -> str:
    """脱敏账号，只保留前四个字符。

    例如：user@example.com -> user*****

    账号密码永远不会被输出；账号只在日志和通知中以脱敏形式出现。
    """

    username = str(username or "")
    return f"{username[:4]}*****" if len(username) > 4 else f"{username}*****"


def normalize_proxy(proxy_url: str) -> str:
    """统一代理协议格式。

    requests 配合 PySocks 使用 SOCKS5 时，``socks5h://`` 会让主机名解析也
    通过代理完成。这里兼容常见的 ``socks5://`` 和 ``socks://`` 写法，
    并统一转换成 ``socks5h://``。
    """

    proxy_url = proxy_url.strip()
    if proxy_url.startswith("socks5://"):
        return "socks5h://" + proxy_url[len("socks5://") :]
    if proxy_url.startswith("socks://"):
        return "socks5h://" + proxy_url[len("socks://") :]
    return proxy_url


def proxy_label(proxy_url: str) -> str:
    """生成不会暴露账号密码的代理标签。

    例如：socks5h://user:pass@example.com:1080 -> example.com:1080
    空字符串 -> direct
    """

    if not proxy_url:
        return "direct"
    parsed = urlsplit(proxy_url)
    host = parsed.hostname or "configured-proxy"
    return f"{host}:{parsed.port}" if parsed.port else host


def parse_proxies(values: Iterable[str]) -> list[str]:
    """清理并规范化代理列表，过滤空字符串。"""

    return [normalize_proxy(value) for value in values if str(value).strip()]


def quota_to_usd(quota: Any) -> float:
    """把 AgentRouter 返回的 quota 换算成美元，保留两位小数。

    接口返回值可能是整数、浮点数、数字字符串或空值，因此先尝试转成
    float。遇到无法识别的值时返回 0.0，由上层负责记录警告。
    """

    try:
        return round(float(quota or 0) / QUOTA_PER_USD, 2)
    except (TypeError, ValueError):
        return 0.0


def bjt_date() -> str:
    """返回通知使用的北京时间日期。"""

    return datetime.now(BEIJING_TZ).strftime("%Y年%m月%d日")


def is_placeholder(value: str) -> bool:
    """判断配置值是否仍然是示例占位文字。

    用于避免用户忘记替换示例账号后，脚本直接向真实网站发起请求。
    只匹配明显的模板文字和 IANA 保留的示例域名，避免误伤真实账号。
    """

    markers = (
        "账号1",
        "账号2",
        "你的 ",
        "你的Telegram",
        "你的PushPlus",
        "PushPlus Token",
        "代理地址",
        "代理用户名",
        "example.com",
        "example.org",
    )
    return any(marker in value for marker in markers)


def safe_error(error: object) -> str:
    """清理错误信息中的敏感内容。

    requests 或代理库有时会把完整代理 URL 放进异常文本。这里会尝试移除
    账号密码、PushPlus Token，以及代理 URL / 代理用户名密码，
    最终错误最多保留 500 个字符。

    注意：只对长度 >= 4 的凭据做替换。代理用户名或密码可能只有一个字符，
    若参与替换会把 "https://" 之类的普通文本也一起破坏，反而让错误信息
    无法阅读。
    """

    message = str(error)
    secrets = [PUSHPLUS_TOKEN]
    secrets.extend(str(account.get("password", "")) for account in ACCOUNTS)
    for proxy in PROXIES:
        normalized = normalize_proxy(str(proxy))
        secrets.extend((str(proxy), normalized))
        parsed = urlsplit(normalized)
        if parsed.username:
            secrets.append(parsed.username)
        if parsed.password:
            secrets.append(parsed.password)
    for secret in sorted(set(secrets), key=len, reverse=True):
        if len(secret) >= 4 and not is_placeholder(secret):
            message = message.replace(secret, "***")
    return message[:500]


def validate_config() -> None:
    """校验启动所需的基础配置。

    只检查配置结构和明显的示例占位符，不向网站验证账号密码。
    账号密码是否有效，交给真正的登录请求判断。
    """

    if not BASE_URL.startswith("https://"):
        raise ValueError("AR_BASE_URL 必须使用 https://")
    if not ACCOUNTS:
        raise ValueError(
            "未配置任何账号：请设置 AR_ACCOUNTS 或 AR_ACCOUNTS_JSON"
        )
    for index, account in enumerate(ACCOUNTS, start=1):
        username = str(account.get("username", "")).strip()
        password = str(account.get("password", ""))
        if not username or not password:
            raise ValueError(f"第 {index} 个账号缺少 username 或 password")
        if is_placeholder(username) or is_placeholder(password):
            raise ValueError(f"第 {index} 个账号仍是示例配置，请填写真实账号")


def json_result(result: AccountResult) -> dict[str, Any]:
    """把 dataclass 结果转换成可序列化的字典。"""

    return asdict(result)


def parse_json_response(response: Response, endpoint: str) -> dict[str, Any]:
    """检查 HTTP 响应并解析 JSON。

    处理顺序：
    1. 优先检查响应正文是否包含 aliyun_waf。
    2. 检查 HTTP 状态码，识别 403、408、429 和 5xx 等可重试错误。
    3. 解析 JSON。
    4. 确保 JSON 顶层是对象，避免后续对 list、字符串调用 get()。

    非 JSON 响应通常意味着被 WAF 或上游网关拦截，因此会标记为可重试。
    """

    if "aliyun_waf" in response.text.lower():
        raise UpstreamError(
            f"{endpoint} blocked by Aliyun WAF",
            retryable=True,
        )
    if response.status_code >= 400:
        retryable = response.status_code in {403, 408, 429} or response.status_code >= 500
        raise UpstreamError(
            f"{endpoint} returned HTTP {response.status_code}",
            retryable=retryable,
        )
    try:
        payload = response.json()
    except ValueError as exc:
        if "aliyun_waf" in response.text.lower():
            raise UpstreamError(
                f"{endpoint} blocked by Aliyun WAF",
                retryable=True,
            ) from exc
        raise UpstreamError(
            f"{endpoint} returned a non-JSON response",
            retryable=True,
        ) from exc
    if not isinstance(payload, dict):
        raise UpstreamError(
            f"{endpoint} returned invalid JSON data",
            retryable=True,
        )
    return payload


# ============================================================================
# HTTP Session 和 AgentRouter 接口
# ============================================================================

def create_session(proxy_url: str = "") -> Session:
    """创建一个独立的 requests.Session。

    Session 会自动保存登录过程中收到的 Cookie，并在后续余额请求中复用。
    每个账号都创建自己的 Session，避免多个账号之间共享 Cookie。
    """

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": f"{BASE_URL}/login",
            "Origin": BASE_URL,
        }
    )
    # AgentRouter 的 HTTP 和 HTTPS 请求都使用同一个代理。
    if proxy_url:
        session.proxies.update({"http": proxy_url, "https": proxy_url})
    return session


def find_working_proxy() -> tuple[str | None, str]:
    """寻找可以访问 AgentRouter 的网络出口。

    返回值：
        (代理 URL, 标签)。直连可用时返回 ``("", "direct")``；
        全部失败时返回 ``(None, "")``。

    顺序是配置顺序，直连永远放在最后。这里只调用状态接口，不涉及任何
    账号登录。找到可用出口后，主流程会为每个账号单独创建 Session，
    复用同一个代理 URL。
    """

    attempts = [(proxy, proxy_label(proxy)) for proxy in parse_proxies(PROXIES)]
    attempts.append(("", "direct"))

    for proxy_url, label in attempts:
        session = create_session(proxy_url)
        log.info("testing AgentRouter connection via %s", label)
        try:
            response = session.get(
                f"{BASE_URL}/api/status",
                timeout=REQUEST_TIMEOUT,
            )
            payload = parse_json_response(response, "/api/status")
            # 只有明确返回 success=true 才算连接可用。
            if payload.get("success") is True:
                log.info("connection available via %s", label)
                return proxy_url, label
            log.warning("%s did not report success", label)
        except (requests.RequestException, UpstreamError) as exc:
            log.warning("connection failed via %s: %s", label, safe_error(exc))
        finally:
            session.close()

    return None, ""


def login_and_checkin(
    session: Session, account: dict[str, str]
) -> tuple[dict[str, Any], str]:
    """登录一个账号，并利用登录动作触发每日签到。

    AgentRouter 的真实行为是：``POST /api/user/login`` 成功后，签到已经在
    登录流程中完成。这里不会虚构或调用额外的 /checkin 接口。

    成功返回 ``(登录响应中的 data 字典, "")``，失败返回 ``({}, 错误信息)``。
    """

    username = account["username"]
    try:
        response = session.post(
            f"{BASE_URL}/api/user/login",
            json={"username": username, "password": account["password"]},
            timeout=REQUEST_TIMEOUT,
        )
        payload = parse_json_response(response, "/api/user/login")
    except (requests.RequestException, UpstreamError) as exc:
        return {}, safe_error(exc)

    # success=false 时，message 通常包含"用户名或密码错误"等真实原因。
    if payload.get("success") is not True:
        return {}, str(payload.get("message") or "login failed")
    data = payload.get("data")
    if not isinstance(data, dict):
        return {}, "login response did not contain valid data"

    log.info("login successful: %s", mask_account(username))
    return data, ""


def get_balance(session: Session, user_data: dict[str, Any]) -> tuple[float, str]:
    """使用当前登录 Session 查询最新余额。

    当前 AgentRouter 网页前端登录成功后，主要依靠 Session 中的 Cookie
    维持登录状态，并在请求头中提供用户 ID，因此 ``access_token`` 不是
    必填字段。

    兼容处理：
        - ``id`` 是余额接口需要的用户 ID，缺少它时无法构造请求。
        - 如果旧版本接口仍返回 ``access_token``，就额外加入 Authorization
          请求头；没有返回时完全依靠 Session Cookie。

    只有登录成功但余额查询失败时才返回 warning，这不会把已经完成的签到
    改成失败。
    """

    user_id = user_data.get("id")
    if user_id in (None, ""):
        return 0.0, "check-in succeeded but user id was missing"

    balance_headers = {
        "New-API-User": str(user_id),
        "Accept": "application/json",
    }
    access_token = user_data.get("access_token")
    if access_token:
        balance_headers["Authorization"] = str(access_token)

    try:
        response = session.get(
            f"{BASE_URL}/api/user/self",
            headers=balance_headers,
            timeout=REQUEST_TIMEOUT,
        )
        payload = parse_json_response(response, "/api/user/self")
    except (requests.RequestException, UpstreamError) as exc:
        return 0.0, f"balance lookup failed: {safe_error(exc)}"

    if payload.get("success") is not True:
        return 0.0, "balance lookup returned an unsuccessful response"
    data = payload.get("data")
    if not isinstance(data, dict):
        return 0.0, "balance lookup returned invalid data"
    quota = data.get("quota", 0)
    try:
        float(quota)
    except (TypeError, ValueError):
        return 0.0, "balance value was invalid"
    return quota_to_usd(quota), ""


def process_account(proxy_url: str, account: dict[str, str]) -> AccountResult:
    """处理一个账号的完整流程：建独立 Session、登录签到、查询余额。

    每个账号使用独立的 Session，避免多个账号之间共享 Cookie 造成串号。
    """

    username = account["username"]
    result = AccountResult(account=mask_account(username))
    session = create_session(proxy_url)
    try:
        user_data, error = login_and_checkin(session, account)
        if error:
            result.error = error
            return result

        if "checked_in" not in user_data:
            # 部分后端版本不返回该字段，此时无法判断本次是否触发新签到。
            log.info(
                "login response had no checked_in field: %s",
                mask_account(username),
            )
        result.checked_in = bool(user_data.get("checked_in"))
        result.balance_usd, result.warning = get_balance(session, user_data)
        return result
    finally:
        session.close()


# ============================================================================
# PushPlus 通知与 GitHub Step Summary
# ============================================================================

def build_pushplus_message(results: list[AccountResult]) -> str:
    """根据全部账号结果生成一条 HTML 格式的 PushPlus 消息。

    失败账号会显示错误，但不会计入总余额。账号名和错误文本会经过 HTML
    转义，避免用户名或上游错误中的特殊字符破坏消息格式。
    """

    successful = [result for result in results if not result.error]
    total_balance = sum(result.balance_usd for result in successful)
    lines = [
        "<b>AgentRouter 签到通知</b>",
        "----------------",
        f"📅 <b>日期</b>：{html.escape(bjt_date())}",
        f"✅ <b>账号数</b>：{len(results)}",
        "----------------",
    ]
    for result in results:
        account = html.escape(result.account)
        lines.append(f"👉 账号：{account}")
        if result.error:
            lines.append(f"   ❌ 登录失败：{html.escape(result.error[:240])}")
        elif result.checked_in:
            lines.append(f"   🎉 签到成功，余额 ${result.balance_usd:,.2f}")
        else:
            lines.append(f"   ✅ 今日已签到，余额 ${result.balance_usd:,.2f}")
        if result.warning:
            lines.append(f"   ⚠️ {html.escape(result.warning[:240])}")
    lines.extend(
        [
            "----------------",
            f"💰 <b>总余额</b>：${total_balance:,.2f}",
        ]
    )
    return "\n".join(lines)


def send_pushplus_notification(results: list[AccountResult]) -> bool:
    """发送 PushPlus 汇总通知。

    通知是签到后的附加动作：
    - 未配置 Token 时跳过，并返回 False。
    - 请求失败、响应不是 JSON 或 PushPlus 返回非 200 code 时记录日志，
      并返回 False。
    - 通知失败不会撤销账号已经完成的签到。

    PushPlus 的 code=200 代表服务端已接收发送请求，不代表微信等最终渠道
    已完成投递；这里的返回值表示"请求已被接受"。
    """

    if not PUSHPLUS_TOKEN or is_placeholder(PUSHPLUS_TOKEN):
        log.info("PushPlus Token 为空，跳过通知")
        return False

    payload: dict[str, Any] = {
        "token": PUSHPLUS_TOKEN,
        "title": PUSHPLUS_TITLE,
        "content": build_pushplus_message(results),
        "template": PUSHPLUS_TEMPLATE,
    }
    if PUSHPLUS_TOPIC:
        payload["topic"] = PUSHPLUS_TOPIC

    url = "https://www.pushplus.plus/send"
    try:
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=PUSHPLUS_TIMEOUT,
        )
    except requests.RequestException as exc:
        log.error("PushPlus notification failed: %s", safe_error(exc))
        return False

    # PushPlus 的失败原因在 JSON 的 code 和 msg 字段中。先读取响应正文，
    # 再判断 HTTP 状态，避免丢失服务端返回的具体原因。
    try:
        body = response.json()
    except ValueError as exc:
        status = getattr(response, "status_code", "unknown")
        log.error(
            "PushPlus notification failed: HTTP %s: response was not valid JSON (%s)",
            status,
            safe_error(exc),
        )
        return False

    if (
        isinstance(body, dict)
        and body.get("code") == 200
        and response.status_code < 400
    ):
        log.info("PushPlus notification request accepted")
        return True

    status = getattr(response, "status_code", "unknown")
    if isinstance(body, dict):
        error_code = body.get("code", status)
        description = body.get("msg", "unknown error")
        message = f"HTTP {status}, PushPlus code {error_code}: {description}"
    else:
        message = f"HTTP {status}: invalid PushPlus response"
    log.error("PushPlus notification failed: %s", safe_error(message))
    return False


def write_step_summary(results: list[AccountResult], proxy_label_used: str) -> None:
    """把签到结果写入 GitHub Actions 的 Step Summary。

    只有在 GitHub Actions 环境中（存在 GITHUB_STEP_SUMMARY）才有动作，
    本地运行时直接返回。这样在 Actions 页面上会显示一张结果表格，
    不必去翻日志。
    """

    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return

    def cell(value: str) -> str:
        return html.escape(str(value)).replace("|", "\\|").replace("\n", " ")

    total_balance = sum(r.balance_usd for r in results if not r.error)
    lines = [
        "## AgentRouter 每日签到结果",
        "",
        f"- 日期（北京时间）：{bjt_date()}",
        f"- 网络出口：`{cell(proxy_label_used)}`",
        f"- 账号数量：{len(results)}",
        "",
        "| 账号 | 状态 | 余额 (USD) | 备注 |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        if result.error:
            status = "❌ 失败"
            note = result.error
        elif result.checked_in:
            status = "🎉 签到成功"
            note = result.warning or "-"
        else:
            status = "✅ 今日已签到"
            note = result.warning or "-"
        lines.append(
            f"| {cell(result.account)} | {status} | ${result.balance_usd:,.2f} | {cell(note)} |"
        )
    lines.extend(["", f"**总余额：${total_balance:,.2f}**", ""])

    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines))
    except OSError as exc:  # pragma: no cover - 只在磁盘异常时触发
        log.warning("无法写入 Step Summary: %s", safe_error(exc))


# ============================================================================
# 主流程和退出码
# ============================================================================

def main() -> int:
    """脚本入口，返回进程退出码。"""

    try:
        validate_config()
    except ValueError as exc:
        log.error("配置校验失败: %s", exc)
        return 2

    log.info("AgentRouter 签到开始，共 %d 个账号", len(ACCOUNTS))
    proxy_url, label = find_working_proxy()
    if proxy_url is None:
        log.error("找不到可用的网络出口，签到中止")
        write_step_summary(
            [
                AccountResult(
                    account=mask_account(account["username"]),
                    error="找不到可用的网络出口",
                )
                for account in ACCOUNTS
            ],
            "unavailable",
        )
        return 2

    results: list[AccountResult] = []
    for account in ACCOUNTS:
        result = process_account(proxy_url, account)
        results.append(result)
        # 机器可读结果写标准输出，一行一个账号。
        print(json.dumps(json_result(result), ensure_ascii=False), flush=True)

    send_pushplus_notification(results)
    write_step_summary(results, label)

    successful = [result for result in results if not result.error]
    total_balance = sum(result.balance_usd for result in successful)
    log.info(
        "签到完成：成功 %d / 共 %d，总余额 $%.2f",
        len(successful),
        len(results),
        total_balance,
    )

    if len(successful) == len(results):
        return 0
    if successful:
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
