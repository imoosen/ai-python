# Week 2 踩坑实录（错题本）

> 来源：2026-10-27 ~ 10-29 REPL 实操，每一条都是亲手撞出来的。
> 复习方式：遮住「正确姿势」，只看报错信息，能说出原因才算过关。

---

## 一、print 与字符串

### 1.1 print 是函数，不是语句

```python
print name          # ✗ SyntaxError（Python 2 的写法）
print(name)         # ✓
```

**原因**：Python 3 里 print 是函数，必须带括号。类比 `System.out.println(name)`。
**附带**：`print` 的全部可调项就两个——`sep`（参数间分隔，默认空格）、`end`（结尾，默认换行）。

### 1.2 `"n=" + 3` → TypeError

```python
print("n=" + 3)     # ✗ TypeError: can only concatenate str (not "int") to str
print("n=" + str(3))    # ✓ 显式转换
print(f"n={3}")         # ✓ f-string
print("n=", 3)          # ✓ 逗号 = 两个参数，sep 自动加空格 → "n= 3"
```

**原因**：Java 的 `+` 会隐式调 `String.valueOf`，Python 拒绝隐式转换（"显式优于隐式"）。
**注意**：`print(1, 2)` 输出 `1 2`；`print(1 + 2)` 输出 `3`。逗号是传参，`+` 是先运算。

### 1.3 手写空格会与 sep 叠加

```python
print(k, " = ", v)    # role  =  assistant（双空格）
print(k, "=", v)      # role = assistant（sep 各加一个）
print(f"{k}={v}")     # role=assistant（要精确控制就用 f-string）
```

**规范**：调试打多个值靠默认 sep；拼文本、写日志、发 API 用 f-string（sep 只活在 print 内部）。

---

## 二、环境与缩进

### 2.1 activate 要站在项目根目录

```bash
cd .venv            # ✗ 站进去之后路径就错了
source .venv/bin/activate   # ✓ 永远从项目根目录敲
```

### 2.2 Tab 与空格混用 → TabError

**规则**：Python 用缩进长度划分代码块（Java 用 `{}`）。编辑器里按 Tab 键没问题（自动转 4 空格），但 Tab 字符和空格混在同一层就报 `TabError`。一层代码块只用一种。

---

## 三、list 与 dict（Week 2 核心）

### 3.1 dict 没有位置索引 → KeyError: -1

```python
d = {"role": "user", "content": "你好"}
d["roles"]    # ✗ KeyError: 'roles'（键名拼错，无模糊匹配）
d[-1]         # ✗ KeyError: -1（-1 被当成"键"去查，dict 没有"第几个"）
```

**判别**：报错是 `KeyError` 就是键的问题，`IndexError` 才是位置越界。
**Java 对照**：`map.get("roles")` 返回 null，Python 直接抛——Java 把"取不到"当"没有"，Python 当"错误"。带兜底：`d.get(k, 默认值)`（不抛）。

### 3.2 for 遍历 dict 得到的是键，不是键值对

```python
for msg in d:            # msg 依次是 "role"、"content"（字符串！）
for k, v in d.items():   # ✓ ≈ Java 的 entrySet()
```

| Python | Java | 得到 |
|---|---|---|
| `for k in d:` | `keySet()` | 键 |
| `for k, v in d.items():` | `entrySet()` | 键+值 |
| `for v in d.values():` | `values()` | 值 |

**调试习惯**：类型不对就先问——`print(type(x))`，一行定位"我遍历的到底是什么"。

### 3.3 拆包数量必须严格相等

```python
for k, v in history[1]:        # ✗ ValueError: too many values to unpack (expected 2)
for k, v in history[1].items(): # ✓
```

**原因**：漏了 `.items()`，遍历 dict 拿到键 `"role"`，Python 试图把 4 个字符拆成 2 个变量。
**Java 没有拆包**：`a, b = 1, 2` 是 Python 特有的元组解构，左右数量必须一致。

### 3.4 键名必须加引号

```python
msg.[role]     # ✗ SyntaxError（多了个点）
msg[role]      # ✗ NameError: name 'role' is not defined（被当成变量）
msg['role']    # ✓
```

