# ai-python — Week 1:最小 LLM 调用

Java 高工转 AI 应用的第一天产出。目标不是「调通一次 API」,而是**第一天就建立生产级习惯**:
超时、重试、错误分类、成本可见、凭据不落代码。

## 这一周的逻辑

```
你的代码 ──► LLMClient ──► DeepSeek API ──► 文本 + 用量
                │
                ├─ 超时(60s)           ← 外部调用不能无限等
                ├─ 重试(最多 3 次)      ← 指数退避 + 抖动
                ├─ 错误分类             ← 决定该重试 / 换 key / 充值 / 改代码
                └─ 成本估算             ← 每次调用花多少钱,立刻看见
```

这四件事你在 Java 里都做过(超时配置、Spring Retry、异常分类、APM 埋点)。
**LLM 应用的工程底座和你熟悉的后端工程是同一套东西**,区别只在业务对象变成了「不确定的模型输出」。

## 环境

| 项 | 值 |
|---|---|
| 机器 | macOS 13.7.8 / Intel i7(够用:全程调云端 API,CPU 不是瓶颈) |
| Python | 3.13.12 |
| 虚拟环境 | `.venv/`(已创建) |
| 编辑器 | VSCode |

## 快速开始

**1. 激活虚拟环境**(每次开新终端都要做)

```bash
cd /Users/apple/gitproject/ai-python
source .venv/bin/activate
```

**2. 配置 API key**

```bash
cp .env.example .env
# 然后编辑 .env,把 DEEPSEEK_API_KEY 换成真实 key
```

key 在 https://platform.deepseek.com/api_keys 申请。
`.env` 已在 `.gitignore` 里,**不会进版本库、不会被打进日志**。

**3. 先跑自检**(不需要 key、不需要联网)

```bash
python -m src.hello_llm --selftest
```

期望输出:

```
自检通过:成本计算 / 退避曲线 / 错误分类 / 配置校验 四项均符合预期
```

**4. 真实调用一次**

```bash
python -m src.hello_llm
```

期望输出(节选):

```
模型=deepseek-flash  超时=60.0s  最大重试=3
提问: 用一句话说明:什么是大语言模型的 token?

回答:
...

--- 观测数据 ---
耗时       : 1.83s
尝试次数   : 1
输入 tokens: 41(其中缓存命中 0)
输出 tokens: 78
本次成本   : ¥0.000353
```

## 文件说明

| 文件 | 作用 |
|---|---|
| `src/config.py` | 配置装配。凭据只从环境变量读,不硬编码 |
| `src/llm_client.py` | 核心:超时 / 重试 / 错误分类 / 成本估算 |
| `src/hello_llm.py` | 入口。`--selftest` 本地自检,默认真实调用 |
| `.env.example` | 配置模板(复制为 `.env` 使用) |

## 成本参考

模型 `deepseek-flash`,空闲时段价(元/百万 token,核实于 2026-10-14 官方定价页):

| 项 | 空闲时段 | 高峰时段 |
|---|---|---|
| 输入(缓存命中) | 0.02 | 0.04 |
| 输入(缓存未命中) | 1.0 | 2.0 |
| 输出 | 4.0 | 8.0 |

**高峰时段** = 周一至周五 9:00–12:00、14:00–18:00(北京时间,不含法定节假日)。
**其余时间(含晚上和周末)= 空闲时段,价格直接减半。**

> 你晚上和周末学习,天然就在半价时段。
> 按每周约 200 次调用估算,三个月 API 成本在 **¥20 以内**。

价格会变,以 https://api-docs.deepseek.com/zh-cn/quick_start/pricing 为准。
改 `.env` 里的 `PRICE_*` 就能同步你的成本估算。

## 本机网络备忘

- PyPI 直连不稳定(`files.pythonhosted.org` 常超时),**装包请加镜像源**:

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <包名>
```

- 已验证可达的镜像:清华、阿里云、腾讯云
- 装不了的:`astral.sh`(所以没用 uv,走的 venv + pip)

## 下一步(Week 2)

- 加多轮对话(消息历史怎么维护、什么时候该截断)
- 加流式输出(stream=True,体验差异在哪)
- 理解 token 与上下文窗口的实际边界

## 待确认

- [ ] VSCode 里 Python 解释器是否指向 `.venv/bin/python`(右下角查看)
- [ ] `.env` 是否已填真实 key
