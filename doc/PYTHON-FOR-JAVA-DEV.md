# 用 Java 视角学 Python

> 教材就是你项目里的代码:`src/config.py`、`src/llm_client.py`、`src/hello_llm.py`
> 前提:你已经会编程。本文只讲**差异**,不讲 for 循环怎么写。

---

## 0. 先定位:你缺什么,不缺什么

| 你已经有(直接迁移) | 你要补的(1-2 周形成肌肉记忆) |
|---|---|
| 类型思维、面向对象 | Python 的语法糖 |
| 异常处理、分层设计 | 工具链(venv / pip) |
| 依赖管理(Maven 那套) | 动态语言特有的写法 |
| 并发、IO 模型 | 没有编译器的世界怎么保证正确性 |

**结论:语法 1-2 天能过,工具链和习惯 1-2 周形成。** 别去看"Python 从入门到精通"的视频,那是给没编过程的人的。

---

## 1. 工具链对照(Maven → pip + venv)

| 概念 | Java | Python |
|---|---|---|
| 依赖声明 | `pom.xml` | `requirements.txt` |
| 装依赖 | `mvn install` | `pip install -r requirements.txt` |
| 隔离环境 | 无(Maven 全局仓库) | **venv**(每个项目一个独立环境) |
| 解释器 | `java -version` | `python --version` |
| 运行 | `java -jar app.jar` | `python -m src.hello_llm` |
| 版本锁定 | `pom.xml` 里的 `<version>` | `requirements.txt` 的 `==` 号 |

**为什么 Python 需要 venv 而 Java 不需要?**
Java 的依赖是"每个项目一份 jar,打包时一起带走",天然隔离。
Python 的依赖装到**解释器级别的 site-packages** 里,全局共享 —— 项目 A 要 `openai==3.0`,项目 B 要 `openai==2.0`,直接冲突。
所以 Python 每个项目建一个 venv,把依赖装进项目自己的目录。**你现在这个项目的 venv 在 `.venv/`。**

**每次开新终端第一件事**:

```bash
source .venv/bin/activate    # 类比:进到项目专属环境
```

激活后命令行前面会出现 `(.venv)`,这时 `pip` 和 `python` 都指向项目自己的那份。

---

## 2. 语法差异速查(只讲你项目里出现的)

### 2.1 变量不需要声明类型

```python
# Java:  String name = "孟工";
name = "孟工"
count = 3
ratio = 0.5
```

Python 是**动态类型**:类型跟着值走,变量只是个名字。
可以在后面加类型注解(给 IDE 看的,运行时不检查):

```python
name: str = "孟工"
count: int = 3
```

> 你项目里 `def backoff_seconds(attempt: int, base: float = 1.0) -> float:` 就是这个注解。
> 写了 IDE 会提示,但**运行时传错类型不会报错**(不像 Java 编译期就拦住)。

### 2.2 缩进就是语法(没有大括号)

```python
# Java
// if (x > 0) {
//     System.out.println("正数");
// }

# Python —— 冒号 + 缩进,没有 {}
if x > 0:
    print("正数")
else:
    print("非正数")
```

缩进错了 = 语法错误。这是新手最容易摔的地方。

### 2.3 字符串模板:f-string

```python
# Java 15+  String s = String.format("你好 %s,%d 岁", name, age);

# Python 3.6+ —— 字符串前加 f,花括号里直接写表达式
s = f"你好 {name},{age} 岁"
```

你项目里到处都是:

```python
print(f"耗时       : {response.latency_seconds:.2f}s")   # :.2f = 保留两位小数
print(f"[重试] 第 {attempt}/{max_attempts} 次失败")
```

`:.2f` 这种格式化语法和 Java 的 `%.2f` 是一回事。

### 2.4 集合:list 和 dict 就是 ArrayList 和 HashMap

```python
# Java
// List<String> list = new ArrayList<>();
// list.add("a");
// Map<String, String> map = new HashMap<>();
// map.put("role", "user");

# Python —— 字面量直接写
list_items = ["a", "b"]
map_items = {"role": "user", "content": "你好"}
list_items.append("c")        # 类比 add()
value = map_items["role"]     # 类比 get()
```

字典在 LLM 应用里是**最常用的结构**,因为 API 的请求就是一个 dict:

```python
{"role": "user", "content": "你好"}
```

你项目里:

```python
messages: list[dict[str, str]] = []
messages.append({"role": "system", "content": system})
```

