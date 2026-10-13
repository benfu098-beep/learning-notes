# Python 速通 · 第 3 天：asyncio 异步编程

> 📌 **并发下载器**和**生产者-消费者**两个模式的详细图解，见 [03b-asyncio-patterns.md](03b-asyncio-patterns.md)

> **目标**：理解事件循环，能写出正确的异步代码，并知道 FastAPI 里 `async def` 和 `def` 该用哪个
> **预计**：4–5 小时（含练习）
>
> **为什么必须学**：FastAPI 是异步框架。不懂 asyncio，你写出的服务会在高并发下静默变慢，
> 而且面试问「Python 怎么处理高并发」时你答不上来。

---

## 1. 先搞清楚：什么时候需要异步

任务分两类：

| 类型 | 特征 | 例子 | 该怎么优化 |
|---|---|---|---|
| **IO 密集** | 大部分时间在**等** | 网络请求、读写数据库、读文件 | ✅ **asyncio** / 多线程 |
| **CPU 密集** | 大部分时间在**算** | 图像处理、加解密、大矩阵运算 | ✅ **多进程** |

**关键认知**：异步不能加速计算，它只是**在等待时不浪费 CPU**。

> 你的项目 A（LLM 网关）是典型 IO 密集型：等上游模型返回、等数据库、等 Redis。
> 所以 asyncio 用得非常值。

### 1.1 同步代码的困境

```python
import time, requests

start = time.perf_counter()
for url in ["https://a.com", "https://b.com", "https://c.com"]:
    requests.get(url)          # 每个请求都要等 1 秒
print(f"耗时 {time.perf_counter() - start:.2f}s")   # 约 3 秒
```

三个请求之间**毫无依赖**，本来可以同时发出去，但同步代码只能一个一个等。这就是异步要解决的问题。

---

## 2. 事件循环：asyncio 的心脏

**核心模型**：单线程 + 一个事件循环（event loop）+ 一堆任务。

```
事件循环不断循环：
  1. 看有没有任务可以推进（比如网络数据到了）
  2. 有 → 执行它，直到它遇到 await 主动让出
  3. 没有 → 等待（但不占 CPU）
```

**关键点**：任务是**自己主动让出**控制权的。当代码遇到 `await`，它会告诉事件循环"我要等了，你先去跑别人"。

> ⚠️ 这也意味着：**如果一个任务不让出，整个循环就卡死了。** 这是新手最大的坑（见第 6 节）。

---

## 3. `async def` / `await` 基本用法

```python
import asyncio

async def say(msg, delay):
    await asyncio.sleep(delay)      # 异步版的 sleep：等待时让出控制权
    print(msg)

async def main():
    await say("hello", 1)           # await = 等待这个协程执行完
    await say("world", 1)

asyncio.run(main())                 # 启动事件循环的入口
```

**几个概念区分**：

| 名词 | 是什么 |
|---|---|
| `async def` 定义的函数 | **协程函数**，调用它不会执行，只返回协程对象 |
| 协程对象 | 一个"待执行的活" |
| `await` | 等待一个协程/可等待对象完成 |
| `Task` | 被事件循环**调度**的协程（可以并发跑） |
| 事件循环 | 调度器 |

⚠️ **常见错误**：调用协程函数却忘了 `await`。

```python
async def main():
    say("hi", 1)          # ✗ 什么都没发生，还会警告 "coroutine was never awaited"
    await say("hi", 1)    # ✓
```

---

## 4. 并发执行：这才是异步的价值

### 4.1 `asyncio.gather` —— 最常用

```python
import asyncio, time

async def fetch(name, delay):
    await asyncio.sleep(delay)
    return f"{name} 完成"

async def main():
    start = time.perf_counter()
    results = await asyncio.gather(
        fetch("A", 1),
        fetch("B", 1),
        fetch("C", 1),
    )
    print(results)                                    # ['A 完成', 'B 完成', 'C 完成']
    print(f"耗时 {time.perf_counter() - start:.2f}s")  # 约 1.0 秒！不是 3 秒

asyncio.run(main())
```

**对比一下：**

