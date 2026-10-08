# Python 速通 · 第 1 天：心智模型与面向对象

> **面向**：有 C/C++ 基础、数据结构已学、但 Python 只停留在语法的同学
> **目标**：读完能读懂并写出 FastAPI 项目里的类定义
> **预计**：3–4 小时（含练习）

---

## 1. 从 C++ 到 Python 的心智转变

### 1.1 变量是"标签"，不是"盒子"

C++ 里 `int a = 1;` 是分配一个盒子把 1 放进去。Python 里 `a = 1` 是**创建一个对象，再把标签 a 贴上去**。

```python
a = [1, 2, 3]
b = a            # b 和 a 是两张标签，贴在同一个列表上
b.append(4)
print(a)         # [1, 2, 3, 4]   ← 不是拷贝！
```

C++ 里值赋值会拷贝，Python 里**赋值永远是贴标签**。

想要拷贝必须明说：

```python
b = a.copy()          # 浅拷贝
b = a[:]              # 浅拷贝（切片）
import copy
b = copy.deepcopy(a)  # 深拷贝
```

**浅拷贝的坑**——只拷一层：

```python
a = [[1, 2], [3, 4]]
b = a.copy()
b[0].append(99)
print(a)   # [[1, 2, 99], [3, 4]]   ← 内层还是共享的！
```

> **记住**：嵌套结构要拷贝，用 `copy.deepcopy`。

### 1.2 一切皆对象

函数是对象、类是对象、模块也是对象。所以你可以：

```python
def hello():
    print("hi")

f = hello          # 函数可以赋值给变量
f()                # hi

def run_twice(func):      # 函数可以作为参数传入
    func()
    func()

run_twice(hello)
```

**这一点极其重要**——FastAPI 的依赖注入、装饰器、回调，全都建立在这个特性上。

### 1.3 可变 vs 不可变（最重要的一张表）

| 不可变 | 可变 |
|---|---|
| `int` `float` `str` `tuple` `frozenset` `bool` `None` | `list` `dict` `set` `bytearray` 自定义类实例 |

**为什么重要**：只有不可变对象能当字典的 key / 放进 set。

```python
d = {}
d[(1, 2)] = "ok"      # ✓ tuple 不可变，可以
d[[1, 2]] = "error"   # ✗ TypeError: unhashable type: 'list'
```

**推论**：函数参数传的是标签。传可变对象进去，函数内部改了它，外面跟着变：

```python
def add_item(lst):
    lst.append("new")

my = [1]
add_item(my)
print(my)   # [1, 'new']   ← C++ 里你要传引用才会这样
```

### 1.4 `is` 和 `==` 的区别

- `==` 比较**值**（调用 `__eq__`）
- `is` 比较**身份**（是不是同一个对象）

```python
a = [1, 2, 3]
b = [1, 2, 3]
a == b    # True   值相同
a is b    # False  两个不同对象
```

**判断 `None` 永远用 `is`**：

```python
if x is None:      # ✓
    ...
if x == None:      # ✗ 别这么写
    ...
```

⚠️ 小整数缓存陷阱：

```python
a = 256; b = 256; print(a is b)   # True（CPython 缓存 -5~256）
a = 257; b = 257; print(a is b)   # 可能 False
```

**结论：永远不要用 `is` 比较数值。**

---

## 2. 数据结构速查

| 结构 | 写法 | 有序 | 可变 | 查找复杂度 | 典型用途 |
|---|---|---|---|---|---|
| `list` | `[1, 2]` | ✅ | ✅ | O(n) | 有序集合、栈 |
| `tuple` | `(1, 2)` | ✅ | ❌ | O(n) | 不可变记录、字典 key |
| `dict` | `{"a": 1}` | ✅(插入序) | ✅ | **O(1)** | 映射、计数、缓存 |
| `set` | `{1, 2}` | ❌ | ✅ | **O(1)** | 去重、存在性判断 |
| `collections.deque` | `deque([1])` | ✅ | ✅ | O(n) | 双端队列、BFS |

**高频操作**：