`list[dict[str, str]]` 读作:`list,里面装的是 dict,key 是 str,value 也是 str`。
类比 Java:`List<Map<String, String>>`。

### 2.5 None 就是 null

```python
def chat(self, prompt: str, system: str | None = None) -> LLMResponse:
```

`str | None` = `String` 或 `null`,Java 里你写 `@Nullable String`。
`= None` 是**默认参数值** —— Java 没有这个,Java 要用重载方法:

```java
// Java 要写两个方法
void chat(String prompt) { chat(prompt, null); }
void chat(String prompt, String system) { ... }
```

Python 一个方法搞定,默认值写在签名里。

### 2.6 异常:try-except 而不是 try-catch

```python
# Java
// try { ... }
// catch (IOException e) { ... }
// finally { ... }

# Python
try:
    result = do_something()
except ValueError as exc:        # as e 写成 as exc
    print(f"出错了: {exc}")
finally:
    cleanup()
```

**重要差异**:Python 里 `except Exception as exc:` 能抓到几乎所有异常(类似 Java 的 `catch (Exception e)`)。
你项目里就有一处:

```python
except Exception as exc:  # noqa: BLE001
    klass = classify(exc)
```

`# noqa: BLE001` 是告诉代码检查工具"这个宽泛捕获是我故意的,别报警"。

### 2.7 不可变对象:@dataclass(frozen=True)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
```

Java 类比:

```java
// Java 17+
public record Settings(String apiKey, String model) {}
```

`frozen=True` = 所有字段 final,构造后不能改。**这是 Python 版的 record。**

`@dataclass` 会自动生成 `__init__`、`__repr__`、`__eq__`,不用手写。

### 2.8 类方法:@classmethod

```python
class Settings:
    @classmethod
    def from_env(cls) -> "Settings":
        ...
```

Java 类比:

```java
// Java: 静态工厂方法
public static Settings fromEnv() { ... }
```

`cls` 就是"类自己",类比 Java 的 `Settings.class`。这里用 `@classmethod` 而非 `@staticmethod`,是为了支持继承。

### 2.9 self = this(但必须显式写)

```python
class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings        # 类比 this.settings = settings

    def chat(self, prompt: str):
        return self._settings.model      # 类比 this.settings.model
```

三个差异:
1. **`self` 是第一个参数**,必须手写(Java 的 `this` 是隐式的)
2. **`__init__` 是构造器**(双下划线开头结尾的都有特殊含义)
3. **`_settings` 前面的下划线**表示"约定私有" —— 这只是**约定**,不是强制(Java 有 `private` 关键字,Python 没有)

### 2.10 枚举:Enum

```python
from enum import Enum

class ErrorClass(str, Enum):
    RETRYABLE = "retryable"
    AUTH = "auth"
```

Java 类比:

```java
public enum ErrorClass { RETRYABLE, AUTH }
```

`(str, Enum)` 表示这个枚举的值同时也是字符串,可以直接和 `"auth"` 比较。

---

## 3. 逐块读懂你的代码

### 3.1 `src/config.py` —— 配置装配

```python
load_dotenv()
```
读取项目根目录的 `.env` 文件,把里面的 `KEY=VALUE` 塞进环境变量。
Java 类比:Spring 的 `@PropertySource` + `Environment`。

```python
@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str
```

Java 类比:`public record Settings(String apiKey, String model)`。不可变配置对象。

```python
@classmethod
def from_env(cls) -> "Settings":
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("缺少环境变量 DEEPSEEK_API_KEY。...")
```

Java 类比:`public static Settings fromEnv()`,读环境变量,缺了就抛异常。
`os.getenv("X", "")` 的第二个参数是**默认值**(Java 的 `System.getenv("X")` 找不到返回 null)。

```python
def estimate(self, cache_hit_tokens: int, ...) -> float:
    return (
        cache_hit_tokens / 1_000_000 * self.input_cache_hit
        + ...
    )
```

`1_000_000` 下划线是**数字分隔符**,纯粹为了好读,值还是 1000000(Java 也支持)。

### 3.2 `src/llm_client.py` —— 核心

```python
class ErrorClass(str, Enum):
    RETRYABLE = "retryable"
    AUTH = "auth"
    QUOTA = "quota"
