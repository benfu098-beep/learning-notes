# W2 讲义：FastAPI 入门

> **周期**：W2（10/19–10/25）
> **目标**：从零搭出一个**有规范结构、能跑起来**的后端服务
> **前置**：Day 3 的 asyncio（异步路由要用到）
> **产出**：一个分层的 FastAPI 项目骨架

---

## 0. 先建立认知：你在造什么

还记得那个聊天 demo 吗？它的结构是：

```
浏览器（前端）──HTTP──▶ FastAPI 服务（后端）──▶ 返回 JSON
```

**W2 就是把那个 demo 变成"正经项目"**：加上分层结构、参数校验、错误处理、日志、依赖注入。

面试官看你的后端项目，第一眼看的就是：
- 目录结构清不清晰
- 参数校验做没做
- 错误处理统一不统一

**这三件事，就是 W2 的全部内容。**

---

## 1. 为什么是 FastAPI

| 对比项 | FastAPI | Flask | Django |
|---|---|---|---|
| 异步支持 | ✅ 原生 | ⚠️ 有限 | ⚠️ 有限 |
| 自动 API 文档 | ✅ 自带 `/docs` | ❌ 要插件 | ❌ 要插件 |
| 参数校验 | ✅ 靠类型提示自动 | ❌ 手写 | ⚠️ 靠 Form |
| 性能 | 高（Starlette + uvloop） | 中 | 中 |
| 适合场景 | **API 服务 / AI 应用** | 小工具 | 全栈网站 |

**对你的方向来说，FastAPI 是对的选择**：AI 应用几乎都是"前端调后端 API"，而 FastAPI 的异步 + 自动校验 + 自动文档正好对口。

---

## 2. 最小可运行服务

```python
# main.py
from fastapi import FastAPI

app = FastAPI(title="我的服务", version="0.1")

@app.get("/")
async def root():
    return {"status": "ok"}
```

```bash
.venv/bin/uvicorn main:app --reload
#                                        ↑ 改代码自动重启（开发时用）
```

打开 http://127.0.0.1:8000/docs —— **API 文档自动生成了，你一行都没写。**

---

## 3. 路由：三种参数（最重要的基础）

### 3.1 路径参数 —— 标识"哪个资源"

```python
@app.get("/users/{user_id}")
async def get_user(user_id: int):        # ← 类型注解让它自动转成 int
    return {"user_id": user_id}
```

- `GET /users/1` → `user_id = 1`（int）
- `GET /users/abc` → **自动返回 422**，你不用写一行校验代码

### 3.2 查询参数 —— 过滤、分页、排序

```python
@app.get("/items")
async def list_items(
    skip: int = 0,                  # 有默认值 → 可选
    limit: int = 10,
    q: str | None = None,           # 允许 None → 可选
):
    return {"skip": skip, "limit": limit, "q": q}
```

- `GET /items` → 用默认值
- `GET /items?skip=5&limit=3` → 覆盖默认值
- `GET /items?limit=abc` → **自动 422**

**带约束的写法（推荐）**：

```python
from typing import Annotated
from fastapi import Query

@app.get("/items")
async def list_items(
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    #                    ↑ 1 <= limit <= 100，超了自动 422
):
    ...
```

### 3.3 请求体 —— 提交数据（POST/PUT）

```python
from pydantic import BaseModel

class ItemIn(BaseModel):
    name: str
    price: float

@app.post("/items", status_code=201)
async def create_item(item: ItemIn):     # ← 参数是 Pydantic 模型 = 请求体
    return {"created": item.model_dump()}
```

- 发 `{"name":"book","price":30}` → 正常
- 发 `{"name":"book"}` → **自动 422**（price 必填）
- 发 `{"name":"book","price":"abc"}` → **自动 422**（类型错）

### 3.4 怎么选？一句话判断

