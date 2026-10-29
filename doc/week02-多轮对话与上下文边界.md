# Week 2:多轮对话、历史管理与上下文边界

> 前提:Week 1 已跑通(自检通过 + 真实调用返回)。你项目里的代码是你的教材,不是答案。
> **本讲义不含练习答案。** 卡住了把报错贴给我,我按错误类型定位。

---

## 0. 这一周只学一件事

> **LLM API 是无状态的。它不记得你上一句说了什么。**

你在 Week 1 写的 `chat()` 每次只发一条 user 消息。所以你在终端里连问两次,第二次它完全不知道第一次的存在——**这不是 bug,这是 API 的设计**。

所谓"多轮对话",本质是:**你每一轮都把之前所有的消息重新发一遍。**

### Java 类比

| 你以为的 | 实际上的 |
|---|---|
| 像 `HttpSession`,服务端帮你存上下文 | 像**无状态 REST 接口**:客户端必须每次带全量数据 |
| 像数据库连接上的会话状态 | 像每次请求都传完整参数的 service 方法 |

所以 Week 2 的全部工程量,都花在**"历史怎么存、怎么发、什么时候砍"** 这三件事上。这也是为什么 AI 应用里上下文管理是核心技能——不是"调 API"难,是**上下文工程**难。

---

## 1. 三个必须答上的问题

### 问题 1:历史存在哪?

**答:存在你自己的进程里。**

API 侧不提供任何存储。你要自己维护一个 `list`,每轮往里追加两条(一条 user、一条 assistant)。

Java 里的 `List<Map<String, String>>`,Python 里就是 `list[dict[str, str]]` —— **不用先定义 DTO 类,字面量直接写**。这是 Python 和 Java 最大的手感差异,也是危险所在(见第 4 节的坑)。

### 问题 2:什么时候砍历史?

**答:上下文窗口是硬上限,而且成本随轮数超线性增长。**

关键洞察:因为**每轮都重发全历史**,所以第 N 轮的输入量 ≈ 前 N-1 轮所有 token 之和。

| 轮次 | 本轮输入 tokens ≈ | 说明 |
|---|---|---|
| 1 | 提问 + system | 基线 |
| 2 | 第 1 轮的(输入 + 输出)+ 新提问 | **第 1 轮的回答也变成输入了** |
| 3 | 第 1 轮 + 第 2 轮 + 新提问 | 继续叠加 |
| 10 | 前 9 轮全部 | 已经涨了好几倍 |

**这就是"为什么长对话越来越贵、越来越慢"的算术原因。** 费用不是线性涨,是平方级涨。

砍法(Week 2 先实现最简单的一种):
- `system` 消息**永远保留**(它是行为约束,丢了模型就变性格)
- 保留**最近 N 轮**,更早的丢掉
- 进阶(Week 6 再学):不是丢,是**摘要压缩**——把老历史让模型总结成一段话

### 问题 3:token 到底怎么算的?

**答:看 `usage` 字段,别自己估。**

这是 Week 2 最值钱的一个验证点。它能把上面那个抽象洞察变成**可测量的预测**:

```
预测:第 2 轮的 input_tokens ≈ 第 1 轮的 input_tokens + 第 1 轮的 output_tokens + 第 2 轮提问的 token
验证:跑两轮,对比 hello_llm 打印的"输入 tokens"
```

**对不上就说明你没理解。对上了,说明"每次重发全历史"这件事你真的懂了。** 这比背十遍概念有用。

---

## 2. 动手练习(按顺序做,改代码不是读代码)

### 练习 A:把 Week 1 收尾(10 分钟,必做)

> 我已帮你把 `.env` 里的 key 填好(从你 aicodeswitch 配置里取的),链路实测已通:
> 自检 4 项通过、真实调用 1.39s、成本 ¥0.000103。

1. 跑一遍 `python -m src.hello_llm`,确认你也能跑通
2. **Week 1 遗留的练习 1**:改掉 `DEFAULT_PROMPT`,观察 `输入 tokens` 怎么随问题长度变
3. **Week 1 遗留的练习 2**:给命令行加 `--temperature` 参数

**练习 2 有个隐藏考点**:DeepSeek 的**思考模式开着时 `temperature` 不生效**。现在代码里 `thinking=False`(已关),所以 temperature 生效。把 `thinking` 打开再试,你会发现 temperature 失效——这就是 Week 3 做 Prompt 对比实验必须先关思考模式的原因。

### 练习 B:让 `chat()` 支持历史(30 分钟,本周核心)

目标:改造 `src/llm_client.py` 的 `chat()`,让它能接收并发送历史。

**只需改 3 处:**

```python
# 1) 签名:加一个 history 参数
def chat(self, prompt, system=None, thinking=False, history=None):
    #                                                       ^^^^^^^ 默认值用 None,不要用 []

# 2) 组装 messages:system 在最前,然后是历史,最后是新提问
#    (现在代码里只有 system + prompt 两条,你要把 history 插进去)

# 3) 返回值:不用改
```

**这里有一个 Python 经典坑,而且是你一定会踩的那种:**

```python
# ❌ 错:默认值是可变对象
def chat(self, history=[]):
    history.append(...)   # 这个 [] 在函数定义时只创建一次,被所有调用共享!

# ✅ 对:用 None 当哨兵
def chat(self, history=None):
    history = history or []
```

Java 里没有这个问题(Java 的默认值机制不一样),所以这是**纯 Python 差异,你必须记住**。

**验收(硬):** 手动构造两轮调用,第二轮把第一轮的问答塞进 history,然后问"我刚才问了什么"——模型要能答出来。

