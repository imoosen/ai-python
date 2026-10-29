# Week 1 交付概览 · 最小 LLM 调用链路

> 日期:2026-10-14 · 项目:`/Users/apple/gitproject/ai-python`

## 做了什么

在 macOS + VSCode 环境下,搭好 Python AI 应用的第一条完整链路:配置装配 → LLM 客户端 → 真实调用 → 观测数据。

**关键取向:第一天就按生产级标准写,而不是写 demo。**

## 交付内容

| 文件 | 作用 |
|---|---|
| `src/config.py` | 配置装配,凭据只从环境变量读 |
| `src/llm_client.py` | 超时 / 重试(指数退避+抖动)/ 错误分类 / 成本估算 |
| `src/hello_llm.py` | 入口,含不联网的 `--selftest` 自检 |
| `.env` / `.env.example` | 配置模板(已建 `.env`,待填 key) |
| `requirements.txt` | 15 个依赖,版本已锁定 |
| `.vscode/` | 解释器指向 + 两个调试配置 + 推荐扩展 |
| `README.md` | 完整启动与验证说明 |

## 关键决策与依据

| 决策 | 依据 |
|---|---|
| 走 venv + pip,**不用 uv** | `astral.sh` 在本机网络不可达(已实测),uv 装不上 |
| 用清华镜像装包 | PyPI 直连的 `files.pythonhosted.org` 反复超时;清华/阿里/腾讯实测 200 |
| Python 3.13.12 | 本机系统 Python 是 3.9.9,低于 openai SDK 要求的 ≥3.10 |
| 默认模型 `deepseek-flash` | 核实于 2026-10-14 官方文档(旧的 `deepseek-chat` 名已下线) |
| 默认关闭思考模式 | 更快更便宜,且让 `temperature` 生效(Week 3 对比实验需要) |

## 验证结果(均已实际执行)

| 验证项 | 结果 |
|---|---|
| 本地自检(成本/退避/分类/配置) | ✅ 四项通过 |
| 缺 API key 时的报错提示 | ✅ 提示清晰并给出修复方式 |
| SDK 参数签名正确性 | ✅ 客户端构造 + 请求发出成功 |
| 401 错误分类 | ✅ 归为 `auth`,且 `attempts=1`(不重试) |
| `api.deepseek.com` 可达性 | ✅ 401 为真实服务端响应 |

## 成本实测口径

`deepseek-flash` 空闲时段:输入未命中 ¥1/百万 token,输出 ¥4/百万 token。
单次问答约 ¥0.0004。**按每周 200 次调用估算,三个月 API 成本在 ¥20 以内**——远低于预算上限 ¥150。

> 高峰时段(工作日 9:00–12:00 / 14:00–18:00)价格翻倍。你晚上和周末学,天然半价。

## 需要你做的两件事

1. 编辑 `/Users/apple/gitproject/ai-python/.env`,把 `DEEPSEEK_API_KEY` 填成真实 key
2. 跑通这两条命令:

```bash
cd /Users/apple/gitproject/ai-python
source .venv/bin/activate
python -m src.hello_llm --selftest    # 应输出"自检通过"
python -m src.hello_llm               # 应打印回答 + 耗时 + token + 成本
```

## 本机环境备忘(影响后续 12 周)

- 这台是 **A1708**(i7-7660U / Ventura 13.7.8 / Intel)。做应用开发够用,但 **Docker 已不支持 macOS 13**——后续若需容器,得换机或改用云端。
- `astral.sh`(uv)、国内部分镜像被网络策略拦截;装包统一走清华源(venv 内已配好)。
- Homebrew 版本为 3.3.9(2022 年),若后续需要 brew 装东西,先评估升级成本(i7 双核编译很慢)。

## 下一步(Week 2 预览)

- 多轮对话:消息历史怎么维护、什么时候该截断
- 流式输出:`stream=True`,体验与实现的差异
- token 与上下文窗口的实际边界
