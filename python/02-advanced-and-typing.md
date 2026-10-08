# Python 速通 · 第 2 天：进阶特性与类型提示

> **目标**：掌握写 FastAPI 项目必备的进阶语法，尤其是**类型提示**
> **预计**：4–5 小时（含练习）

---

## 1. 推导式

Python 最常用的语法糖，用来替代 C++ 里的 for 循环 + push_back。

```python
# 列表推导式
squares = [x * x for x in range(10)]
evens   = [x for x in range(20) if x % 2 == 0]

# 带条件表达式
labels = ["偶" if x % 2 == 0 else "奇" for x in range(5)]

# 嵌套
matrix = [[i * j for j in range(3)] for i in range(3)]

# 字典推导式
word_len = {w: len(w) for w in ["hi", "hello"]}      # {'hi': 2, 'hello': 5}
flipped  = {v: k for k, v in word_len.items()}

# 集合推导式（自动去重）
uniq = {x % 3 for x in range(10)}                    # {0, 1, 2}
```

**等价对比**：

```python
# 推导式（推荐）
result = [f(x) for x in data if cond(x)]

# 等价循环（啰嗦）
result = []
for x in data:
    if cond(x):
        result.append(f(x))
```

> **刷题提示**：读输入、处理矩阵、构造哈希表，推导式能省你很多行。

---

## 2. 生成器与迭代协议

### 2.1 迭代协议

`for x in obj` 的本质是：先调 `iter(obj)` 拿到迭代器，再反复调 `next()` 直到 `StopIteration`。

```python
class Countdown:
    def __init__(self, start):
        self.n = start

    def __iter__(self):
        return self

    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1

for i in Countdown(3):
    print(i)      # 3 2 1
```

### 2.2 `yield`：写生成器的最简方式

函数里只要有 `yield`，它就变成生成器函数，调用时**不执行函数体**，只返回一个生成器。

```python
def countdown(n):
    while n > 0:
        yield n          # 每次 next() 执行到这里暂停并返回
        n -= 1

for i in countdown(3):
    print(i)             # 3 2 1
```

### 2.3 生成器 vs 列表：内存差异

```python
import sys

lst = [x for x in range(1_000_000)]        # 立刻占用几十 MB
gen = (x for x in range(1_000_000))        # 几乎不占内存

print(sys.getsizeof(lst))   # 约 8 MB
print(sys.getsizeof(gen))   # 约 200 字节
```

**结论**：处理大文件、大结果集时用生成器，内存友好。

```python
# 逐行读大文件，不会把整个文件读进内存
def read_large(path):
    with open(path) as f:
        for line in f:
            yield line.strip()
```

### 2.4 `yield from`

```python
def chain(*iterables):
    for it in iterables:
        yield from it          # 等价于 for x in it: yield x

list(chain([1, 2], [3, 4]))    # [1, 2, 3, 4]
```

---

## 3. 装饰器

**前提回顾（第 1 天）**：函数是对象，可以当参数传、可以返回。

### 3.1 手写一个装饰器

```python
import time

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)     # 调用原函数
        cost = time.perf_counter() - start
        print(f"{func.__name__} 耗时 {cost:.4f}s")
        return result
    return wrapper                     # 返回新函数

@timer                                 # 等价于 slow = timer(slow)
def slow():
    time.sleep(1)

slow()     # 输出：slow 耗时 1.00xx s
```

### 3.2 ⚠️ 必须加 `functools.wraps`

上面 `wrapper` 会丢掉原函数的名字和文档：

```python
print(slow.__name__)   # 输出 wrapper  ← 不是 slow，出问题了
```

正确写法：

```python
import functools

def timer(func):
    @functools.wraps(func)             # 保留原函数的元信息
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            print(f"{func.__name__} 耗时 {time.perf_counter() - start:.4f}s")
    return wrapper
```

### 3.3 带参数的装饰器（三层嵌套）

```python
def retry(times=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception:
                    if attempt == times - 1:
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(times=3, delay=0.5)
def flaky_api_call():
    ...
```

> **实战中你会用到**：FastAPI 的 `@app.get()`、`@app.middleware()`、`@pytest.fixture`、Pydantic 的 `@field_validator` —— 全是装饰器。

---