### 练习 C:写一个多轮对话 REPL(40 分钟,本周产出)

新建 `src/chat_repl.py`。这是 Week 2 的可跑产出。

**要求(自己实现,我不给代码):**

| # | 功能 | 要点 |
|---|---|---|
| 1 | 循环读输入 | `while True` + `input()`,空行跳过 |
| 2 | `/exit` 退出 | `break` |
| 3 | `/reset` 清空历史 | 清完之后模型应该"失忆" |
| 4 | 每轮打印本轮 token + 成本 | 复用 `LLMResponse` 里的字段 |
| 5 | 追加历史 | 每轮把 user 和 assistant 两条都 append 进去 |
| 6 | 历史截断 | 超过 N 轮就丢最早的(保留 system) |

**骨架(签名给你,实现留给你):**

```python
"""Week 2:多轮对话 REPL。"""
from .config import Settings
from .llm_client import LLMClient

MAX_TURNS = 10          # 保留最近多少轮

def main() -> int:
    settings = Settings.from_env()
    client = LLMClient(settings)

    history: list[dict[str, str]] = []
    total_cost = 0.0
    # TODO 1: 循环读输入
    # TODO 2: 处理 /exit 和 /reset
    # TODO 3: 调 client.chat(..., history=history)
    # TODO 4: 把 user 和 assistant 两条 append 进 history
    # TODO 5: 打印本轮 + 累计 token/成本
    # TODO 6: 超长就截断(提示:history 是 list,切片就能截)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

**验收(全是硬的,你自己就能测):**

1. **多轮记忆**:第 1 句告诉它"我叫孟工",第 3 句问"我叫什么"——要答对
2. **失忆可验证**:`/reset` 之后再问"我叫什么"——要答不知道
3. **token 符合预测**:第 2 轮的输入 tokens ≈ 第 1 轮输入 + 第 1 轮输出 + 新提问(误差在几条以内)
4. **截断生效**:连问 12 轮,输入 tokens 不再无限增长,稳定在某个上限附近

**第 3 条是本轮的核心验收。** 它能跑通,说明"重发全历史"这件事你是真懂了。

### 练习 D(加餐,有余力再做):流式输出

现在的实现是"等模型全部生成完才一次性返回"。流式是边生成边打印。

关键点:`stream=True` 之后返回的不再是完整对象,而是**一个可迭代的增量流**;并且 `usage` 默认不返回,要额外传 `stream_options={"include_usage": True}`。

**验收:** 文字是一个一个蹦出来的(不是一次性出现),并且结束后仍能打印出 token 数。

---

## 3. Java 视角:这几个差异你要主动记住

| 主题 | Java | Python | 风险 |
|---|---|---|---|
| 数据结构 | 先定义 DTO class,字段有编译检查 | `dict` 字面量直接写,**拼错 key 运行时才炸** | ⚠️ 高 |
| 类型安全 | 编译器兜底 | 靠类型标注 + 工具,运行时不检查 | ⚠️ 高 |
| 方法重载 | `overload` | 默认参数 `=None` 模拟 | 中 |
| 可变默认值 | 无此问题 | **默认参数只求值一次,共享** | ⚠️ 高 |
| 循环控制 | `for` / `while` | 一样,但 `range(1,5)` **不含 5** | 中 |

**主动补回类型安全(推荐做,10 分钟):** 用 `TypedDict` 定义消息结构,Java 类比就是 DTO:

```python
from typing import TypedDict

class Message(TypedDict):
    role: str
    content: str
```

然后 `list[Message]`。这样编辑器能提示字段、拼错会被指出来 —— **主动把 Java 的优势在 Python 里补回来,这是你的长项,别丢掉。**

---

## 4. 常见坑(按踩中概率排序)

| # | 坑 | 症状 | 解法 |
|---|---|---|---|
| 1 | `history` 默认参数写 `=[]` | 第二轮莫名带着上一次的历史 | 用 `=None` 当哨兵 |
| 2 | dict 的 key 拼错(`role` → `roles`) | API 报 400,信息晦涩 | 用 `TypedDict`;或打印出 messages 看一眼 |
| 3 | 忘了 append assistant 的回答 | 模型"记不住自己说过什么" | 每轮 append 两条,不是一条 |
| 4 | `input()` 带首尾空白/换行 | 提问里混进 `\n` | `.strip()` |
| 5 | 截断时把 system 也丢了 | 模型突然开始客套、变啰嗦 | system 单独存,不放进被截断的部分 |
| 6 | 以为 token 是线性的 | 长对话费用超预期 | 看 `usage`,做第 3 条验收预测 |

---

## 5. 学完这周你应该能回答(自检 5 题)

1. 为什么说 LLM API 是无状态的?那"多轮对话"是谁在做?
2. 第 5 轮的输入 token 里,包含哪些东西?
3. 为什么长对话的成本是超线性增长,不是线性?
4. `history=[]` 作为默认参数会发生什么?为什么?
5. 历史截断时,为什么 system 消息不能一起丢?

答不上来就回去看第 1 节——**这 5 题是 Week 3(Prompt 工程)的地基。**

---

## 6. 节奏建议

| 时间 | 内容 |
|---|---|
| 第 1 次(1-1.5h) | 练习 A + 读第 1 节,把"无状态"这件事想透 |
| 第 2 次(1-1.5h) | 练习 B,改 `chat()` 签名 |
| 第 3 次(2h) | 练习 C 主体 |
| 第 4 次(1-2h) | 练习 C 验收 + 5 道自检题 |

约 6-8h。**做完练习 C 就是本周可跑产出。** 做完告诉我,进 Week 3(Prompt 工程 + Structured Output)。
