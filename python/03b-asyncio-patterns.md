# asyncio 实战模式补充讲解

> 补充 [03-asyncio.md](03-asyncio.md) 里讲得不够细的两个模式：
> **并发下载器** 和 **生产者-消费者**。
>
> 这两块之所以难，是因为它们不是"语法"，是**模式**。
> 下面用图和逐行走读讲清楚。

---

# 一、先建立一个心智模型：餐厅

```
   厨师（生产者）          传菜窗口（队列）          服务员（消费者）
     做菜 ──────────▶   [菜1][菜2][菜3]  ──────────▶  端给客人
     继续做下一道         最多放 N 个                有空就来取
```

**关键**：厨师**不用等**服务员端走才做下一道菜。窗口（队列）让两边解耦。

并发下载器是同一个模型，只是角色换了：

```
   你（主协程）           10 个下载任务（同时在等网络）
     gather ──────────▶   任务1: await 网络 ▓▓▓▓░░░░
                          任务2: await 网络 ░░▓▓▓▓░░
                          任务3: await 网络 ░░░░▓▓▓▓
```

---

# 二、`await` 内部到底发生了什么（理解一切的关键）

```python
resp = await client.get(url)
```

这一行实际做了 5 件事：

```
① 把 HTTP 请求写进 socket            （微秒级，很快）
② 遇到 await → 把控制权【交还】给事件循环     ★ 关键
③ 事件循环转头去跑别的任务（比如另外 9 个下载）
④ 网络数据到达 → 事件循环【唤醒】本任务
⑤ 从 ② 的位置继续往下，拿到 resp
```

**所以并发的本质不是"同时在做"，而是"在等待的时候不闲着"。**

## 并发 vs 串行：时间轴对比

```
【串行】总耗时 = 1 + 1 + 1 = 3 秒
时间 →
任务1: [发请求]▓▓等待▓▓[收到][处理]
任务2:                    [发请求]▓▓等待▓▓[收到][处理]
任务3:                                       [发请求]▓▓等待▓▓[收到]
                                          ↑ 等待段完全不重叠

【并发】总耗时 ≈ max(1,1,1) = 1 秒
时间 →
任务1: [发请求]▓▓等待▓▓[收到][处理]
任务2:    [发请求]▓▓等待▓▓[收到][处理]
任务3:       [发请求]▓▓等待▓▓[收到][处理]
              ↑ 三个"等待"段重叠在一起
```

**看懂了这张图，你就懂了 asyncio 的全部价值。**

---

# 三、模式 1：并发下载器

## 3.1 为什么只建【一个】client

```python
# ❌ 慢：每个请求都新建 client
for url in urls:
    async with httpx.AsyncClient() as client:
        await client.get(url)

# ✅ 快：一个 client，所有请求复用
async with httpx.AsyncClient(timeout=3.0) as client:
    results = await asyncio.gather(*(fetch_one(client, u) for u in urls))
```

原因有两条：

1. **HTTP 请求要先三次握手建立 TCP 连接**。`AsyncClient` 内部维护**连接池**，复用连接能省掉这个开销。
2. **每个 client 都占着 socket**，建太多会耗尽文件描述符（Mac 默认上限不高）。

> 类比：一个是每次打电话都重新办一张手机卡，一个是办一张卡打 10 个电话。

## 3.2 异常处理：为什么不能在 gather 外面统一 try

先看**错误**写法：

```python
async def fetch_one(client, url):
    resp = await client.get(url)          # 网络异常在这抛
    resp.raise_for_status()               # 404/500 在这抛
    return resp.json()

results = await asyncio.gather(*(fetch_one(c, u) for u in URLS))
```

只要**任何一个** URL 失败：

```
① gather 立刻把异常抛出去 → 整个程序崩掉
② 其他 9 个任务【已经在跑了】，但它们的结果全部丢失
③ 你甚至不知道是哪个 URL 失败的
```

**正确**写法——在 `fetch_one` 内部就把异常"吃掉"，转成返回值：

```python
async def fetch_one(client: httpx.AsyncClient, url: str) -> dict:
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return {"url": url, "ok": True, "bytes": len(resp.content)}
    except Exception as e:
        return {"url": url, "ok": False, "error": f"{type(e).__name__}: {e}"}
```

**核心思想：把「失败」也当作一种正常结果返回**，而不是让它中断整个流程。

> 另一种写法是 `asyncio.gather(..., return_exceptions=True)`——异常会作为返回值出现在结果列表里。
> 两种都行，但"在函数内部处理"更清晰，因为你能完全控制返回的数据结构。

## 3.3 逐行走读

```python
async def fetch_all_concurrent() -> tuple[list, float]:
    t0 = time.perf_counter()                          # 秒表开始
    async with httpx.AsyncClient(timeout=3.0) as client:
        #    ↑ 建一个 client，进 with 时创建，出 with 时自动关闭连接
        async with asyncio.timeout(3):
            #    ↑ 整体超时保护：3 秒还没全部跑完就全部取消
            results = await asyncio.gather(
                *(fetch_one(client, u) for u in URLS)
            )
            #    ↑ 星号把生成器的 10 个协程"摊开"传进去
            #      gather 同时启动它们，全部完成后按【传入顺序】返回
    return list(results), time.perf_counter() - t0
```

**`*(...)` 这个星号是干什么的？**

```python
asyncio.gather(fetch_one(c, u1), fetch_one(c, u2), ..., fetch_one(c, u10))
# 等价于
asyncio.gather(*(fetch_one(c, u) for u in URLS))
```

星号把"一个可迭代对象"摊开成"一堆位置参数"。第 2 天讲函数参数时见过 `*args`，这里是同一个东西的用法。

---

# 四、模式 2：生产者-消费者

## 4.1 不用队列会怎样

