"""集中配置:所有可变项从环境变量读取,凭据绝不硬编码(C6)。

Java 类比:相当于 @ConfigurationProperties 绑定的一个不可变 POJO,
区别是这里没有 Spring 容器,由 from_env() 显式装配。
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# 读取项目根目录的 .env,已存在的真实环境变量优先级更高(load_dotenv 不覆盖)
load_dotenv()


@dataclass(frozen=True)
class Pricing:
    """每百万 token 的人民币单价,仅用于本地成本估算。"""

    input_cache_hit: float
    input_cache_miss: float
    output: float

    def estimate(self, cache_hit_tokens: int, cache_miss_tokens: int, output_tokens: int) -> float:
        """按真实用量估算单次调用成本(元)。

        缓存命中的输入按低价计,未命中的按高价计 —— 这是 DeepSeek 的计费方式,
        也是「把稳定不变的前缀放在 prompt 前面」能省钱的原理。
        """
        return (
            cache_hit_tokens / 1_000_000 * self.input_cache_hit
            + cache_miss_tokens / 1_000_000 * self.input_cache_miss
            + output_tokens / 1_000_000 * self.output
        )


@dataclass(frozen=True)
class Settings:
    """运行期配置。frozen=True 表示装配后不可改,避免运行中被意外改写。"""

    api_key: str
    base_url: str
    model: str
    timeout_seconds: float
    max_retries: int
    pricing: Pricing

    @classmethod
    def from_env(cls) -> "Settings":
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "缺少环境变量 DEEPSEEK_API_KEY。\n"
                "修复方式:复制 .env.example 为 .env,填入你在 "
                "https://platform.deepseek.com/api_keys 申请的 key。"
            )
        if api_key.startswith("sk-在这里填"):
            raise RuntimeError(
                "DEEPSEEK_API_KEY 还是 .env.example 里的占位值,请填入真实 key。"
            )

        return cls(
            api_key=api_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip(),
            timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            pricing=Pricing(
                input_cache_hit=float(os.getenv("PRICE_INPUT_CACHE_HIT", "0.02")),
                input_cache_miss=float(os.getenv("PRICE_INPUT_CACHE_MISS", "1.0")),
                output=float(os.getenv("PRICE_OUTPUT", "4.0")),
            ),
        )