## 4. 上下文管理器（`with`）

### 4.1 为什么需要

```python
# 不用 with：容易忘记关
f = open("a.txt")
try:
    data = f.read()
finally:
    f.close()

# 用 with：自动释放，即使中途抛异常
with open("a.txt") as f:
    data = f.read()
```

### 4.2 自己实现：`__enter__` / `__exit__`

```python
class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self                  # as 后面的变量拿到这个

    def __exit__(self, exc_type, exc_val, tb):
        print(f"耗时 {time.perf_counter() - self.start:.4f}s")
        return False                 # 返回 True 会吞掉异常，一般返回 False

with Timer():
    time.sleep(1)
```

### 4.3 更简单的写法：`contextlib`

```python
from contextlib import contextmanager

@contextmanager
def timer():
    start = time.perf_counter()
    try:
        yield                        # yield 之前的相当于 __enter__
    finally:
        print(f"耗时 {time.perf_counter() - start:.4f}s")

with timer():
    time.sleep(1)
```

> **实战中你会用到**：数据库连接、Redis 连接、asyncio 锁、`httpx.AsyncClient`。

---

## 5. 异常处理

```python
try:
    risky()
except (ValueError, TypeError) as e:     # 捕获多种
    print(f"参数错误: {e}")
except KeyError:
    print("键不存在")
except Exception as e:                   # 兜底
    print(f"未知错误: {e}")
    raise                                # 重新抛出，保留堆栈
else:
    print("没出错才执行")                  # 可选
finally:
    print("无论如何都执行")                # 可选，用于清理
```

### 5.1 自定义异常

```python
class BizError(Exception):
    """业务异常基类"""
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)

class UserNotFound(BizError):
    def __init__(self, uid):
        super().__init__(404, f"用户 {uid} 不存在")

try:
    raise UserNotFound(1)
except BizError as e:
    print(e.code, e.message)
```

### 5.2 EAFP vs LBYL

- **LBYL**（Look Before You Leap）：先检查再操作 —— C 风格
- **EAFP**（Easier to Ask Forgiveness than Permission）：直接做，出错再处理 —— Python 风格

```python
# LBYL（不推荐）
if "key" in d:
    value = d["key"]
else:
    value = None

# EAFP（推荐）
try:
    value = d["key"]
except KeyError:
    value = None

# 或者直接用 .get()
value = d.get("key")
```

> Python 社区偏好 EAFP。**但用 `.get()` / `.setdefault()` 这类现成方法更简洁。**

---

## 6. 类型提示（⭐ 本节最重要）

### 6.1 为什么它对你至关重要

因为你后面要写 FastAPI，而 **FastAPI 和 Pydantic 的核心机制就是读你的类型注解**：

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str                          # ← FastAPI 靠这个做参数校验
    price: float
    tags: list[str] = []

@app.post("/items")
async def create_item(item: Item) -> dict:   # ← 靠注解自动解析请求体
    return {"name": item.name}
```

**不写类型提示 = 用不了 FastAPI 的核心能力。** 这不是"可选的风格问题"，是硬性要求。

### 6.2 基本写法

```python
# 变量注解
name: str = "benfu"
count: int = 0
ratio: float = 0.5
active: bool = True

# 函数签名
def greet(name: str, times: int = 1) -> str:
    return f"hi {name} " * times
```

### 6.3 容器类型（Python 3.9+ 用内置泛型）

```python
nums: list[int] = [1, 2, 3]
mapping: dict[str, int] = {"a": 1}
unique: set[str] = {"a", "b"}
pair: tuple[int, str] = (1, "a")
fixed: tuple[int, int, int] = (1, 2, 3)
```

### 6.4 Optional / Union / `|`

```python
from typing import Optional, Union

# 三种等价写法
def f1(x: Optional[str]) -> None: ...        # 老写法
def f2(x: Union[str, None]) -> None: ...     # 等价
def f3(x: str | None) -> None: ...           # 新写法（3.10+），推荐

def g(x: int | str) -> None: ...             # 多类型
```

> `Optional[str]` 的意思是"str **或** None"，**不是"可选参数"**。这是个常见误解。

### 6.5 常用补充类型

```python
from typing import Any, Literal, TypedDict

