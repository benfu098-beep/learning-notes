# Python 速查卡

> **用途**：卡住时 10 秒内找到答案。不是重新学一遍。
> **原则**：只记「容易搞混的」和「你总忘的」。抄讲义没有意义。
>
> 用法建议：写完代码后，把自己查过的东西补进来。**这份文件越长，说明你用得越多。**

---

## 一、最容易搞混的（这几条必须清楚）

### 变量是标签，不是盒子

```python
a = [1, 2]
b = a            # b 和 a 贴在同一个列表上
b.append(3)
print(a)         # [1, 2, 3]  ← 不是拷贝！

b = a.copy()     # 浅拷贝（只拷一层）
b = a[:]         # 同上
import copy
b = copy.deepcopy(a)   # 深拷贝（嵌套结构必须用这个）
```

### `is` vs `==`

```python
a == b    # 比【值】
a is b    # 比【身份】（是不是同一个对象）

if x is None:      # ✅ 判断 None 永远用 is
if x == None:      # ❌
```

### ⚠️ 可变默认参数（面试高频，必须背）

```python
# ❌ 错的：默认值只在函数【定义时】求值一次，所有调用共享同一个列表
def collect(x, acc=[]):
    acc.append(x)
    return acc

# ✅ 对的：真正的列表在【函数体】里创建，每次调用都是新的
def collect(x, acc=None):
    if acc is None:
        acc = []
    acc.append(x)
    return acc
```

`@dataclass` 里同理，要用 `field(default_factory=list)` 而不是 `= []`。

---

## 二、常用速查

```python
# dict
d.get(k, default)        # 取不到返回默认值，不抛异常 ⭐
d.setdefault(k, [])      # 不存在就设默认值（分组常用）
for k, v in d.items(): ...

# set
a & b   # 交
a | b   # 并
a - b   # 差

# 计数 / 分组
from collections import Counter, defaultdict
Counter("hello")                 # Counter({'l': 2, 'h': 1, 'e': 1, 'o': 1})
groups = defaultdict(list)
groups["a"].append(1)            # 不用先判断 key 存在

# 推导式
[x * x for x in range(5) if x % 2 == 0]
{w: len(w) for w in words}
{x % 3 for x in range(10)}

# 同时遍历下标和值
for i, v in enumerate(items): ...

# 合并两个列表
for a, b in zip(list1, list2): ...

# f-string
f"{name} 今年 {age} 岁，平均分 {score:.1f}"
```

---

## 三、模板（抄这个结构，改内容）

### 装饰器：两层

```python
import functools

def my_decorator(func):
    @functools.wraps(func)          # 别忘了，否则函数名会变成 wrapper
    def wrapper(*args, **kwargs):
        # 调用【前】的逻辑
        result = func(*args, **kwargs)
        # 调用【后】的逻辑
        return result
    return wrapper
```

### 装饰器：三层（带参数）

```python
def my_decorator(param=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator        # ⚠️ 返回 decorator，不是 wrapper
```

### 上下文管理器

```python
from contextlib import contextmanager

@contextmanager
def my_context():
    resource = acquire()        # ← yield 之前 ≈ __enter__
    try:
        yield resource          # 把资源交给 with 代码块
    finally:
        release(resource)       # 无论如何都执行清理
```

事务版本（只在无异常时提交）：

```python
@contextmanager
def transaction():
    print("BEGIN")
    try:
        yield
    except Exception:
        print("ROLLBACK")
        raise                   # ⚠️ 必须重新抛出，否则异常被吞掉
    else:
        print("COMMIT")
```

### 生成器

```python
def my_gen(n):
    for i in range(n):
        yield i * i

# 无限序列要配 islice
from itertools import islice
list(islice(fib(), 10))
```

生成器 **调用时不执行**，遇到 `next()` 才跑；不占内存。

### 类 + 魔术方法

```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: int
    y: int
    tags: list[str] = field(default_factory=list)

    @property
    def norm(self) -> float:            # 像属性一样访问：p.norm
        return (self.x ** 2 + self.y ** 2) ** 0.5

# 常用魔术方法
__init__    # 构造
__repr__    # print / 调试显示，必须 return 字符串
__eq__      # ==
__hash__    # 放进 set / 当 dict key
__len__     # len()
__iter__    # for 循环
```

---

## 四、类型提示速查

```python
x: int = 1
xs: list[int] = []
m: dict[str, int] = {}
s: set[str] = set()
pair: tuple[int, str] = (1, "a")
maybe: str | None = None            # 3.10+ 写法，推荐
either: int | str = 1

def f(a: int, b: str = "x", *args, **kwargs) -> bool:
    ...

from typing import Any, Literal, TypedDict
mode: Literal["r", "w"] = "r"
```

⭐ **核心认知**：类型提示**运行时不做检查**，它是给 `mypy` 和 `FastAPI` 看的。

```python
def add(a: int, b: int) -> int: return a + b
add("hello", "world")     # 不报错！返回 "helloworld"
```

---

## 五、我总是忘记的（自己往里加）

> 每次写代码时查过的东西，就补一条到这里。
> 记法：**「什么时候用」比「怎么写」更重要。**

- [ ] 例：`d.get(k, 0)` —— 不想让 key 不存在时抛异常就用它
- [ ]
- [ ]
- [ ]

---

## 六、容易忘的命令

```bash
# Python 环境
source .venv/bin/activate         # 激活虚拟环境
.venv/bin/python xxx.py           # 不激活也能跑
uv add 包名                        # 加依赖
uv pip install 包名                # 装到当前环境

# 检查
.venv/bin/python -m mypy xxx.py   # 类型检查
.venv/bin/ruff check .            # 代码规范
.venv/bin/ruff format .           # 自动格式化

# Git
git add -A && git commit -m "..." && git push    # 一条龙
git log --oneline -5                              # 看最近提交
git diff                                          # 看未提交的改动
```