| 你想表达 | 用哪种 |
|---|---|
| "操作**哪一个**资源" | 路径参数 `/users/{id}` |
| "**可选**的过滤/分页条件" | 查询参数 `?limit=10` |
| "**提交一份**结构化的数据" | 请求体（Pydantic 模型） |

---

## 4. Pydantic：类型提示变成功能

### 4.1 为什么必须用它

上一节你已经看到效果：**写了类型注解，校验、转换、文档全自动**。

这不是可选的风格问题——**FastAPI 的核心机制就是读 Pydantic 模型**。不写模型，你就要手写一堆 `if not isinstance(...)`。

### 4.2 字段约束（Field）

```python
from pydantic import BaseModel, Field

class UserIn(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    tags: list[str] = Field(default_factory=list)     # ← 可变默认值的老坑（Day 1 学过）
```

### 4.3 嵌套模型

```python
class Address(BaseModel):
    city: str
    street: str

class UserIn(BaseModel):
    name: str
    address: Address           # ← 模型可以嵌套模型
```

### 4.4 响应模型（重要，防止数据泄露）

```python
class UserOut(BaseModel):
    id: int
    name: str
    # 注意：没有 password 字段

@app.get("/users/{uid}", response_model=UserOut)
async def get_user(uid: int):
    return {"id": uid, "name": "benfu", "password": "secret123"}
    #                                    ↑ 会被自动过滤掉，不会返回给前端
```

**`response_model` 的作用：只返回你声明的字段。** 这是防止把密码、内部字段泄露出去的关键手段。

### 4.5 三个常用方法

```python
user = UserIn(name="a", age=20)
user.model_dump()          # → dict
user.model_dump_json()     # → JSON 字符串
UserIn.model_validate({...})   # dict → 模型
```

---

## 5. 依赖注入 `Depends`

### 5.1 解决什么问题

假设 10 个接口都需要做同一件事：**校验 token、拿当前用户**。

不注入的话，每个接口都要抄一遍：

```python
@app.get("/a")
async def a(token: str = Header(...)):
    user = verify_token(token)        # ← 重复
    ...

@app.get("/b")
async def b(token: str = Header(...)):
    user = verify_token(token)        # ← 又抄一遍
    ...
```

用 `Depends` 抽出来：

```python
from fastapi import Depends, Header, HTTPException

async def current_user(token: str = Header(...)) -> str:
    user = verify_token(token)
    if not user:
        raise HTTPException(401, "认证失败")
    return user

@app.get("/a")
async def a(user: str = Depends(current_user)):    # ← 一行搞定
    return {"user": user}

@app.get("/b")
async def b(user: str = Depends(current_user)):
    return {"user": user}
```

### 5.2 实战：数据库会话

W3 你会用到这个模式：

```python
async def get_db():
    async with SessionLocal() as session:
        yield session                  # ← 用 yield 做清理（Day 2 学过）

@app.get("/users")
async def list_users(db = Depends(get_db)):
    ...
```

### 5.3 依赖可以嵌套

```python
async def get_db(): ...
async def get_current_user(db = Depends(get_db)): ...   # ← 依赖里再用依赖
async def get_admin(user = Depends(get_current_user)): ...

@app.get("/admin")
async def admin(user = Depends(get_admin)):
    ...
```

**FastAPI 会自动解析依赖树**，同一个请求内相同依赖只执行一次（有缓存）。

---

## 6. 错误处理与统一响应

### 6.1 抛业务异常

```python
from fastapi import HTTPException

raise HTTPException(status_code=404, detail="用户不存在")
# → 前端收到 {"detail": "用户不存在"}
```

### 6.2 全局异常处理器（统一格式）

```python
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"code": 400, "message": str(exc), "data": None},
    )
```

### 6.3 统一响应体（面试加分项）

真实项目里，所有接口返回同一个结构：

```python
class Resp(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None
```

好处：前端只需要写一套处理逻辑。

### 6.4 中间件：记录每个请求的耗时