x: Any = anything()                          # 放弃类型检查，少用

# Literal：限定取值范围（FastAPI 里做枚举校验很好用）
Mode = Literal["read", "write", "append"]
def open_file(path: str, mode: Mode) -> None: ...

# TypedDict：给字典定义结构
class UserDict(TypedDict):
    name: str
    age: int

u: UserDict = {"name": "benfu", "age": 20}

# Callable：函数类型
from collections.abc import Callable
Handler = Callable[[int, str], bool]
```

### 6.6 ⚠️ 关键认知：类型提示**运行时不做检查**

```python
def add(a: int, b: int) -> int:
    return a + b

add("hello", "world")     # 不报错！返回 "helloworld"
```

类型提示是给**静态检查工具**（mypy、ruff）和**框架**（FastAPI、Pydantic）看的，Python 解释器本身不管。

要强制执行，得用：

```bash
uv run mypy your_file.py       # 静态类型检查
uv run ruff check .            # 代码规范检查
```

### 6.7 加分项：`from __future__ import annotations`

```python
from __future__ import annotations      # 让注解延迟求值

class Node:
    def __init__(self, next: Node | None = None):   # 不用写引号了
        self.next = next
```

不加这行，引用尚未定义的类要写成字符串 `"Node"`。

---

## 7. 模块、包与工程结构

### 7.1 模块与导入

```python
# 标准库
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# 第三方
import httpx
from fastapi import FastAPI, HTTPException

# 自己的模块
from app.models import User
from .utils import helper          # 相对导入
```

### 7.2 包 = 目录 + `__init__.py`

```
myproject/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   └── routers/
│       ├── __init__.py
│       └── users.py
├── tests/
│   └── test_main.py
├── pyproject.toml          # uv 管理的依赖声明
└── README.md
```

### 7.3 `if __name__ == "__main__"`

```python
def main():
    print("程序入口")

if __name__ == "__main__":    # 只有直接运行这个文件时才执行
    main()                    # 被 import 时不执行
```

等价于 C 的 `int main()`，但**必须显式判断**，否则 import 时会执行。

### 7.4 uv 工作流（你的日常命令）

```bash
uv init myproject             # 初始化项目
uv add fastapi httpx          # 加依赖（自动写进 pyproject.toml）
uv add --dev pytest ruff      # 开发依赖
uv sync                       # 按 lock 文件同步环境
uv run python main.py         # 在项目环境里运行
uv run pytest                 # 运行测试
```

---

## 8. 第 2 天练习

**① 推导式**
把下面这段用一行推导式改写：
```python
result = []
for word in ["hello", "hi", "world"]:
    if len(word) > 2:
        result.append(word.upper())
```

**② 生成器**
写一个生成器 `fib()`，无限产出斐波那契数列，然后用 `itertools.islice` 取前 10 个。

**③ 装饰器**
写一个 `@count_calls` 装饰器，记录函数被调用了多少次，并支持 `.calls` 属性查看。记得用 `functools.wraps`。

**④ 上下文管理器**
用 `@contextmanager` 写一个 `db_transaction()`：进入时打印"开始事务"，正常退出打印"提交"，异常时打印"回滚"并重新抛出。

**⑤ 类型提示**（重点）
给下面这个函数补全类型注解，然后用 `uv run mypy` 检查：
```python
def process_users(users, default_role, verbose):
    result = {}
    for u in users:
        result[u["name"]] = u.get("role", default_role)
    if verbose:
        print(result)
    return result
```

**⑥ 综合**
写一个 `@retry(times=3)` 装饰器 + 一个会随机失败的函数，验证重试逻辑生效。

---

## 9. 自查

- [ ] 能熟练写列表/字典/集合推导式
- [ ] 能说清生成器相比列表的内存优势
- [ ] 能默写一个带 `functools.wraps` 的装饰器
- [ ] 能说清 `@contextmanager` 里 `yield` 前后各对应什么
- [ ] 能自定义异常类
- [ ] **能用 `list[int]` / `dict[str, int]` / `str | None` 写类型注解**
- [ ] **知道类型提示运行时不做检查，是给 mypy 和 FastAPI 用的**
- [ ] 会用 `uv add` / `uv run` 管理项目

全部打勾 → 进入第 3 天。
