# 第 3 天练习 ⑤：思考题

> **用你自己的话回答，不要抄讲义。** 这几道题面试真的会问。
> 写完提交，这份文件就是你面试前的复习材料。

---

## 1. IO 密集 vs CPU 密集

你的项目 A（LLM 网关）要做下面这些事，分别该用什么方式？

| 任务 | 该用什么 | 为什么 |
|---|---|---|
| 转发用户请求到大模型 API（流式返回） | | |
| 从 Redis 读缓存 | | |
| 对 token 做计数统计 | | |
| 把日志写入文件 | | |
| 对一批文本做本地 embedding 计算 | | |

**候选**：`asyncio` / 多线程 / 多进程 / 直接同步写

---

## 2. 阻塞事件循环

在 FastAPI 里，下面两种写法哪种是**对的**？为什么？

```python
import requests
from fastapi import FastAPI

app = FastAPI()

@app.get("/a")
async def a():
    return requests.get("https://api.example.com").json()

@app.get("/b")
def b():
    return requests.get("https://api.example.com").json()
```

**我的回答：**




---

## 3. GIL

用你自己的话回答：

- GIL 是什么？
- 为什么多线程不能加速 CPU 密集任务？
- 为什么 asyncio 不受 GIL 影响？

**我的回答：**




---

## 4. 一句话总结（面试模拟）

如果面试官问：**「Python 怎么处理高并发？」**

用 3 句话以内回答：

**我的回答：**




---

## 5. 自我检查

- [ ] 我能解释「阻塞事件循环」是什么，并能在代码里认出来
- [ ] 我知道 FastAPI 里什么时候写 `async def`、什么时候写 `def`
- [ ] 我能说出 GIL 是什么，以及 asyncio 为什么不受它影响
- [ ] 我能默写 `asyncio.gather` 的用法

全部打勾 → **Day 3 完成，地基阶段结束，可以进入 W2 了。**
