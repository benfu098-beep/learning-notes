# W3 讲义：SQLAlchemy 2.0 异步 ORM

> **周期**：W3（压缩到 11/04–11/10，与 W4 Redis 合并）
> **目标**：能用异步 ORM 完成增删改查，能定义表结构和关系
> **配置**：MySQL 26.10（`mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes`）

---

## 0. ORM 解决什么问题

**不用 ORM**（原生 SQL）：

```python
cursor.execute("SELECT id, name FROM users WHERE id = %s", (1,))
row = cursor.fetchone()          # 拿到的是元组 (1, 'benfu')
user = {"id": row[0], "name": row[1]}    # 手动拼装
```

**用 ORM**：

```python
user = await session.get(User, 1)     # 直接拿到 User 对象
user.name                             # 属性访问，有类型提示
```

**ORM 的价值**：

| 好处 | 说明 |
|---|---|
| 面向对象 | 表 → 类，行 → 对象，不用手动拼装 |
| 类型安全 | `Mapped[str]` 让 IDE 和 mypy 都能检查 |
| 防 SQL 注入 | 自动参数化，不用手动拼接 |
| 换库不改代码 | MySQL / PostgreSQL 都一套写法 |
| 关系自动处理 | 一对多、多对多，`user.articles` 直接拿 |

> **代价**：ORM 生成的 SQL 可能不够优，复杂查询仍要写原生 SQL。所以 **W3 后半要学 EXPLAIN 和索引**，不能只会 ORM。

---

## 1. 三个核心概念

```
Engine  ──  连接池，一个进程建一个，全局共享
   │
   ├─ Session  ──  一次数据库会话（事务边界），每个请求一个
   │      │
   │      └─ Model  ──  表 → 类，行 → 实例
   │
   └─ Session  ──  另一个请求的会话
```

| 概念 | 生命周期 | 数量 |
|---|---|---|
| **Engine** | 整个应用 | 1 个 |
| **Session** | 一个请求 / 一次事务 | 很多个 |
| **Model** | 定义（类本身） | 每个表 1 个 |

**最常见的错误**：把 Session 当全局变量用，或者每次都新建 Engine。

---

## 2. 定义模型

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有模型的基类"""
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

### ⭐ `Mapped[T]` 决定两件事

| 写法 | 含义 |
|---|---|
| `Mapped[str]` | 字符串，**NOT NULL** |
| `Mapped[str \| None]` | 字符串，**可为 NULL** |
| `Mapped[bool]` | 布尔 |

**这不是可选的**——SQLAlchemy 2.0 靠 `Mapped[T]` 推断列是否可空、该用哪个 Python 类型。写 `str | None` 就自动变成 `nullable=True`。

### `mapped_column(...)` 决定数据库细节

```python
mapped_column(primary_key=True)          # 主键
mapped_column(String(50))                # 指定长度
mapped_column(unique=True)               # 唯一索引
mapped_column(index=True)                # 普通索引
mapped_column(default=True)              # Python 层默认值
mapped_column(server_default=func.now()) # 数据库层默认值 ← 推荐用于时间
```

### `default` vs `server_default`

```python
created_at: Mapped[datetime] = mapped_column(default=datetime.now)         # Python 算
created_at: Mapped[datetime] = mapped_column(server_default=func.now())    # 数据库算
```

**用 `server_default`**——多个应用实例时时间才一致，也不受应用服务器时钟影响。

---

## 3. 异步引擎与会话

```python
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"

engine = create_async_engine(DATABASE_URL, echo=False)     # ✅ 一个进程一个
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖：每个请求一个 Session，用完自动关闭"""
    async with SessionLocal() as session:
        yield session
```

### ⚠️ `expire_on_commit=False` 为什么必要

```python
user = User(username="benfu")
session.add(user)
await session.commit()
print(user.id)      # 如果 expire_on_commit=True（默认），这里会抛异常
                    # 因为 commit 后对象被标记过期，访问属性要重新查库
                    # 但异步里获取属性不能 await → 报错