```python
async def producer():
    for i in range(5):
        await asyncio.sleep(0.5)
        await handle(i)          # ❌ 直接处理，没有缓冲
```

问题：**生产者必须等处理完才能继续生产。两边被绑死。**

用队列之后：

```python
async def producer(queue):
    for i in range(5):
        await asyncio.sleep(0.5)
        await queue.put(i)       # ✅ 只管生产，放进去就走

async def consumer(queue):
    while True:
        item = await queue.get() # ✅ 只管消费
        await handle(item)
```

生产者不用管消费者忙不忙，消费者不用管生产者什么时候来。**队列就是中间的缓冲区。**

## 4.2 这个模式在真实项目里到处都是

| 场景 | 生产者 | 队列 | 消费者 |
|---|---|---|---|
| Web 服务器 | 接收请求 | 请求队列 | worker 线程池 |
| 爬虫 | 解析出 URL | URL 队列 | 下载协程 |
| **你的 LLM 网关** | 进来的请求 | 请求队列 | 限制并发数的调用协程 |
| 日志系统 | 业务代码 | 日志队列 | 异步写盘协程 |

## 4.3 sentinel：消费者怎么知道"没货了"

消费者 `await queue.get()` 时，如果队列空着，它会**一直等**。它怎么知道该退出了？

```python
# ❌ 不可靠：队列空了不代表结束，生产者可能只是暂时慢
if queue.empty():
    break

# ✅ 用一个【约定值】明确告诉消费者"收工"
item = await queue.get()
if item is None:        # None 就是约定的结束信号
    break
```

这个约定值叫 **sentinel（哨兵）**。为什么选 `None`？因为它是不可变对象、语义清晰、平时不会出现在正常数据里。

> ⚠️ 判断用 `is None`，不是 `== None`（第 1 天讲过）。

## 4.4 ⚠️ 为什么 2 个消费者要放 2 个 `None`

每个消费者都在**独立地**执行 `await queue.get()`。往队列放进 1 个 `None`，只有 1 个消费者能抢到：

```
队列: [None]

消费者-1: get() → None → 退出 ✅
消费者-2: get() → 队列空了 → 继续等…… ❌ 永远卡住！
```

整个程序会**永远挂住不退出**。所以：

```python
for _ in range(CONSUMER_COUNT):     # 有几个消费者就放几个
    await queue.put(None)
```

## 4.5 完整流程图

```
时间 →

生产者:   put(0)  put(1)  put(2)  put(3)  put(4)   put(None)×2
           └0.5s┘  └0.5s┘  └0.5s┘  └0.5s┘  └0.5s┘
             ↓       ↓       ↓       ↓       ↓
队列:      [0] ──▶ [1] ──▶ [2] ──▶ [3] ──▶ [4] ──▶ [None, None]
             ↓       ↓       ↓       ↓       ↓
消费者-1:  get(0) 处理.3s   get(2) 处理.3s   get(4) 处理.3s   get(None)→退出
消费者-2:      get(1) 处理.3s   get(3) 处理.3s         get(None)→退出
                 ↑ 两个消费者交替取，所以输出是交错的
```

## 4.6 逐行走读

```python
async def producer(queue: asyncio.Queue) -> None:
    for i in range(PRODUCE_COUNT):
        await asyncio.sleep(0.5)      # 模拟生产耗时
        await queue.put(i)            # ★ put 是异步的：队列满时会等待
        print(f"  [生产者] 放入 {i}")

    for _ in range(CONSUMER_COUNT):   # ★ 每个消费者一个结束信号
        await queue.put(None)

async def consumer(name: str, queue: asyncio.Queue) -> list:
    got = []
    while True:
        item = await queue.get()      # ★ get 也是异步的：队列空时会等待
        if item is None:              # ★ 收到结束信号
            break
        got.append(item)
        await asyncio.sleep(0.3)      # 模拟处理耗时
    return got
```

**为什么 `put` 和 `get` 都要 `await`？**

| 方法 | 什么时候会"等" |
|---|---|
| `await queue.put(x)` | 队列**满**了，等消费者取走腾出空间 |
| `await queue.get()` | 队列**空**了，等生产者放东西进来 |

`asyncio.Queue()` 默认**没有容量上限**，所以 `put` 基本不会等。但写成 `asyncio.Queue(maxsize=10)` 就有了背压（backpressure）——生产太快会被挡住，防止内存爆掉。

> **背压**是个重要概念：让快的生产者和慢的消费者自动平衡。你在项目 A 里限制模型并发数时会用到。

---

# 五、这两个模式在你项目里的位置

| 模式 | 你用在哪 |
|---|---|
| **并发下载器** | 项目 B 里并发调用 embedding API；批量文档处理 |
| **生产者-消费者** | 项目 A 里限制同时调用大模型的请求数；项目 B 里文档解析任务队列 |

**面试时**，如果被问到"你怎么处理大量并发请求"，你可以说：

> "用 asyncio 做 IO 并发，`gather` 同时发起请求；需要限流或解耦的地方用 `asyncio.Queue` 做生产者-消费者，配合 `maxsize` 实现背压，防止上游打爆下游。"

这段话说出来，比背概念有说服力得多。

---

# 六、一句话总结

| 概念 | 本质 |
|---|---|
| `await` | 我要等了，控制权还给你 |
| **并发** | 等待时**不闲着**，不是"同时在做" |
| `gather` | 同时启动 N 个任务，按**传入顺序**返回结果 |
| 连接池 | 复用 TCP 连接，别每次新建 client |
| 队列 | 生产者和消费者之间的**缓冲带** |
| sentinel | 用约定值告诉消费者"收工"（N 个消费者要 N 个） |
| 背压 | `maxsize` 让快的生产者被慢的消费者自动拖住 |