```python
# dict
d = {"a": 1}
d.get("b", 0)          # 取不到返回默认值，不抛异常 ← 比 d["b"] 安全
d.setdefault("c", [])  # 不存在就设默认值（分组常用）
for k, v in d.items(): # 同时遍历键值
    pass

# set
s = {1, 2, 3}
s & {2, 3, 4}   # 交集 {2, 3}
s | {4}         # 并集 {1, 2, 3, 4}
s - {1}         # 差集

# 计数
from collections import Counter
Counter("hello")   # Counter({'l': 2, 'h': 1, 'e': 1, 'o': 1})

# 默认字典（避免 KeyError）
from collections import defaultdict
groups = defaultdict(list)
groups["a"].append(1)   # 不用先判断 key 存在
```

> **刷题提示**：Python 的 `dict` / `set` 是 O(1) 的，很多在 C++ 里要手写哈希表的题，Python 里一行就能解决。这是你的优势。

---

## 3. 函数

### 3.1 参数形式

```python
def f(a, b=2, *args, **kwargs):
    print(a, b, args, kwargs)

f(1)                      # 1 2 () {}
f(1, 3)                   # 1 3 () {}
f(1, 3, 4, 5)             # 1 3 (4, 5) {}
f(1, 3, 4, x=9)           # 1 3 (4,) {'x': 9}
f(1, b=3)                 # 关键字传参
```

C++ 里没有 `**kwargs`，这是 Python 非常常用的模式（装饰器、FastAPI 全靠它）。

### 3.2 ⚠️ 经典陷阱：可变默认参数

```python
def add(item, lst=[]):     # ✗ 危险！
    lst.append(item)
    return lst

add(1)   # [1]
add(2)   # [1, 2]   ← 你以为会是 [2]
add(3)   # [1, 2, 3]
```

**原因**：默认值在函数**定义时**求值一次，之后所有调用共享同一个列表对象。

**正确写法**：

```python
def add(item, lst=None):
    if lst is None:
        lst = []
    lst.append(item)
    return lst
```

> 这个坑面试也爱问，务必记牢。

### 3.3 作用域：LEGB

查找顺序 **L**ocal → **E**nclosing → **G**lobal → **B**uilt-in

```python
x = "global"

def outer():
    x = "enclosing"
    def inner():
        # x = "local"
        print(x)      # 没有 local 就找 enclosing
    inner()

outer()   # enclosing
```

要修改外层变量，得用 `global` / `nonlocal` 声明：

```python
count = 0
def inc():
    global count      # 不写这行会报 UnboundLocalError
    count += 1
```

### 3.4 闭包（装饰器的基础）

```python
def make_counter():
    count = 0
    def counter():
        nonlocal count
        count += 1
        return count
    return counter

c = make_counter()
print(c(), c(), c())   # 1 2 3
```

⚠️ **late binding 陷阱**——闭包捕获的是变量，不是值：

```python
funcs = [lambda: i for i in range(3)]
print([f() for f in funcs])   # [2, 2, 2]  ← 不是 [0, 1, 2]！

# 修复：用默认参数把当前值绑住
funcs = [lambda i=i: i for i in range(3)]
print([f() for f in funcs])   # [0, 1, 2]
```

---

## 4. 面向对象

### 4.1 基本形态

```python
class Animal:
    species = "unknown"          # 类属性，所有实例共享

    def __init__(self, name):    # 构造函数；self 相当于 C++ 的 this，但必须显式写
        self.name = name         # 实例属性

    def speak(self):
        return f"{self.name} makes a sound"

    def __str__(self):           # 相当于 toString / operator<<
        return f"Animal({self.name})"


class Dog(Animal):               # 继承
    def __init__(self, name, breed):
        super().__init__(name)   # 调父类构造函数
        self.breed = breed

    def speak(self):             # 重写
        return f"{self.name} barks"


d = Dog("旺财", "柴犬")
print(d.speak())     # 旺财 barks
print(d)             # Animal(旺财)   ← 调用了 __str__
print(isinstance(d, Animal))   # True
```

### 4.2 ⚠️ 没有真正的私有

```python
class A:
    def __init__(self):
        self.public = 1
        self._protected = 2      # 约定：内部用，别从外面碰
        self.__private = 3       # 名字改写为 _A__private，仍可访问

a = A()
print(a._protected)          # 能访问，只是约定
print(a._A__private)         # 也能访问（不推荐）
```