```python
# 串行：3 秒
await fetch("A", 1)
await fetch("B", 1)
await fetch("C", 1)

# 并发：1 秒
await asyncio.gather(fetch("A", 1), fetch("B", 1), fetch("C", 1))
```

### 4.2 `asyncio.TaskGroup`（3.11+ 推荐）

比 `gather` 更安全：任一任务失败会取消其余任务，异常不会静默丢失。

```python
async def main():
    async with asyncio.TaskGroup() as tg:
        t1 = tg.create_task(fetch("A", 1))
        t2 = tg.create_task(fetch("B", 2))
    # 退出 with 时自动等待全部完成
    print(t1.result(), t2.result())
```

### 4.3 `as_completed`：谁先完成先处理

```python
async def main():
    tasks = [asyncio.create_task(fetch(n, d)) for n, d in [("A", 2), ("B", 1)]]
    for coro in asyncio.as_completed(tasks):
        print(await coro)      # 先打印 B，再打印 A
```

### 4.4 超时控制

```python
async def main():
    try:
        async with asyncio.timeout(2):        # 3.11+
            await fetch("slow", 10)
    except TimeoutError:
        print("超时了")

# 或者对单个协程
result = await asyncio.wait_for(fetch("slow", 10), timeout=2)
```

> **实战用途**：调用大模型 API 必须加超时，否则请求堆积会拖垮服务。

---

## 5. 一个真实的例子：并发下载

```python
import asyncio, time, httpx

URLS = [f"https://httpbin.org/delay/1?i={i}" for i in range(10)]

async def fetch(client, url):
    resp = await client.get(url)
    return len(resp.content)

async def main():
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as client:     # 复用连接池
        results = await asyncio.gather(*(fetch(client, u) for u in URLS))
    print(f"共 {len(results)} 个请求，耗时 {time.perf_counter() - start:.2f}s")

asyncio.run(main())
```

10 个各需 1 秒的请求，**总耗时约 1 秒**。

> 注意 `httpx.AsyncClient` 要复用，不要每次请求都新建——这对应后面项目里的连接池。

---

## 6. ⚠️ 最大的坑：阻塞事件循环

**在 `async def` 里调用同步阻塞函数，会卡死整个事件循环。**

```python
import asyncio, time

async def bad():
    time.sleep(1)          # ✗ 阻塞！这 1 秒里事件循环完全停摆

async def main():
    start = time.perf_counter()
    await asyncio.gather(bad(), bad(), bad())
    print(f"耗时 {time.perf_counter() - start:.2f}s")   # 3.00 秒 ← 说好的并发呢？
```

对比正确写法：

```python
async def good():
    await asyncio.sleep(1)     # ✓ 等待时让出控制权

async def main():
    start = time.perf_counter()
    await asyncio.gather(good(), good(), good())
    print(f"耗时 {time.perf_counter() - start:.2f}s")   # 1.00 秒 ✓
```

**把上面两段代码都跑一遍，感受这个差异——这是理解 asyncio 最快的方式。**

### 6.1 同步阻塞库怎么办

常见的同步阻塞操作：`requests.get`、`time.sleep`、`psycopg2` 查询、CPU 密集计算。

**方案一：丢到线程池**（适合 IO 阻塞）

```python
import asyncio

def blocking_io():
    import time; time.sleep(1)
    return "done"

async def main():
    result = await asyncio.to_thread(blocking_io)     # 3.9+ 推荐写法
    print(result)
```

**方案二：直接用异步版本的库**（首选）

| 同步库 | 异步替代 |
|---|---|
| `requests` | `httpx` |
| `time.sleep` | `asyncio.sleep` |
| `psycopg2` | `asyncpg` / `psycopg3` 异步模式 |
| `redis-py`（同步） | `redis.asyncio` |
| `open()` 读写文件 | `aiofiles`（或 `to_thread`） |

---

## 7. ⭐ FastAPI 实战：`async def` 还是 `def`？

**这是新手最容易踩的坑，务必记住。**