### 3.5 append 返回 None

```python
nums = []
result = nums.append(3)   # result 是 None！
nums = nums.append(3)     # ✗ 经典事故：把列表直接丢了，且不报错
```

**Java 对照**：`list.add()` 返回 boolean；Python 的 `append` 返回 None——**调用后不要接返回值**。

### 3.6 正确的两层结构（多轮对话的真实数据形状）

```python
history = []
history.append({"role": "user", "content": "你好"})
history.append({"role": "assistant", "content": "你好，我是助手"})
history.append({"role": "user", "content": "今天上海天气"})

print(history[-1]["content"])     # 先按位置取 dict，再按键取值
for msg in history:
    print(msg["role"], "->", msg["content"])
```

Java 等价：`List<Map<String, String>>`。

---

## 四、异常

### 4.1 SyntaxError 在编译期，try 管不住

```python
try:
    result = 123sdf      # ✗ SyntaxError: invalid decimal literal
except ValueError:
    ...
```

**原因**：源码先编译成字节码，编译不过整个 try 块根本没执行。Java 同理：编译不过的代码不存在"被 catch"。
**教训**：造异常要用运行时才发生的表达式——`int("abc")`、`{}["x"]`、`1/0`、`未定义变量`。

### 4.2 一行代码三颗雷，一次只修一个

```python
except Exceptions as ex        # 雷1: 少冒号(SyntaxError，挡住后面)
                               # 雷2: Exceptions 拼错，内置名是 Exception
    print(f"{exc}")            # 雷3: as ex 接的，打印却用 exc
```

修完雷 1 才能暴露雷 2、3。**报错一次只修一个，修完再跑。**

### 4.3 dunder 是双下划线

```python
type(exc)._name_     # ✗ AttributeError
type(exc).__name__   # ✓
```

`__xxx__` 是保留命名空间，已见过的：`__init__`（构造器）、`__name__`（名字）、`__repr__`（打印格式）。看到单下划线先怀疑少敲一个。

### 4.4 except 顺序：宽泛在前会吞掉精确分支

```python
try:
    ...
except Exception as exc:    # KeyError 会被这里接住
    ...
except KeyError as exc:     # 永远执行不到，但 Python 不报错
    ...
```

**Java 会报 unreachable catch**（编译器拿静态类型证明）；Python 动态类型，`except` 后面的名字运行时才查找，编译期不检查——**从上到下第一个匹配的分支生效**。
项目实证：`llm_client.py` 用 `except Exception` 是故意的（SDK 异常种类不稳定），抓下来交给 `classify()` 按 `isinstance` 分类。

### 4.5 except Exception 抓不到 Ctrl-C

```python
except KeyboardInterrupt:   # 继承 BaseException，不继承 Exception
```

设计意图：业务代码不该把用户中断当普通错误吞掉。顺序无关——类型不匹配才是关键。

### 4.6 异常链：隐式 vs 显式

```python
# 隐式：except 块里又抛新异常 → "During handling of the above exception..."
# 显式：
raise AgeError(f"收到 {text!r}") from exc
# → "The above exception was the direct cause of..."
```

**Java 对照**：不带 cause 的 `throw new E(msg)` 会丢原始异常；`new E(msg, cause)` 对应 `from exc`。Python 默认帮你留链。

### 4.7 日志打值用 !r

```python
text = " 20 "
print(f"收到 {text}")    # 空格看不见
print(f"收到 {text!r}")  # ' 20 ' —— repr 带引号，空串/空格/不可见字符一目了然
```

排查解析失败类问题，必看 repr。

---

## 五、高频报错速查

| 报错 | 一句话原因 |
|---|---|
| `SyntaxError` | 语法错，代码没运行（编译期） |
| `NameError` | 名字不存在（拼错 / 没引号 / as 变量名不一致） |
| `TypeError` | 类型不匹配（str + int、字符串当索引用） |
| `KeyError` | dict 里没有这个键 |
| `IndexError` | list 位置越界 |
| `ValueError` | 值的类型对但内容不对（int("abc")）或拆包数量不等 |
| `AttributeError` | 对象没有这个属性/方法（对字符串调 .get） |