```

**这是整份代码里最值得学的设计**:把"错误"分成几类,每类对应一种处理动作。
- `RETRYABLE` → 等一会再试
- `AUTH` → 凭据问题,重试没用
- `QUOTA` → 去充值

Java 里你是用异常类型分层做的(`RetryableException` / `FatalException`),这里是同一个思路的 Python 版。

```python
def classify(exc: Exception) -> ErrorClass:
    if isinstance(exc, APIConnectionError):
        return ErrorClass.RETRYABLE
    if isinstance(exc, APIStatusError):
        code = exc.status_code
        if code in (401, 403):
            return ErrorClass.AUTH
```

- `isinstance(x, T)` = `x instanceof T`
- `code in (401, 403)` = 元组成员判断,类比 `Set.of(401,403).contains(code)`

```python
def backoff_seconds(attempt: int, base: float = 1.0, cap: float = 30.0) -> float:
    exponential = min(cap, base * (2 ** (attempt - 1)))
    return exponential * random.uniform(0.5, 1.0)
```

`2 ** 3` 是幂运算(Java 是 `Math.pow(2, 3)`)。
`min(a, b)` 是内置函数(类比 `Math.min`)。
`random.uniform(0.5, 1.0)` 生成 0.5~1.0 的随机浮点数 —— **这就是抖动(jitter)**。

```python
for attempt in range(1, max_attempts + 1):
```

`range(1, 5)` 产生 `1, 2, 3, 4`(**不含右端**)。
Java 类比:`for (int attempt = 1; attempt <= 4; attempt++)`。
**这是 Python 新手最容易错的点**:Python 的区间是左闭右开的。

```python
response = self._client.chat.completions.create(
    model=self._settings.model,
    messages=messages,
    extra_body=extra_body or None,
)
```

`extra_body=extra_body or None`:`or` 的短路特性 —— 如果 `extra_body` 是空 dict(`{}`,假值),就传 `None`。
Java 类比:`extra_body.isEmpty() ? null : extra_body`。

```python
except Exception as exc:
    klass = classify(exc)
    if klass is not ErrorClass.RETRYABLE or attempt >= max_attempts:
        raise LLMError(klass, str(exc), attempt) from exc
```

- `klass is not X`:用 `is` 判断对象身份(枚举比较推荐用 `is`)
- `raise ... from exc`:**链式异常** —— 抛出新异常时保留原始异常。
  Java 类比:`throw new LLMError(msg, exc)`(把 cause 传进构造器)

### 3.3 `src/hello_llm.py` —— 入口

```python
parser = argparse.ArgumentParser(description="Week 1:最小 LLM 调用")
parser.add_argument("-p", "--prompt", default=DEFAULT_PROMPT)
parser.add_argument("--selftest", action="store_true")
args = parser.parse_args(argv)
```

`argparse` 是标准库的命令行解析,**Java 类比:picocli / Spring Shell**。
`action="store_true"` 表示这是个开关(有就是 True)。

```python
if __name__ == "__main__":
    sys.exit(main())
```

**这行的意思**:只有"直接运行这个文件"时才执行,被 import 时不执行。
Java 类比:Java 没有这个概念,因为你直接跑 `main` 方法。

```python
DEFAULT_PROMPT = "..."
SYSTEM_PROMPT = "..."
```

**全大写 = 常量约定**。Java 是 `static final`,Python 只能靠命名约定。

---

## 4. 动手练习(改代码,不是读代码)

> 学习发生在你**改动代码并看到结果**的时候,不发生在你读代码的时候。

### 练习 1:改默认问题(5 分钟)

把 `hello_llm.py` 里的 `DEFAULT_PROMPT` 改成你关心的问题,跑一遍。

```bash
python -m src.hello_llm
```

**验收**:输出变了,而且 `输入 tokens` 的数量随问题长度变化。
**观察**:为什么同样一个问题,两次跑的 `输入 tokens` 一样但 `输出 tokens` 可能不一样?

---

### 练习 2:加一个 `--temperature` 参数(20 分钟)

**目标**:让命令行能控制随机性。

**提示**:`chat()` 方法里有 `extra_body`,但注意——DeepSeek 的思考模式下 `temperature` 不生效,而我们已经关掉了思考模式,所以这里能生效。

需要改两处:
1. `hello_llm.py` 的 `run_once()` 加参数,`argparse` 里加 `--temperature`
2. `llm_client.py` 的 `chat()` 加 `temperature: float | None = None` 参数,非空时塞进请求

**验收**:`python -m src.hello_llm --temperature 0` 跑两次,回答应该**完全一样**;
`--temperature 1.5` 跑两次,回答应该**明显不同**。

**你会学到**:`**kwargs` 传参、`None` 作为"不传"的哨兵值。

---

### 练习 3:改成多轮对话(40 分钟)

**目标**:让程序记住上一句说了什么。

**提示**:现在 `chat()` 每次调用都从空消息列表开始。要让对话连续,得把历史消息**存在外面**,每次调用时传进去。

需要:
1. 把 `messages` 从 `chat()` 内部提升为 `chat()` 的参数
2. 在 `run_once()` 里维护一个列表,每次问完把回答也 append 进去

**验收**:写一个循环,连续问三个相关问题(比如"我叫孟工" → "我是做什么的" → "我的名字是什么"),最后一句能答对名字。

**你会学到**:list 的增删、状态放在哪一层。**这是 Week 2 的核心内容,提前做等于抢跑**。

---

### 练习 4:加一个计时装饰器(30 分钟)

**目标**:不用改 `chat()` 内部代码,就给它加上"打印耗时"的能力。

Python 的装饰器相当于 Java 的注解 + AOP:

```python
import time
from functools import wraps