```

**异步 ORM 里必须设 `expire_on_commit=False`。**

---

## 4. CRUD 四件套

### Create

```python
user = User(username="benfu", email="a@b.com")
session.add(user)
await session.commit()
await session.refresh(user)        # 拿回数据库生成的 id
print(user.id)
```

批量插入用 `add_all`。

### Read

```python
# 按主键查（最简单）
user = await session.get(User, 1)

# 条件查询
from sqlalchemy import select

stmt = select(User).where(User.is_active == True).order_by(User.id.desc()).limit(10)
result = await session.execute(stmt)
users = result.scalars().all()          # 拿到 list[User]

# 查单个
stmt = select(User).where(User.username == "benfu")
user = (await session.execute(stmt)).scalar_one_or_none()
```

**`scalars()` vs `scalar_one_or_none()`：**

| 方法 | 场景 | 结果 |
|---|---|---|
| `.scalars().all()` | 多条 | `list[User]` |
| `.scalars().first()` | 可能没结果 | `User \| None` |
| `.scalar_one_or_none()` | 期望 0 或 1 条 | `User \| None`，多条会报错 |
| `.scalar_one()` | 期望恰好 1 条 | `User`，0 条或多条都报错 |

### Update

```python
user = await session.get(User, 1)
user.email = "new@b.com"      # 直接改属性
await session.commit()        # 提交才生效
```

**ORM 会自动检测哪些字段改了，只 UPDATE 变化的部分。**

### Delete

```python
user = await session.get(User, 1)
await session.delete(user)
await session.commit()
```

---

## 5. 关系：一对多

```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    articles: Mapped[list["Article"]] = relationship(back_populates="author")


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    author: Mapped["User"] = relationship(back_populates="articles")
```

**用法：**

```python
# 从用户拿文章
user = await session.get(User, 1)
for a in user.articles: ...
# ⚠️ 异步里访问懒加载关系会报错！必须用 selectinload 预加载：
stmt = select(User).options(selectinload(User.articles)).where(User.id == 1)
```

> ⚠️ **异步 ORM 的关系加载是个大坑**：默认懒加载会在属性访问时发 SQL，但异步里不能那样隐式 await。**必须用 `selectinload()` 预加载。** 这个坑 W3 练习里会专门练。

---

## 6. 建表：开发期 vs 生产

### 开发期：`create_all`

```python
async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
```

**特点**：表不存在就建，已存在就跳过。**不会改表结构**——加了字段它不管。

### 生产：Alembic 迁移

```bash
alembic init migrations
alembic revision --autogenerate -m "add email column"
alembic upgrade head
```

**为什么需要？** 因为生产数据库里有数据，不能删表重建。Alembic 会把每次结构变更记成一个迁移脚本，可以前进也可以回滚。

**W3 先会 `create_all` 就够了**，Alembic 等做项目 A 时再用。

---

## 7. 常见坑清单

| 坑 | 表现 | 解决 |
|---|---|---|
| 忘 `commit` | 数据没写进去 | add/delete 后必须 commit |
| `expire_on_commit` 没关 | commit 后访问属性报错 | `expire_on_commit=False` |
| 异步里用同步 Session | `MissingGreenlet` 错误 | 全程用 `AsyncSession` |
| 异步里访问关系属性 | `MissingGreenlet` 错误 | `selectinload()` 预加载 |
| Engine 每次新建 | 连接泄漏、性能差 | 全局一个 engine |
| Session 全局共享 | 并发串数据 | 每请求一个，用 `Depends` |
| `default` 用 `datetime.now` | 多实例时间不一致 | 用 `server_default=func.now()` |

---

## 8. 自查清单

- [ ] 能说出 Engine / Session / Model 各自的生命周期
- [ ] 能定义带主键、索引、默认值的模型
- [ ] 知道 `Mapped[str]` 和 `Mapped[str | None]` 的区别
- [ ] 知道 `default` 和 `server_default` 该用哪个
- [ ] 能写出增删改查四个操作
- [ ] 能区分 `scalars().all()` 和 `scalar_one_or_none()`
- [ ] 知道为什么 `expire_on_commit=False`
- [ ] 知道异步里关系必须用 `selectinload()` 预加载

全部打勾 → **W3 ORM 部分完成，进入索引/事务/EXPLAIN。**