**结论**：Python 靠约定，不靠访问控制。别指望封装来保护数据。

### 4.3 常用魔术方法

```python
class Vector:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):                    # 调试用，给开发看
        return f"Vector({self.x}, {self.y})"

    def __str__(self):                     # 打印用，给用户看
        return f"({self.x}, {self.y})"

    def __eq__(self, other):               # ==
        return self.x == other.x and self.y == other.y

    def __hash__(self):                    # 放进 set / 当 dict key 需要
        return hash((self.x, self.y))

    def __add__(self, other):              # +
        return Vector(self.x + other.x, self.y + other.y)

    def __len__(self):                     # len()
        return 2

    def __iter__(self):                    # for 循环
        yield self.x
        yield self.y
```

**在 FastAPI 项目里你会天天见到 `__init__`、`__repr__`、`__eq__`。**

### 4.4 `@property`：像属性一样访问方法

```python
class Circle:
    def __init__(self, r):
        self._r = r

    @property
    def area(self):                 # 访问时不用写括号
        return 3.14159 * self._r ** 2

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, value):             # 赋值时做校验
        if value < 0:
            raise ValueError("半径不能为负")
        self._r = value

c = Circle(2)
print(c.area)     # 12.566...  ← 注意没有 ()
c.r = 5           # 走 setter
```

### 4.5 `@dataclass`：少写样板代码（强烈推荐）

```python
from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int
    label: str = "origin"     # 带默认值

p = Point(1, 2)
print(p)              # Point(x=1, y=2, label='origin')
print(p == Point(1, 2, "origin"))   # True ← 自动生成 __eq__

# 不可变版本
@dataclass(frozen=True)
class Config:
    host: str
    port: int

# 冻结后能当 dict key
d = {Config("localhost", 8080): "dev"}
```

**等价于 C++ 里手写构造函数 + `operator==` + `toString`，一行搞定。**

### 4.6 类方法 / 静态方法

```python
class User:
    def __init__(self, name):
        self.name = name

    def instance_method(self):        # 普通方法，第一个参数是实例
        return self.name

    @classmethod
    def from_dict(cls, data):         # 类方法，第一个参数是类；常用作备用构造器
        return cls(data["name"])

    @staticmethod
    def is_valid_name(name):          # 静态方法，不碰类也不碰实例
        return len(name) > 0


u = User.from_dict({"name": "benfu"})   # 备用构造器模式
```

> **在 FastAPI / Pydantic 项目里，`@classmethod` 的备用构造器模式很常见。**

---

## 5. 第 1 天练习

做完把代码提交到 `python/exercises/` 目录下。

**① 心智模型**
```python
a = [[1, 2], [3, 4]]
b = a.copy()
b[0].append(5)
print(a)      # 输出什么？为什么？
```
用代码验证你的答案，并写一行注释解释。

**② 类与魔术方法**
写一个 `Fraction` 分数类，支持：
- `Fraction(1, 2)` 构造
- `+` 加法（`__add__`），结果自动约分
- `==` 比较（`__eq__`）
- `print` 输出 `1/2`（`__repr__`）

**③ dataclass**
用 `@dataclass` 重写一个 `Student(name, age, scores: list)`，要求：
- 自动生成 `__eq__` 和 `__repr__`
- 加一个 `@property average` 返回平均分

**④ 可变默认参数**
解释下面这段代码为什么输出 `[1, 2, 3]`，并改成正确写法：
```python
def collect(x, acc=[]):
    acc.append(x)
    return acc

print(collect(1), collect(2), collect(3))
```

---

## 6. 自查：这些你都会了吗

- [ ] 能说清"变量是标签"意味着什么，以及什么时候必须用 `deepcopy`
- [ ] 知道哪些类型可变、哪些不可变，以及为什么只有不可变能当 dict key
- [ ] 知道 `is` 和 `==` 的区别，以及判断 `None` 该用哪个
- [ ] 能默写可变默认参数的正确写法
- [ ] 能解释闭包的 late binding 陷阱
- [ ] 能写出带 `__init__` / `__repr__` / `__eq__` / `__add__` 的类
- [ ] 会用 `@dataclass` 和 `@property`
- [ ] 知道 `@classmethod` 和 `@staticmethod` 的区别

全部打勾 → 进入第 2 天。
