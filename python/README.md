# Python 速通讲义

> 面向**有 C/C++ 基础、数据结构已学、Python 只停留在语法**的同学编写。
> 只讲和 C++ 不同的地方，以及 FastAPI 项目真正会用到的部分。
>
> 配套周期：**W0–W1（10/08–10/18）**，每天一份，每份 3–5 小时。

## 目录

| 天 | 讲义 | 内容 | 关键产出 |
|---|---|---|---|
| 第 1 天 | [01-mindset-and-oop.md](01-mindset-and-oop.md) | 心智模型、数据结构、函数、面向对象 | 能写出带魔术方法的类 |
| 第 2 天 | [02-advanced-and-typing.md](02-advanced-and-typing.md) | 推导式、生成器、装饰器、上下文管理器、**类型提示** | 能写装饰器 + 类型注解 |
| 第 3 天 | [03-asyncio.md](03-asyncio.md) | 事件循环、`async/await`、并发、**FastAPI 实战判断** | 理解阻塞事件循环 |

## 学完你应该能

- 读懂并写出 FastAPI 项目里的类定义、装饰器、类型注解
- 正确使用 `asyncio.gather` 做并发，并识别"阻塞事件循环"的代码
- 判断一个 FastAPI 路由该写 `async def` 还是 `def`
- 说出 GIL 是什么，以及为什么 asyncio 不受它影响

## 方法建议

1. **每份讲义里的代码都要亲手敲一遍**，不要只读
2. **做每份末尾的练习**，提交到 `python/exercises/` 目录
3. 对照最后一节的自查清单，**全部打勾再进下一天**
4. 遇到不懂的先记下来，攒够三个一起问

## 练习提交规范

```
python/exercises/
├── day1_fraction.py
├── day2_retry_decorator.py
└── day3_concurrent_fetch.py
```

每份代码开头用注释写：**这道题考什么、我踩了什么坑**。