```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time(request: Request, call_next):
    t0 = time.perf_counter()                 # 🕐 秒表（Day 3 学过）
    response = await call_next(request)
    cost = time.perf_counter() - t0
    response.headers["X-Process-Time"] = f"{cost:.4f}"
    print(f"{request.method} {request.url.path} → {response.status_code}  {cost*1000:.1f}ms")
    return response
```

---

## 7. 项目结构：为什么要分层

### 7.1 一个文件写 2000 行的下场

- 找代码靠搜索，改一处怕影响十处
- 没法写单元测试
- 面试官打开一看就关掉了

### 7.2 推荐结构（W2 就用这个）

```
app/
├── main.py              # 入口：创建 app、注册路由和中间件
├── core/
│   ├── config.py        # 配置（从环境变量读）
│   └── exceptions.py    # 自定义异常 + 全局处理器
├── models/              # Pydantic 模型（请求/响应结构）
│   ├── user.py
│   └── item.py
├── routers/             # 路由层：只管接收参数、返回结果
│   ├── users.py
│   └── items.py
├── services/            # 业务逻辑层：真正的处理逻辑
│   └── user_service.py
└── dependencies/        # 依赖：get_db、current_user
    └── auth.py
```

### 7.3 每层职责（一句话）

| 层 | 职责 | 不该做什么 |
|---|---|---|
| `routers/` | 接参数、调 service、返回结果 | ❌ 不写业务逻辑、不直接操作数据库 |
| `services/` | 业务逻辑、编排 | ❌ 不碰 HTTP 相关的东西 |
| `models/` | 数据结构定义 | ❌ 不写逻辑 |
| `dependencies/` | 复用逻辑（认证、DB 会话） | ❌ 不写业务 |

**为什么要这样分？** 因为 W6 的项目 A 会有几十个接口。现在养成习惯，后面才不会一团乱。

### 7.4 循环导入怎么避免

```python
# ❌ routers/users.py 里 from app.main import app  → 循环导入
# ✅ 用 APIRouter
from fastapi import APIRouter
router = APIRouter(prefix="/users", tags=["用户"])

@router.get("/{uid}")
async def get_user(uid: int): ...

# main.py 里统一注册
from app.routers import users
app.include_router(users.router)
```

---

## 8. `async def` vs `def`（复习 + 实战）

Day 3 学过，这里再强调一次，因为 W2 天天要用：

| 接口里用的库 | 写什么 |
|---|---|
| 异步库（`httpx` / `asyncpg` / `redis.asyncio`） | **`async def`** |
| 同步库（`requests` / `psycopg2` / 同步 `redis`） | **`def`**（FastAPI 自动丢线程池） |
| 纯 CPU 计算 | `def`，或丢进程池 |

**最糟的错误**：在 `async def` 里调 `requests.get()` —— 单机并发能力直接崩掉。

---

## 9. 调试工具

```bash
# 1. 交互式文档（最好用）
open http://127.0.0.1:8000/docs

# 2. curl
curl http://127.0.0.1:8000/users/1
curl -X POST http://127.0.0.1:8000/items \
     -H "Content-Type: application/json" \
     -d '{"name":"book","price":30}'

# 3. TestClient（写测试用，不用启动服务器）⭐
#    你的练习文件就是用它自测的
from fastapi.testclient import TestClient
client = TestClient(app)
assert client.get("/users/1").status_code == 200
```

---

## 10. 自查清单

- [ ] 能说清路径参数 / 查询参数 / 请求体分别用在哪
- [ ] 能用 Pydantic 模型定义请求体，并加上字段约束
- [ ] 知道 `response_model` 为什么能防数据泄露
- [ ] 能用 `Depends` 抽出重复逻辑（认证、DB 会话）
- [ ] 会写全局异常处理器，统一响应格式
- [ ] 能画出分层结构，并说清每层职责
- [ ] 能正确判断接口该写 `async def` 还是 `def`
- [ ] 会用 `TestClient` 给接口写测试

全部打勾 → **W2 完成，进入 W3（数据库）。**
