"""LLM 客户端封装:超时 + 重试(指数退避 + 抖动) + 错误分类。

为什么不用 SDK 自带重试?
    自带重试是黑盒:你不知道它重试了几次、为什么重试、下次什么间隔。
    自己写一遍,「几次、什么退避曲线、哪些错误该重试」就变成显式可控的。
    这件事在 Java 里你早做过(Spring Retry / Resilience4j),这里是同一件事的 Python 版。

C4 要求:所有外部调用必须有显式超时、重试策略、失败降级路径。
C5 要求:任何循环必须有界 —— 这里的界是 max_retries。
"""

import random
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from openai import APIConnectionError, APIStatusError, OpenAI

from .config import Pricing, Settings


class ErrorClass(str, Enum):
    """错误分类:决定失败之后走哪条路。

    这是「生产级」和「demo」的分界之一 —— demo 直接把异常抛给用户,
    生产代码要先判断这个错是「等一下再试」「换凭据」「去充值」还是「改代码」。
    """

    RETRYABLE = "retryable"      # 网络抖动 / 限流 / 服务端 5xx -> 退避重试
    AUTH = "auth"                # 401 / 403 -> 凭据问题,重试无意义,需人工
    QUOTA = "quota"              # 402 -> 余额不足,需人工充值
    BAD_REQUEST = "bad_request"  # 4xx 参数错误 -> 改代码,重试无意义
    UNKNOWN = "unknown"          # 未归类,保守起见不重试


# 这些 HTTP 状态码重试有意义(服务端瞬时问题或限流)
RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """本项目统一的 LLM 异常。携带分类,让上层能做决策而不是只能打印堆栈。"""

    def __init__(self, error_class: ErrorClass, message: str, attempts: int) -> None:
        super().__init__(message)
        self.error_class = error_class
        self.attempts = attempts


def classify(exc: Exception) -> ErrorClass:
    """把一个异常映射到 ErrorClass。

    先判断连接/超时类(它们不是 APIStatusError),再按 HTTP 状态码分。
    APITimeoutError 是 APIConnectionError 的子类,一起处理即可。
    """
    if isinstance(exc, APIConnectionError):
        return ErrorClass.RETRYABLE
    if isinstance(exc, APIStatusError):
        code = exc.status_code
        if code in (401, 403):
            return ErrorClass.AUTH
        if code == 402:
            return ErrorClass.QUOTA
        if code in RETRYABLE_STATUS:
            return ErrorClass.RETRYABLE
        if 400 <= code < 500:
            return ErrorClass.BAD_REQUEST
        return ErrorClass.UNKNOWN
    return ErrorClass.UNKNOWN


def backoff_seconds(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    """指数退避 + 抖动。

    attempt 从 1 开始:1s, 2s, 4s, 8s...(封顶 cap),各乘一个 0.5~1.0 的随机因子。
    抖动(jitter)的作用:多个客户端同时被限流时,避免它们在同一毫秒一起重试把服务端再打挂。
    """
    exponential = min(cap, base * (2 ** (attempt - 1)))
    return exponential * random.uniform(0.5, 1.0)


def _extract_cached_tokens(usage: Any) -> int:
    """兼容读取「缓存命中的输入 token 数」。

    不同厂商字段名不一致(DeepSeek 与 OpenAI 就不同),做容错读取,
    读不到就返回 0 —— 成本估算少算一点,但绝不因此报错。
    """
    direct = getattr(usage, "prompt_cache_hit_tokens", None)
    if isinstance(direct, int):
        return direct
    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        nested = getattr(details, "cached_tokens", None)
        if isinstance(nested, int):
            return nested
    return 0


@dataclass
class LLMResponse:
    """一次成功调用的结果 + 观测数据。"""

    text: str
    model: str
    prompt_tokens: int
    cached_tokens: int
    completion_tokens: int
    attempts: int
    latency_seconds: float
    cost_cny: float


class LLMClient:
    """最小可用的 LLM 客户端。Week 1 只有一个 chat() 方法。"""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pricing: Pricing = settings.pricing
        # max_retries=0:关掉 SDK 自带重试,全部由我们自己的循环控制
        self._client = OpenAI(
            api_key=settings.api_key,
            base_url=settings.base_url,
            timeout=settings.timeout_seconds,
            max_retries=0,
        )

    def chat(
        self,
        prompt: str,
        system: str | None = None,
        thinking: bool = False,
    ) -> LLMResponse:
        """发一条消息,拿回文本。

        thinking=False 会显式关闭思考模式:更快、更便宜,且让 temperature 生效。
        Week 3 学 Prompt 工程做对比实验时需要 temperature 可控,所以这里默认关掉。
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        extra_body: dict[str, Any] = {}
        if not thinking:
            extra_body["thinking"] = {"type": "disabled"}

        max_attempts = self._settings.max_retries + 1
        last_error: Exception | None = None

        for attempt in range(1, max_attempts + 1):
            started = time.perf_counter()
            try:
                response = self._client.chat.completions.create(
                    model=self._settings.model,
                    messages=messages,
                    extra_body=extra_body or None,
                )
            except Exception as exc:  # noqa: BLE001 —— 这里就是要按分类处理所有异常
                klass = classify(exc)
                last_error = exc
                if klass is not ErrorClass.RETRYABLE or attempt >= max_attempts:
                    raise LLMError(klass, str(exc), attempt) from exc
                wait = backoff_seconds(attempt)
                print(
                    f"[重试] 第 {attempt}/{max_attempts} 次失败"
                    f"(分类={klass.value}),{wait:.1f}s 后重试"
                )
                time.sleep(wait)
                continue

            latency = time.perf_counter() - started
            usage = response.usage
            prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
            completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
            cached_tokens = _extract_cached_tokens(usage)
            cache_miss_tokens = max(0, prompt_tokens - cached_tokens)
            cost = self._pricing.estimate(cached_tokens, cache_miss_tokens, completion_tokens)

            content = response.choices[0].message.content or ""
            return LLMResponse(
                text=content,
                model=str(getattr(response, "model", self._settings.model)),
                prompt_tokens=prompt_tokens,
                cached_tokens=cached_tokens,
                completion_tokens=completion_tokens,
                attempts=attempt,
                latency_seconds=latency,
                cost_cny=cost,
            )

        # 理论上不可达:循环内要么 return 要么 raise
        raise LLMError(ErrorClass.UNKNOWN, f"耗尽重试仍未成功: {last_error}", max_attempts)
