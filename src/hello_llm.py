"""Week 1 竖切片:最小可运行的 LLM 调用链路。

跑通它意味着这条链路是通的:
    你的代码 -> DeepSeek API -> 返回文本 -> 打印 + 成本

用法:
    python -m src.hello_llm                 # 用默认问题调一次
    python -m src.hello_llm -p "你的问题"    # 自定义问题
    python -m src.hello_llm --selftest      # 自检:不联网、不需要 key,验证代码骨架
"""

import argparse
import sys

from .config import Pricing, Settings
from .llm_client import ErrorClass, LLMClient, LLMError, backoff_seconds, classify

DEFAULT_PROMPT = "用一句话说明:什么是大语言模型的 token?"

SYSTEM_PROMPT = "你是一个简洁的技术助手,回答控制在三句话以内,不要客套。"


def run_selftest() -> int:
    """不联网、不需要 API key,验证纯逻辑部分是否符合预期。

    这是「竖切片」思路的延伸:先证明零件是对的,再把它们接上外部服务。
    """
    failures: list[str] = []

    # 1) 成本计算
    pricing = Pricing(input_cache_hit=0.02, input_cache_miss=1.0, output=4.0)
    cost = pricing.estimate(cache_hit_tokens=0, cache_miss_tokens=1_000_000, output_tokens=0)
    if abs(cost - 1.0) > 1e-9:
        failures.append(f"成本计算错误:100万未命中输入应为 1.0 元,实际 {cost}")
    cost_mixed = pricing.estimate(cache_hit_tokens=500_000, cache_miss_tokens=500_000, output_tokens=1_000_000)
    expected_mixed = 500_000 / 1_000_000 * 0.02 + 500_000 / 1_000_000 * 1.0 + 1_000_000 / 1_000_000 * 4.0
    if abs(cost_mixed - expected_mixed) > 1e-9:
        failures.append(f"混合成本计算错误:期望 {expected_mixed},实际 {cost_mixed}")

    # 2) 退避曲线:单调不降 + 封顶
    samples = [backoff_seconds(i) for i in range(1, 8)]
    if any(samples[i] > samples[i + 1] + 30 for i in range(len(samples) - 1)):
        failures.append(f"退避曲线异常: {samples}")
    if max(samples) > 30.0:
        failures.append(f"退避未封顶在 30s: 最大值 {max(samples)}")

    # 3) 错误分类:非 openai 异常归为 unknown(保守不重试)
    if classify(ValueError("普通错误")) is not ErrorClass.UNKNOWN:
        failures.append("普通异常应归类为 unknown")

    # 4) 配置校验:缺 key 必须报错,而不是带着空 key 去调 API
    import os

    saved = os.environ.pop("DEEPSEEK_API_KEY", None)
    try:
        Settings.from_env()
        failures.append("缺少 DEEPSEEK_API_KEY 时应当抛错,但没有")
    except RuntimeError:
        pass
    finally:
        if saved is not None:
            os.environ["DEEPSEEK_API_KEY"] = saved

    if failures:
        print("自检未通过:")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("自检通过:成本计算 / 退避曲线 / 错误分类 / 配置校验 四项均符合预期")
    return 0


def run_once(prompt: str) -> int:
    """真实调用一次 API,打印回答与观测数据。"""
    settings = Settings.from_env()
    client = LLMClient(settings)

    print(f"模型={settings.model}  超时={settings.timeout_seconds}s  最大重试={settings.max_retries}")
    print(f"提问: {prompt}\n")

    try:
        response = client.chat(prompt, system=SYSTEM_PROMPT)
    except LLMError as exc:
        # 按错误分类给出「下一步该干什么」,而不是甩一个堆栈
        guidance = {
            ErrorClass.AUTH: "凭据无效。检查 .env 里的 DEEPSEEK_API_KEY 是否正确、是否已过期。",
            ErrorClass.QUOTA: "余额不足。去 https://platform.deepseek.com 充值。",
            ErrorClass.BAD_REQUEST: "请求参数错误。检查模型名和参数,重试无意义。",
            ErrorClass.RETRYABLE: "多次重试后仍未成功,可能是网络或服务端问题,稍后再试。",
            ErrorClass.UNKNOWN: "未归类的错误,先看下面的原始信息。",
        }[exc.error_class]
        print(f"[失败] 分类={exc.error_class.value}  尝试次数={exc.attempts}")
        print(f"[建议] {guidance}")
        print(f"[原始] {exc}")
        return 1

    print("回答:")
    print(response.text)
    print()
    print("--- 观测数据 ---")
    print(f"耗时       : {response.latency_seconds:.2f}s")
    print(f"尝试次数   : {response.attempts}")
    print(f"输入 tokens: {response.prompt_tokens}(其中缓存命中 {response.cached_tokens})")
    print(f"输出 tokens: {response.completion_tokens}")
    print(f"本次成本   : ¥{response.cost_cny:.6f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Week 1:最小 LLM 调用")
    parser.add_argument("-p", "--prompt", default=DEFAULT_PROMPT, help="要提问的内容")
    parser.add_argument("--selftest", action="store_true", help="本地自检,不联网、不需要 API key")
    args = parser.parse_args(argv)

    if args.selftest:
        return run_selftest()
    return run_once(args.prompt)


if __name__ == "__main__":
    sys.exit(main())