def timed(func):
    """装饰器:调用前后各打一次时间戳。"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[timed] {func.__name__} 耗时 {elapsed:.3f}s")
        return result

    return wrapper


# 用法:加一行注解在方法上
class LLMClient:
    @timed
    def chat(self, prompt: str, ...):
        ...
```

**验收**:调用后多打一行 `[timed] chat 耗时 1.832s`。

**你会学到**:装饰器、`*args/**kwargs`(可变参数)、闭包。
**Java 对照**:Java 里做这件事要写切面 + 代理,Python 一个函数搞定。

> 注意:上面的 `timed` 是**完整可用的代码**,直接抄进 `llm_client.py` 就能跑。

---

### 练习 5:加批量提问(40 分钟)

**目标**:一次问一串问题,打印每个回答和总成本。

**提示**:
- 命令行参数从"一个字符串"变成"多个字符串":`nargs="+"`
- 用一个循环,累计 `cost_cny`
- 用列表推导式收集结果

```python
# 列表推导式 —— Python 特有,Java 要用 Stream
# Java:  questions.stream().map(q -> client.chat(q)).toList()
results = [client.chat(q) for q in questions]
```

**验收**:`python -m src.hello_llm -p "问题1" "问题2" "问题3"` 输出三条回答 + 总成本。

**你会学到**:列表推导式、累加、`nargs`。

---

## 5. 自检:读完能不能回答这 10 个?

1. `1_000_000` 的值是多少?
2. `range(1, 5)` 会产生哪几个数?
3. `self` 是什么,和 Java 的 `this` 差在哪?
4. `@dataclass(frozen=True)` 对应 Java 的什么?
5. `str | None` 是什么意思?
6. `klass is not ErrorClass.RETRYABLE` 为什么用 `is` 而不是 `==`?
7. `raise X from exc` 里的 `from exc` 干什么用?
8. `if __name__ == "__main__":` 为什么需要?
9. `extra_body or None` 里 `or` 的作用是什么?
10. venv 解决了什么问题,Java 为什么不需要?

> 答不上来的,回到对应章节再读一遍。**这 10 个答得出,Python 语法你就过关了。**

---

## 6. 怎么继续学(别看的和该看的)

**别看的**:
- "Python 从入门到精通"这类零基础视频 —— 对你效率极低,前 5 小时都在讲变量和循环
- 语法大全类书籍 —— 查手册比读书快

**该看的**:
- **Python 官方教程**第 4-9 章(中文版),特别是"数据结构""类""错误和异常"—— 有编程基础的人读这个最合适
- 遇到不懂的语法点,直接在 REPL 里试:

```bash
python   # 进交互模式,敲一行看一行结果
```

交互式探索是 Python 的核心学习方式,相当于 Java 的 JShell 但好用得多。

---

## 7. 你的下一个里程碑

不要试图"学完 Python 再写 AI 应用"。正确顺序是:

```
读这份文档(1 小时)
  ↓
做练习 1-3(1.5 小时)
  ↓
进入 Week 2:多轮对话 + 流式输出
  ↓ 过程中遇到不懂的语法,回来查速查表
```

**语法是用出来的,不是学出来的。**
