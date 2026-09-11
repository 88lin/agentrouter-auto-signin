#!/usr/bin/env python3
"""AgentRouter 每日自动签到（本地版）。

作者：88lin
仓库：https://github.com/88lin/agentrouter-auto-signin

一个自包含的单文件脚本，在你自己的电脑上静默运行，每天自动完成 AgentRouter
的登录签到并查回余额。

核心流程：

1. 读取 ``config.json``（环境变量可覆盖任意一项）。
2. 调用 ``GET /api/status`` 确认站点可达，并读出余额换算单位。
3. 每个账号使用独立 Session 调用 ``POST /api/user/login`` 登录。
4. AgentRouter 的登录动作本身就会触发当日签到，无需额外签到接口。
5. 调用 ``GET /api/user/self`` 查询余额，按站点公布的换算单位折成美元。
6. 汇总成一行 JSON 输出（或写入日志文件）。

用法：

    python signin.py             # 等同 auto
    python signin.py auto        # 立刻签到 + 查余额，结果打到 stdout（手动用）
    python signin.py silent      # 给定时任务用：当天已签成过就直接跳过，
                                 # 否则签到并把结果写进日志文件
    python signin.py diagnose    # 只探测站点是否可达，不登录任何账号

退出码：

    0  全部账号成功（含 silent 判定「今天已签过、跳过」）
    1  部分账号失败
    2  全部账号失败、配置错误，或站点不可达

关于定时任务：``silent`` 会把「今天已经签成了」记进 ``checkin.state``，所以
可以放心地每隔 30 分钟跑一次——成功那天只有第一次真正联网，后面全是空转；
失败才会在下一次运行重试。这是因为系统本身不提供按退出码重试的能力
（Windows 计划任务的 RestartCount 只管「任务起不来」，不管「跑完了返回失败」）。

关于网络：脚本没有任何代理配置项，它会跟随系统的网络环境，不需要也不能在
这里配代理。想换站点域名改 ``base_url`` 即可（环境变量 ``AGENTROUTER_BASE_URL``
优先级更高）。被 WAF 拦截、5xx、响应不是 JSON 这类瞬时失败会自动重试一次；
密码错误之类的业务失败不重试。
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

try:
    import requests
    from requests import Response, Session
except ImportError:  # pragma: no cover - 只在依赖缺失时触发
    print(
        "缺少依赖，请先安装：python -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise


# 脚本所在目录：配置文件和日志文件默认都放在这里，
# 这样从任何工作目录调用（计划任务、launchd、cron）都能正确定位。
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = SCRIPT_DIR / "config.json"
DEFAULT_LOG_PATH = SCRIPT_DIR / "checkin.log"
DEFAULT_STATE_PATH = SCRIPT_DIR / "checkin.state"

# 日志与输出统一使用北京时间（UTC+8）。
BEIJING_TZ = timezone(timedelta(hours=8))

# quota 换算单位的兜底值。正常情况下会优先采用站点 ``/api/status``
# 返回的 ``quota_per_unit``，站点调整比例时脚本会自动跟随。
FALLBACK_QUOTA_PER_UNIT = 500000

# 单次运行的网络时间预算默认值（秒）。防止网络严重超时时请求逐个挂死，
# 把系统计划任务拖到被强杀，导致当天记录整条丢失。
DEFAULT_BUDGET_SECONDS = 300
MAX_BUDGET_SECONDS = 540

# 可重试失败（WAF 拦截、5xx、响应不是 JSON）的尝试次数与退避间隔。
# 只重试一次：站点前面挂着风控，连着猛敲反而更容易被拦，而且每天还有
# 第二个定时任务兜底，这里没必要死磕。
MAX_ATTEMPTS = 2
RETRY_BACKOFF_SECONDS = 3

# 多账号之间的间隔（秒）。一串登录请求连着打过去容易被风控当成异常流量。
ACCOUNT_INTERVAL_SECONDS = 2

# 单次运行允许的最大账号数。
#
# 这是一条刻意写死、不给配置项的硬上限。站点的使用规范把「通过脚本或多重账号
# 批量获取额度」列为重点关注行为，拿几十上百个号来跑签到正是它要拦的事。
# 个人自用（比如个人号 + 工作号）远够用；做成可配置就等于没有上限。
MAX_ACCOUNTS = 10

# silent 模式下，哪些结果码算「今天到此为止、不必再重试」：
#   OK          —— 签到成功，当天已完成
#   AUTH_ERROR  —— 密码错 / 账号被封，重试也没用，还会拿错密码反复登录被站点判定异常
# 其余（NETWORK / NO_EXIT / TIMEOUT / PARTIAL / ERROR）都是可能自愈的临时故障，
# 不写状态，留给下一次定时运行重试。CONFIG_ERROR 发生在联网之前、不碰站点，
# 故意不算「到此为止」——让它每次都如实报错，好让你一眼看到配置坏了。
TERMINAL_RESULTS = ("OK", "AUTH_ERROR")

# 脱敏后缀。mask_account 靠它认出「已经遮过」的值，从而可以重复调用。
MASK_SUFFIX = "*****"

log = logging.getLogger("agentrouter")


class ConfigError(Exception):
    """配置缺失或非法。"""


class UpstreamError(Exception):
    """AgentRouter 的 HTTP 响应或响应格式异常。"""

    def __init__(self, message: str, retryable: bool = False):
        super().__init__(message)
        self.retryable = retryable


class BeijingLogFormatter(logging.Formatter):
    """把日志时间统一格式化为北京时间，便于和签到日期对应。"""

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        current = datetime.fromtimestamp(record.created, BEIJING_TZ)
        return current.strftime(datefmt or "%Y-%m-%d %H:%M:%S")


# ============================================================================
# 配置
# ============================================================================

@dataclass
class Config:
    """运行期配置。所有字段都可以被环境变量覆盖。"""

    # 站点有两个官方域名：ps.air-outer.com（新，默认） / agentrouter.org（旧）
    base_url: str = "https://ps.air-outer.com"
    accounts: list[dict[str, str]] = field(default_factory=list)
    request_timeout: int = 25
    budget_seconds: int = DEFAULT_BUDGET_SECONDS
    log_path: Path = DEFAULT_LOG_PATH
    config_path: Path = DEFAULT_CONFIG_PATH
    # 非致命问题（例如超时值非法被夹到安全值），会随输出一起返回。
    warnings: list[str] = field(default_factory=list)


def _env(name: str) -> str:
    """读取环境变量，空白字符串视为未设置。"""

    value = os.environ.get(name)
    return value.strip() if value and value.strip() else ""


def _env_int(name: str, default: int, warnings: list[str]) -> int:
    """读取整数型环境变量，非法值回退默认值并记录警告。"""

    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        warnings.append(f"{name} 不是合法整数（{raw!r}），已改用默认值 {default}")
        return default


def _clamp(value: int, low: int, high: int, label: str, warnings: list[str]) -> int:
    """把数值夹到安全区间，并在发生夹取时记录警告。"""

    if value < low:
        warnings.append(f"{label} 过小（{value}），已夹到 {low}")
        return low
    if value > high:
        warnings.append(f"{label} 过大（{value}），已夹到 {high}")
        return high
    return value


def _config_int(
    raw: dict[str, Any], key: str, default: int, warnings: list[str]
) -> int:
    """读取配置文件里的整数项，非法值回退默认值并记录警告。

    不能直接 ``int(raw[key])``：配置里手滑写成 ``"abc"`` 或写成数组时，
    裸 int() 会抛到最外层的兜底 except，把一句可修的配置问题伪装成
    「脚本运行异常」，还附一行生英文报错。
    """

    value = raw.get(key)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        warnings.append(f"{key} 不是合法整数（{value!r}），已改用默认值 {default}")
        return default


def resolve_log_path() -> Path:
    """日志文件路径：环境变量优先，否则脚本同目录的 ``checkin.log``。

    单独拎出来是因为它必须在任何校验之前定下：配置报错也得落进用户真正
    在 tail 的那个文件，而不是悄悄写回默认路径。
    """

    return Path(_env("AGENTROUTER_LOG") or DEFAULT_LOG_PATH)


def resolve_state_path() -> Path:
    """状态文件路径：环境变量优先，否则脚本同目录的 ``checkin.state``。"""

    return Path(_env("AGENTROUTER_STATE") or DEFAULT_STATE_PATH)


def read_done_date(path: Path) -> str:
    """读出状态文件里「当天已了结」的日期，读不到就返回空串。

    任何异常都当成「没记录」：状态文件只是省一次请求的优化，它坏了最多
    让今天多签一次（幂等，没有副作用），绝不能因此让签到跑不起来。
    """

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str(data.get("date", "")) if isinstance(data, dict) else ""


def mark_done(path: Path, date: str, result: str) -> None:
    """记下「今天不用再跑了」。写失败只告警，不影响已经完成的签到。"""

    payload = {"date": date, "result": result, "time": bjt_now()}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        log.warning("写入状态文件失败：%s", exc)


def _parse_accounts_from_text(raw_text: str) -> list[dict[str, str]]:
    """解析 ``用户名:密码`` 多行文本。

    只在**第一个**冒号处分割，所以密码里带冒号不会被误切。
    空行和以 ``#`` 开头的行会被忽略。
    """

    accounts: list[dict[str, str]] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ConfigError(
                f"账号配置第 {line_number} 行缺少冒号，格式应为 用户名:密码"
            )
        username, password = line.split(":", 1)
        accounts.append({"username": username.strip(), "password": password})
    return accounts


def _parse_accounts_from_json(raw_json: str) -> list[dict[str, str]]:
    """解析 ``[{"username": ..., "password": ...}]`` 形式的 JSON 数组。"""

    try:
        payload = json.loads(raw_json)
    except ValueError as exc:
        raise ConfigError(f"账号 JSON 不是合法 JSON：{exc}") from exc
    if not isinstance(payload, list):
        raise ConfigError("账号 JSON 必须是数组")
    accounts: list[dict[str, str]] = []
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise ConfigError(f"账号 JSON 第 {index} 项不是对象")
        accounts.append(
            {
                "username": str(item.get("username", "")).strip(),
                "password": str(item.get("password", "")),
            }
        )
    return accounts


def load_config(config_path: Path | None = None) -> Config:
    """加载配置：先读 ``config.json``，再用环境变量覆盖。

    支持的环境变量（都存在时优先于配置文件）：

        配置文件路径    AGENTROUTER_CONFIG
        日志文件路径    AGENTROUTER_LOG
        账号（多行）    AGENTROUTER_ACCOUNTS
        账号（JSON）    AGENTROUTER_ACCOUNTS_JSON
        站点地址        AGENTROUTER_BASE_URL
        请求超时        AGENTROUTER_REQUEST_TIMEOUT
        时间预算        AGENTROUTER_BUDGET_SECONDS
    """

    warnings: list[str] = []
    path = config_path or Path(_env("AGENTROUTER_CONFIG") or DEFAULT_CONFIG_PATH)

    raw: dict[str, Any] = {}
    if path.exists():
        text = path.read_text(encoding="utf-8")
        try:
            loaded = json.loads(text)
        except ValueError as exc:
            raise ConfigError(f"{path} 不是合法 JSON：{exc}") from exc
        if not isinstance(loaded, dict):
            raise ConfigError(f"{path} 的顶层必须是对象")
        raw = loaded

    config = Config(config_path=path, warnings=warnings)

    # 日志路径要最先定下：下面任何一条校验抛 ConfigError，都得写进这个文件。
    config.log_path = resolve_log_path()

    # ---- 站点地址 ----
    config.base_url = (
        _env("AGENTROUTER_BASE_URL")
        or str(raw.get("base_url") or "").strip()
        or Config.base_url
    ).rstrip("/")

    # ---- 账号 ----
    accounts_json = _env("AGENTROUTER_ACCOUNTS_JSON")
    accounts_text = _env("AGENTROUTER_ACCOUNTS")
    if accounts_json:
        config.accounts = _parse_accounts_from_json(accounts_json)
    elif accounts_text:
        config.accounts = _parse_accounts_from_text(accounts_text)
    else:
        raw_accounts = raw.get("accounts")
        if raw_accounts is None:
            config.accounts = []
        elif isinstance(raw_accounts, list):
            parsed: list[dict[str, str]] = []
            for index, item in enumerate(raw_accounts, start=1):
                if not isinstance(item, dict):
                    raise ConfigError(f"accounts 第 {index} 项不是对象")
                parsed.append(
                    {
                        "username": str(item.get("username", "")).strip(),
                        "password": str(item.get("password", "")),
                    }
                )
            config.accounts = parsed
        else:
            raise ConfigError("accounts 必须是数组")

    # ---- 超时与预算 ----
    config.request_timeout = _env_int(
        "AGENTROUTER_REQUEST_TIMEOUT",
        _config_int(raw, "request_timeout", Config.request_timeout, warnings),
        warnings,
    )
    config.budget_seconds = _env_int(
        "AGENTROUTER_BUDGET_SECONDS",
        _config_int(raw, "budget_seconds", Config.budget_seconds, warnings),
        warnings,
    )

    config.request_timeout = _clamp(
        config.request_timeout, 5, 120, "request_timeout", warnings
    )
    config.budget_seconds = _clamp(
        config.budget_seconds, 30, MAX_BUDGET_SECONDS, "budget_seconds", warnings
    )

    if not config.base_url.startswith("https://"):
        raise ConfigError(f"base_url 必须使用 https://（当前为 {config.base_url!r}）")
    if not config.accounts:
        raise ConfigError(
            "未配置任何账号：请在 config.json 的 accounts 里填写，"
            "或设置 AGENTROUTER_ACCOUNTS / AGENTROUTER_ACCOUNTS_JSON"
        )
    if len(config.accounts) > MAX_ACCOUNTS:
        raise ConfigError(
            f"账号数超过上限：配了 {len(config.accounts)} 个，最多 {MAX_ACCOUNTS} 个。"
            "本工具面向个人自用，站点的使用规范不允许拿多账号批量刷额度"
        )
    for index, account in enumerate(config.accounts, start=1):
        if not account.get("username") or not account.get("password"):
            raise ConfigError(f"第 {index} 个账号缺少 username 或 password")

    return config


# ============================================================================
# 运行期辅助
# ============================================================================

class Deadline:
    """单次运行的时间预算。

    每次发请求前用 :meth:`remaining` 把超时压到剩余预算内，
    预算耗尽时 :meth:`expired` 为真，主流程如实收尾而不是被系统强杀。
    """

    def __init__(self, seconds: int):
        self._end = time.monotonic() + seconds

    def expired(self) -> bool:
        return time.monotonic() >= self._end

    def seconds_left(self) -> float:
        """剩余预算（秒），已耗尽时为负数。"""

        return self._end - time.monotonic()

    def remaining(self, cap: int) -> int:
        return max(1, min(cap, int(self.seconds_left())))


def mask_account(username: str) -> str:
    """脱敏账号，只保留前四个字符：user@example.com -> user*****

    已经脱敏过的值原样返回，所以重复调用是安全的。
    短名字不整段露出：``ab`` 只留一半，遮完是 ``a*****``。
    """

    username = str(username or "")
    if username.endswith(MASK_SUFFIX):
        return username
    keep = 4 if len(username) > 4 else len(username) // 2
    return f"{username[:keep]}{MASK_SUFFIX}"


def safe_error(error: object) -> str:
    """清理错误信息里的敏感内容。

    只替换长度 >= 4 的凭据：太短的片段参与替换会把 ``https://`` 之类的
    普通文本一起打碎，反而没法排查。
    """

    message = str(error)
    config = CONFIG_REF[0]
    secrets: list[str] = []
    if config is not None:
        secrets.extend(
            str(account.get("password", "")) for account in config.accounts
        )
    for secret in sorted(set(secrets), key=len, reverse=True):
        if len(secret) >= 4:
            message = message.replace(secret, "***")
    return message[:500]


# 主流程把当前配置登记在这里，供 safe_error 做脱敏时取用。
CONFIG_REF: list[Config | None] = [None]


def bjt_now() -> str:
    """北京时间字符串，用于日志和输出。"""

    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")


def bjt_date() -> str:
    """北京时间的日期。

    站点的签到按北京时间自然日计、每天 00:00 重置，所以「今天签过没」
    必须按北京时间判断，不能用本机时区——否则跨时区使用会判错一整天。
    """

    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")


def quota_to_usd(quota: Any, quota_per_unit: int) -> float:
    """把 quota 换算成美元，保留两位小数。无法识别时返回 0.0。"""

    try:
        return round(float(quota or 0) / quota_per_unit, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0


# ============================================================================
# 结果数据结构
# ============================================================================

@dataclass
class AccountResult:
    """单个账号的签到结果。

    account      脱敏后的用户名（构造时强制脱敏，任何路径都不可能泄露完整账号）
    checked_in   站点登录响应里的 checked_in 原始值。该字段恒为 true，
                 判断不出当天是否首次签到，仅作数据保留
    balance_usd  按 quota 折算的美元余额
    error         登录失败原因，非空即视为该账号失败
    warning       签到成功但余额查询异常时的提示，不影响成败判定
    """

    account: str
    checked_in: bool = False
    balance_usd: float = 0.0
    error: str = ""
    warning: str = ""

    def __post_init__(self) -> None:
        # 脱敏是硬约束而不是调用方自觉：谁构造它，账号都会被遮住。
        self.account = mask_account(self.account)


# ============================================================================
# HTTP 与 AgentRouter 接口
# ============================================================================

def create_session(config: Config) -> Session:
    """创建一个独立的 requests.Session。

    Session 会保存登录过程中收到的 Cookie——AgentRouter 的登录态主要靠
    Cookie 维持，所以每个账号都用自己的 Session，避免多账号串号。
    """

    session = requests.Session()
    # 保持 requests 默认的代理继承（不设 trust_env=False），这样系统层的网络
    # 方案都能直接生效，脚本本身不需要也不提供任何代理配置。
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Referer": f"{config.base_url}/login",
            "Origin": config.base_url,
        }
    )
    return session


def parse_json_response(response: Response, endpoint: str) -> dict[str, Any]:
    """检查 HTTP 响应并解析成 JSON 对象。

    顺序：先看正文里有没有 aliyun_waf（被 WAF 拦截时返回的是 HTML 挑战页），
    再看状态码，最后解析 JSON 并确认顶层是对象。
    """

    if "aliyun_waf" in response.text.lower():
        raise UpstreamError(f"{endpoint} 被阿里云 WAF 拦截", retryable=True)
    if response.status_code >= 400:
        retryable = (
            response.status_code in {403, 408, 429} or response.status_code >= 500
        )
        raise UpstreamError(
            f"{endpoint} 返回 HTTP {response.status_code}", retryable=retryable
        )
    try:
        payload = response.json()
    except ValueError as exc:
        if "aliyun_waf" in response.text.lower():
            raise UpstreamError(f"{endpoint} 被阿里云 WAF 拦截", retryable=True) from exc
        raise UpstreamError(f"{endpoint} 返回的不是 JSON", retryable=True) from exc
    if not isinstance(payload, dict):
        raise UpstreamError(f"{endpoint} 返回的 JSON 结构异常", retryable=True)
    return payload


def request_json(
    session: Session,
    method: str,
    url: str,
    endpoint: str,
    config: Config,
    deadline: Deadline,
    **kwargs: Any,
) -> dict[str, Any]:
    """发一次请求并解析 JSON，可重试的失败会再试一次。

    只重试 :func:`parse_json_response` 标成 ``retryable`` 的失败——WAF 拦截、
    5xx、响应不是 JSON 这类瞬时问题。密码错误之类的业务失败走不到这里
    （那是 HTTP 200 + ``success=false``），不会被重复提交。

    requests 自己抛的连接异常不重试：重试一次超时等于把时间预算再赔一份，
    而每天两次定时任务本身就是兜底。
    """

    attempt = 0
    while True:
        attempt += 1
        try:
            response = session.request(
                method,
                url,
                timeout=deadline.remaining(config.request_timeout),
                **kwargs,
            )
            return parse_json_response(response, endpoint)
        except UpstreamError as exc:
            # 退避还没睡完预算就见底，重试也来不及，不如如实收尾。
            no_time_left = deadline.seconds_left() <= RETRY_BACKOFF_SECONDS + 1
            if attempt >= MAX_ATTEMPTS or not exc.retryable or no_time_left:
                raise
            log.warning(
                "%s 失败（%s），%d 秒后重试",
                endpoint,
                safe_error(exc),
                RETRY_BACKOFF_SECONDS,
            )
            time.sleep(RETRY_BACKOFF_SECONDS)


def fetch_site_info(config: Config, deadline: Deadline) -> dict[str, Any]:
    """调用 ``/api/status`` 确认站点可达，并取回站点信息。

    成功返回接口的 ``data``（含 ``quota_per_unit`` 等），失败时抛
    :class:`UpstreamError` 或 requests 的异常。被 WAF 拦截时异常文本里会
    出现 ``aliyun_waf``，调用方据此区分「风控拦截」和「网络不通」。
    """

    session = create_session(config)
    try:
        payload = request_json(
            session,
            "GET",
            f"{config.base_url}/api/status",
            "/api/status",
            config,
            deadline,
        )
        if payload.get("success") is not True:
            raise UpstreamError("/api/status 返回 success != true", retryable=True)
        data = payload.get("data")
        return data if isinstance(data, dict) else {}
    finally:
        session.close()


def classify_connection_error(detail: str) -> str:
    """判断连接失败属于风控拦截（``"waf"``）还是网络不通（``"network"``）。

    两者对用户的排查动作完全不同：前者要换网络环境，后者要查断网 / DNS。

    403 也算风控：站点不说原因，但对用户来说动作和被 WAF 拦一样。这里的
    判定必须和 :func:`judge` 的 ``waf_markers`` 保持一致，否则 diagnose 和
    auto 会对同一个错误给出两种结论。
    """

    lowered = detail.lower()
    return "waf" if "waf" in lowered or "http 403" in lowered else "network"


def login_and_checkin(
    config: Config, session: Session, account: dict[str, str], deadline: Deadline
) -> tuple[dict[str, Any], str]:
    """登录账号，登录动作本身即触发当日签到。

    返回 ``(登录响应中的 data, "")``，失败返回 ``({}, 错误信息)``。
    注意：登录失败时接口同样返回 HTTP 200，靠 ``success`` 字段判断。
    """

    username = account["username"]
    try:
        payload = request_json(
            session,
            "POST",
            f"{config.base_url}/api/user/login",
            "/api/user/login",
            config,
            deadline,
            json={"username": username, "password": account["password"]},
        )
    except (requests.RequestException, UpstreamError) as exc:
        return {}, safe_error(exc)

    if payload.get("success") is not True:
        return {}, str(payload.get("message") or "登录失败")
    data = payload.get("data")
    if not isinstance(data, dict):
        return {}, "登录响应缺少 data"
    log.info("登录成功：%s", mask_account(username))
    return data, ""


def get_balance(
    config: Config,
    session: Session,
    user_data: dict[str, Any],
    quota_per_unit: int,
    deadline: Deadline,
) -> tuple[float, str]:
    """查询余额。

    当前前端只靠登录 Cookie 和 ``New-API-User`` 请求头查余额，``access_token``
    不是必需字段（旧版本会返回，返回了就一并带上）。查不到余额只记 warning，
    不会把已经完成的签到改判为失败。
    """

    user_id = user_data.get("id")
    if user_id in (None, ""):
        return 0.0, "签到成功但响应里没有用户 id，无法查询余额"

    headers = {"New-API-User": str(user_id), "Accept": "application/json"}
    access_token = user_data.get("access_token")
    if access_token:
        headers["Authorization"] = str(access_token)

    try:
        payload = request_json(
            session,
            "GET",
            f"{config.base_url}/api/user/self",
            "/api/user/self",
            config,
            deadline,
            headers=headers,
        )
    except (requests.RequestException, UpstreamError) as exc:
        return 0.0, f"余额查询失败：{safe_error(exc)}"

    if payload.get("success") is not True:
        return 0.0, "余额接口返回 success != true"
    data = payload.get("data")
    if not isinstance(data, dict):
        return 0.0, "余额接口返回的数据结构异常"
    return quota_to_usd(data.get("quota", 0), quota_per_unit), ""


def process_account(
    config: Config,
    account: dict[str, str],
    quota_per_unit: int,
    deadline: Deadline,
) -> AccountResult:
    """处理单个账号：建独立 Session → 登录签到 → 查余额。"""

    username = account["username"]
    # 不用在这里 mask：AccountResult 构造时一定会遮，那是硬约束。
    result = AccountResult(account=username)
    if deadline.expired():
        result.error = "已达时间预算，未执行"
        return result

    session = create_session(config)
    try:
        user_data, error = login_and_checkin(config, session, account, deadline)
        if error:
            result.error = error
            return result
        result.checked_in = bool(user_data.get("checked_in"))
        result.balance_usd, result.warning = get_balance(
            config, session, user_data, quota_per_unit, deadline
        )
        return result
    finally:
        session.close()


# ============================================================================
# 汇总与输出
# ============================================================================

def judge(results: list[AccountResult]) -> str:
    """把账号级结果归并成一个结果码。"""

    if not results:
        return "ERROR"
    successful = [r for r in results if not r.error]
    # 全部成功就是成功：哪怕预算刚好在最后一个账号之后耗尽，
    # 也不该把一次成功的签到报成 TIMEOUT（那会让定时任务无谓地变红）。
    #
    # 这里不区分「新签到」和「已签到」：站点每次登录都返回 checked_in=true，
    # 据此判断不出当天是不是第一次签，硬分只会得出假结论。
    if len(successful) == len(results):
        return "OK"
    if successful:
        return "PARTIAL"
    if all("时间预算" in r.error for r in results):
        return "TIMEOUT"
    auth_markers = ("用户名或密码错误", "密码错误", "用户已被封禁")
    if all(any(marker in r.error for marker in auth_markers) for r in results):
        return "AUTH_ERROR"
    # WAF 必须排在网络之前判：被风控拦下时站点本身是通的，报成 NETWORK
    # 会把人引去查断网 / DNS / 防火墙，方向完全反了——该做的是换网络出口。
    waf_markers = ("WAF", "HTTP 403")
    if all(any(marker in r.error for marker in waf_markers) for r in results):
        return "NO_EXIT"
    network_markers = (
        "Failed to establish",
        "Max retries",
        "timed out",
        "Connection",
        "ProxyError",
        "SSLError",
        "返回的不是 JSON",
        "HTTP 5",
        # WAF / 403 保留在这里：混着超时之类的失败时，NETWORK 是个合适的统称。
        "HTTP 403",
        "HTTP 429",
        "WAF",
    )
    if all(any(marker in r.error for marker in network_markers) for r in results):
        return "NETWORK"
    return "ERROR"


def build_report(results: list[AccountResult], result_code: str) -> str:
    """生成一句人话汇报（对应 JSON 里的 report 字段）。"""

    successful = [r for r in results if not r.error]
    total_balance = sum(r.balance_usd for r in successful)

    if result_code == "OK":
        return (
            f"签到成功 {len(successful)} 个账号，总余额 ${total_balance:,.2f}"
        )
    if result_code == "PARTIAL":
        failed = [r for r in results if r.error]
        first = failed[0]
        return (
            f"{len(results)} 个账号中 {len(successful)} 个成功，"
            f"总余额 ${total_balance:,.2f}；"
            f"{first.account} 失败：{first.error[:120]}"
        )
    if result_code == "AUTH_ERROR":
        first = results[0]
        return f"登录失败：{first.error[:160]}"
    if result_code == "NO_EXIT":
        # 覆盖两种情形：明确的 WAF 挑战页，和光秃秃的 403。后者站点不说原因，
        # 但对用户来说动作一样——换个网络出口，而不是去查断网。
        return "被站点风控拦截，签到未执行：当前出口 IP 被拦，换个网络环境再试"
    if result_code == "NETWORK":
        return "网络不可达：无法连接站点，签到未执行"
    if result_code == "TIMEOUT":
        # 只要有账号成功，judge() 就归成 PARTIAL，所以走到这里必然是 0 个成功。
        return "已达本次运行时间预算，没有账号完成签到，等下次定时任务重试"
    if result_code == "CONFIG_ERROR":
        return "配置错误，请检查 config.json 或环境变量"
    first = results[0] if results else None
    detail = f"：{first.error[:160]}" if first and first.error else ""
    return f"脚本运行异常{detail}"


def build_payload(
    config: Config,
    results: list[AccountResult],
    result_code: str,
) -> dict[str, Any]:
    """组装最终输出：一行 JSON。"""

    payload: dict[str, Any] = {
        "time": bjt_now(),
        "result": result_code,
        "report": build_report(results, result_code),
    }
    if results:
        successful = [r for r in results if not r.error]
        payload["accounts"] = [asdict(r) for r in results]
        # 套一层 float：全失败时 sum([]) 是 int 0，会让这个字段在 JSON 里
        # 时而整数时而小数，下游解析平白多一种情况要处理。
        payload["total_balance_usd"] = round(
            float(sum(r.balance_usd for r in successful)), 2
        )
    if config.warnings:
        payload["config_warning"] = config.warnings
    return payload


def emit(config: Config, payload: dict[str, Any], silent: bool) -> None:
    """输出结果：auto 打到 stdout，silent 追加进日志文件。"""

    line = json.dumps(payload, ensure_ascii=False)
    if not silent:
        print(line, flush=True)
        return
    try:
        # 自定义日志路径指向还不存在的目录时，先建出来，别让整条记录白丢。
        config.log_path.parent.mkdir(parents=True, exist_ok=True)
        with config.log_path.open("a", encoding="utf-8") as handle:
            handle.write(f"[{payload.get('time', bjt_now())}] {line}\n")
    except OSError as exc:
        print(f"写入日志文件失败：{exc}", file=sys.stderr)


# ============================================================================
# 子命令
# ============================================================================

def run_checkin(config: Config, silent: bool) -> int:
    """auto / silent 的主流程。

    silent（定时任务）会读写状态文件：当天已经签成过就直接跳过，连站点都不碰；
    只有还没成功时才真正去登录。这样定时任务可以放心地每隔一段时间跑一次，
    失败自动重试，成功后当天剩下的运行全是空转——站点每天只被登录一次。

    auto（手动）不看状态、也不写状态：你手动敲了就是要它跑。
    """

    # 两个都无条件先算出来：下面的收尾逻辑要用到，只在 silent 分支里定义的话，
    # 收尾处一旦有人把判断条件改掉，就会踩 NameError。多算一次没有代价。
    today = bjt_date()
    state_path = resolve_state_path()

    if silent and read_done_date(state_path) == today:
        log.info("今天已签到成功，跳过本次运行")
        return 0

    deadline = Deadline(config.budget_seconds)

    log.info("检查站点可达性：%s", config.base_url)
    try:
        site_info = fetch_site_info(config, deadline)
    except (requests.RequestException, UpstreamError) as exc:
        detail = safe_error(exc)
        failure = classify_connection_error(detail)
        if failure == "waf":
            log.error(
                "被站点风控拦截：当前出口 IP 被拦（WAF 挑战页或 403），"
                "换个网络环境再试。"
            )
            result_code = "NO_EXIT"
            reason = "被站点风控拦截，当前出口 IP 被拦"
        else:
            log.error("无法连接站点：%s", detail)
            result_code = "NETWORK"
            reason = f"网络不可达，无法连接站点：{detail[:120]}"

        results = [
            AccountResult(account=account["username"], error=reason)
            for account in config.accounts
        ]
        emit(config, build_payload(config, results, result_code), silent)
        # 站点没连上属于可自愈的临时故障，不写状态，留给下次运行重试。
        return 2

    quota_per_unit = site_info.get("quota_per_unit")
    try:
        quota_per_unit = int(quota_per_unit)
        if quota_per_unit <= 0:
            raise ValueError
    except (TypeError, ValueError):
        quota_per_unit = FALLBACK_QUOTA_PER_UNIT

    log.info("站点可达，开始签到，共 %d 个账号", len(config.accounts))

    results: list[AccountResult] = []
    for index, account in enumerate(config.accounts):
        # 账号之间隔一下：一串登录请求连着打过去，容易被站点风控当成异常流量。
        if index and not deadline.expired():
            time.sleep(ACCOUNT_INTERVAL_SECONDS)
        results.append(
            process_account(config, account, quota_per_unit, deadline)
        )

    timed_out = deadline.expired()
    if timed_out:
        log.warning("时间预算已用尽，部分账号可能未处理")

    result_code = judge(results)

    payload = build_payload(config, results, result_code)
    emit(config, payload, silent)
    log.info("完成：%s", payload["report"])

    if silent and result_code in TERMINAL_RESULTS:
        mark_done(state_path, today, result_code)

    if result_code == "OK":
        return 0
    if result_code == "PARTIAL":
        return 1
    return 2


def run_diagnose(config: Config, silent: bool) -> int:
    """diagnose：只确认站点可达，不登录任何账号。

    用来区分「站点被 WAF 拦」和「本机网络不通」——这两种情况的处理方式
    完全不同，但终端里都只看到一句「连不上」。
    """

    deadline = Deadline(config.budget_seconds)
    log.info("探测 %s/api/status", config.base_url)

    ok = False
    detail = ""
    failure_kind = ""
    data: dict[str, Any] = {}
    try:
        data = fetch_site_info(config, deadline)
        ok = True
    except (requests.RequestException, UpstreamError) as exc:
        detail = safe_error(exc)
        failure_kind = classify_connection_error(detail)

    if ok:
        print(f"OK   站点可达（{config.base_url}）")
        if data.get("system_name"):
            print(f"     站点名称：{data['system_name']}")
        if data.get("quota_per_unit"):
            print(f"     换算单位：{data['quota_per_unit']} quota = 1 美元")
    else:
        print(f"FAIL 无法访问 {config.base_url}")
        print(f"     {detail}")
        if failure_kind == "waf":
            print("     这是站点风控拦截（WAF 挑战页或 403），不是断网：换个网络环境再试。")

    # result 要跟 failure_kind 一致：以前这里恒为 NO_EXIT，网络不通也报成
    # 「被 WAF 拦」，同一行 JSON 里两个字段互相打脸。
    if ok:
        result_code = "OK"
    elif failure_kind == "waf":
        result_code = "NO_EXIT"
    else:
        result_code = "NETWORK"

    payload = {
        "time": bjt_now(),
        "result": result_code,
        "report": (
            f"站点可达（{data.get('system_name') or config.base_url}）"
            if ok
            else f"站点不可达：{detail[:160]}"
        ),
        "reachable": ok,
    }
    if not ok:
        payload["failure_kind"] = failure_kind
    if config.warnings:
        payload["config_warning"] = config.warnings
    emit(config, payload, silent)
    return 0 if ok else 2


# ============================================================================
# 入口
# ============================================================================

def usage() -> str:
    return (
        "用法：python signin.py [auto|silent|diagnose]\n"
        "  auto      立刻签到 + 查余额，结果打到 stdout（默认，手动用）\n"
        "  silent    给定时任务用：当天已签成过就跳过，否则签到并写入日志文件\n"
        "  diagnose  只确认站点是否可达，不登录任何账号\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv

    # Windows 控制台/重定向场景的编码是 GBK，个别字符打印会直接崩；
    # 统一按 UTF-8 输出（pythonw 下 stream 为 None，跳过即可）。
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass

    if args and args[0] in ("-h", "--help", "help"):
        print(usage())
        return 0

    command = args[0] if args else "auto"
    if command not in ("auto", "silent", "diagnose"):
        print(f"未知命令：{command}\n\n{usage()}", file=sys.stderr)
        return 2

    # Windows 下用 pythonw.exe 静默运行时 sys.stderr 为 None，此时不能挂控制台
    # 日志处理器，否则每条日志都会触发内部的 write 异常。直接关掉日志即可——
    # 结果仍然会通过 emit() 写进日志文件，不会丢。
    if sys.stderr is not None:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            stream=sys.stderr,
        )
        for handler in logging.getLogger().handlers:
            handler.setFormatter(
                BeijingLogFormatter("%(asctime)s [%(levelname)s] %(message)s")
            )
    else:
        logging.disable(logging.CRITICAL)

    silent = command == "silent"
    config: Config | None = None
    try:
        config = load_config()
        CONFIG_REF[0] = config
        if command == "diagnose":
            return run_diagnose(config, silent)
        return run_checkin(config, silent)
    except ConfigError as exc:
        log.error("配置错误：%s", exc)
        # load_config 可能在定下 log_path 之前就抛了，这里自己再解析一次：
        # 配置报错必须写进用户真正在看的那个日志文件。
        fallback = config or Config(log_path=resolve_log_path())
        payload = {
            "time": bjt_now(),
            "result": "CONFIG_ERROR",
            "report": f"配置错误：{exc}",
            "hint": "请参考 config.example.json 创建 config.json",
        }
        emit(fallback, payload, silent)
        return 2
    except Exception as exc:  # 兜底：异常绝不静默丢失
        detail = safe_error(exc)
        log.error("脚本运行异常：%s", detail)
        fallback = config or Config(log_path=resolve_log_path())
        payload = {
            "time": bjt_now(),
            "result": "ERROR",
            "report": f"脚本运行异常：{detail}",
            "error_type": type(exc).__name__,
        }
        emit(fallback, payload, silent)
        return 2


if __name__ == "__main__":
    sys.exit(main())