```python
import requests, httpx
from fastapi import FastAPI

app = FastAPI()

# ✅ 正确：async def 配异步库
@app.get("/async-ok")
async def async_ok():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://api.example.com")
    return resp.json()

# ❌ 危险：async def 里用同步阻塞库
@app.get("/async-bad")
async def async_bad():
    resp = requests.get("https://api.example.com")   # 阻塞整个事件循环！
    return resp.json()

# ✅ 也可以：用普通 def，FastAPI 会自动丢到线程池
@app.get("/sync-ok")
def sync_ok():
    resp = requests.get("https://api.example.com")   # 在线程池里跑，不阻塞循环
    return resp.json()
```

### 判断口诀

| 你的路由里用的库 | 该怎么写 |
|---|---|
| 异步库（`httpx` / `asyncpg` / `redis.asyncio`） | **`async def`** |
| 同步库（`requests` / `psycopg2` / 同步 `redis`） | **`def`**（让 FastAPI 丢线程池） |
| 纯 CPU 计算 | `def`，或丢给多进程 |

**最糟的情况是第三种以外你搞反了**：在 `async def` 里写 `requests.get`——单机并发能力会直接崩掉。

---

## 8. GIL 预告（W1 正式学）

你可能已经听说 Python 有 **GIL（全局解释器锁）**：同一时刻只有一个线程能执行 Python 字节码。

**由此推出的三条结论**：

1. **多线程不能加速 CPU 密集任务** —— 因为 GIL 挡着，线程只能轮流跑
2. **多线程能加速 IO 密集任务** —— 因为等 IO 时会释放 GIL
3. **asyncio 单线程也能高并发 IO** —— 因为它根本不用线程，靠事件循环调度

**所以选型是**：

| 场景 | 用什么 |
|---|---|
| 高并发网络 IO | `asyncio` |
| 少量阻塞 IO / 用同步库 | 多线程，或 `asyncio.to_thread` |
| CPU 密集 | **多进程**（`multiprocessing`） |
| 又要 IO 又要算 | 异步 + 进程池混合 |

> **面试高频问题**：「Python 的 GIL 是什么？为什么还有 asyncio？」
> 答：GIL 保证同一时刻只有一个线程执行字节码；asyncio 是单线程事件循环，
> 靠协程主动让出来做并发 IO，所以不受 GIL 影响，也没有线程切换开销。

---

## 9. 第 3 天练习

**① 感受阻塞**（最重要）
把第 6 节的两段代码分别跑一遍，**记录实际耗时**，写进注释。这是你今天必须做的第一件事。

**② 并发改造**
下面这段是串行的，改成并发，让总耗时从 3 秒降到 1 秒：
```python
import asyncio, time

async def task(name, sec):
    await asyncio.sleep(sec)
    return f"{name} done"

async def main():
    start = time.perf_counter()
    r1 = await task("A", 1)
    r2 = await task("B", 1)
    r3 = await task("C", 1)
    print(r1, r2, r3, f"耗时 {time.perf_counter()-start:.2f}s")

asyncio.run(main())
```

**③ 并发下载器**
用 `httpx.AsyncClient` 并发请求 10 个 URL，打印总耗时和成功数。加上 3 秒超时和异常处理。

**④ 生产者-消费者**
用 `asyncio.Queue` 实现：一个协程每秒生产一个数字，两个协程并发消费。

**⑤ 思考题**（写进笔记）
你的项目 A（LLM 网关）要做这些事，分别该用什么方式？
- 转发用户请求到大模型 API（流式返回）
- 从 Redis 读缓存
- 对 token 做计数统计
- 把日志写入文件

---

## 10. 自查

- [ ] 能说清 IO 密集和 CPU 密集的区别，以及各自该用什么方案
- [ ] 能画出事件循环的工作模型（等待 → 让出 → 调度）
- [ ] 能默写 `asyncio.gather` 做并发，并说清它和串行 `await` 的区别
- [ ] **能解释"阻塞事件循环"是什么，并在代码里识别出来**
- [ ] 知道同步库怎么在异步环境里用（`to_thread`）
- [ ] **能在 FastAPI 里正确判断该写 `async def` 还是 `def`**
- [ ] 能说出 GIL 是什么，以及为什么 asyncio 不受它影响

全部打勾 → **地基阶段完成，进入 W2：FastAPI 与 Web 核心**。
