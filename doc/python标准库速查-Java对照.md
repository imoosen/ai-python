# Python 标准库速查（Java 对照）

> 回答的问题："练习里我一直没 import 任何东西，Python 自带的类有哪些、高频的是哪些？"
> 你 mini 上是 Python 3.13.6，本表在 3.12/3.13 无差别。

## 为什么你到现在没 import 过

**内置类型不用 import**：`list`、`dict`、`set`、`tuple`、`str`、`int`、`float`、`bool`、`print`、`len`、`type`、`range`、`open` 全是"语言自带"，相当于 Java 的 `java.lang`（自动 import 的那部分）。练习只用了内置，所以一个 import 都没有。

第一个真正的 import 就在 `src/config.py` 第一行：`import os`。

## 高频对照表（按你的 12 周路线排序）

| 场景 | Java (JDK) | Python | 要 import 吗 |
|---|---|---|---|
| 动态数组 | `ArrayList` | `list` | 内置 |
| 哈希表 | `HashMap` | `dict` | 内置 |
| 集合 | `HashSet` | `set` | 内置 |
| 不可变列表/元组 | `List.of` | `tuple` | 内置 |
| 枚举 | `enum` | `enum.Enum` | ✓ `from enum import Enum` |
| 不可变数据类 | `record` | `dataclasses.dataclass(frozen=True)` | ✓ |
| 环境变量 | `System.getenv` | `os.getenv("K", "默认值")` | ✓ `import os` |
| JSON | Jackson（**第三方**） | `json`（**内置**） | ✓ `import json` |
| 文件路径 | `Path` / `Paths` | `pathlib.Path` | ✓ |
| 读文件 | `Files.readAllLines` | `Path.read_text()` / `open()` | ✓ (pathlib) |
| 日期时间 | `java.time.*` | `datetime` | ✓ |
| 正则 | `Pattern` / `Matcher` | `re` | ✓ |
| 日志 | SLF4J + Logback（第三方） | `logging`（内置） | ✓ |
| 计数/统计 | Stream + groupingBy | `collections.Counter` | ✓ |
| 双端队列 | `ArrayDeque` | `collections.deque` | ✓ |
| Stream 管道 | `map/filter/sorted` | 列表推导式 + `sorted(key=)` | 内置语法 |
| Optional | `Optional<T>` | 没有，用 `None` + `str \| None` 标注 | — |
| 命令行参数 | `main(String[] args)` | `sys.argv` / `argparse` | ✓ |
| 进程 | `ProcessBuilder` | `subprocess` | ✓ |
| 哈希/编码 | `MessageDigest` / `Base64` | `hashlib` / `base64` | ✓ |
| UUID | `UUID` | `uuid` | ✓ |
| SQLite | JDBC（第三方驱动） | `sqlite3`（**内置**） | ✓ |
| 退出 | `System.exit` | `sys.exit` | ✓ |
| 测试 | JUnit（第三方） | `unittest`（内置）/ pytest（事实标准） | ✓ |
| 并发 | 线程 / 虚拟线程 | `threading` / `asyncio` / `queue` | ✓ |

## 两个和 Java 期望相反的点

1. **Java 要装第三方的东西，Python 不少是内置的**：JSON、SQLite、正则、日志、测试框架、命令行解析全在标准库里。Python 的口号叫"batteries included（自带电池）"。
2. **内置 ≠ 不用学**：`dict`/`list` 的方法面（`.get`/`.items`/`.append`）你已经练了；`json.loads/dumps`、`os.getenv` 是下一步马上要用的。

## 你 12 周内真正高频的前 10 个

```
json         每次 LLM 返回都要解
os           环境变量、路径
pathlib      文件读写
dataclasses  所有配置和响应对象
enum         错误分类（llm_client.py 现成的 ErrorClass）
datetime     延迟、时间戳
typing       类型标注（str | None、list[dict[str, str]]）
re           文本清洗
logging      比 print 正式的输出
collections  Counter / defaultdict
```

## 命名规则（防拼错）

- **模块全小写**：`os`、`json`、`dataclasses` —— import 的是模块，不是类
- **类 PascalCase**：`Enum`、`Path`、`Counter`
- **函数/变量 snake_case**：`load_dotenv()`、`getenv()`
- **dunder 双下划线**：`__init__`、`__name__` —— 单双下划线别混
- 没有 `new`：`Path("a.txt")` 直接调

## 马上会遇到的第三方包（pip 装的）

| 包 | 用途 | 出现位置 |
|---|---|---|
| `python-dotenv` | 读 .env 文件 | config.py：`from dotenv import load_dotenv` |
| `openai` | LLM SDK（兼容 DeepSeek） | llm_client.py |

第三方和标准库的区别：标准库随 Python 安装即有；第三方要 `pip install`（装进 `.venv`，清单记在 `requirements.txt`）——相当于 Maven 依赖，只是不写 pom.xml。
