# W3 补充：关系与异步加载

> **这一节讲的是"异步 ORM 独有的坑"**——同步 SQLAlchemy 里根本不会遇到。
> 不知道这个，你在项目 A 里必卡。

---

## 1. 一对多关系怎么定义

```python
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    # 一个用户有多篇文章
    articles: Mapped[list["Article"]] = relationship(back_populates="author")


class Article(Base):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # 多篇文章属于一个作者
    author: Mapped["User"] = relationship(back_populates="articles")
```

### 三个关键点

| 要素 | 作用 |
|---|---|
| `ForeignKey("users.id")` | 数据库层的**外键约束**（建表的 DDL 里会有） |
| `relationship(...)` | Python 层的**对象导航**（`user.articles`、`article.author`） |
| `back_populates` | **双向关联**：两边互指，ORM 才知道是一对关系 |

**`ForeignKey` 和 `relationship` 是两回事**：
- `ForeignKey` 管**数据库**
- `relationship` 管**Python 对象**

**只写 `ForeignKey` 不写 `relationship`**：表能建，但 `user.articles` 用不了。

---

## 2. ⭐ 核心问题：异步里懒加载会崩

**同步 SQLAlchemy（没问题）**：

```python
user = session.get(User, 1)
for a in user.articles:        # ✅ 自动发一条 SELECT articles WHERE author_id=1
    print(a.title)
```

**异步（会崩）**：

```python
user = await session.get(User, 1)
for a in user.articles:        # ❌ MissingGreenlet
    print(a.title)
```

**报错长这样**：

```
sqlalchemy.exc.MissingGreenlet: greenlet_spawn has not been called;
can't call await_only() here. Was IO attempted in an unexpected place?
```

### 为什么会崩

**懒加载（lazy loading）的本质是"隐式 IO"**：

```
访问 user.articles
    ↓
发现数据还没加载
    ↓
【隐式地】发一条 SQL 去查          ← 这里需要 await
    ↓
但属性访问语法 `user.articles` 不能写 await
    ↓
💥 MissingGreenlet
```

**同步代码能忍**：属性访问时阻塞一下没关系。
**异步代码不忍**：事件循环里不能有"偷偷阻塞"的 IO。

---

## 3. 解法：在查询时就把关系一起加载

### `selectinload` —— 最常用（发第二条 SELECT）

```python
from sqlalchemy.orm import selectinload

stmt = select(User).options(selectinload(User.articles)).where(User.id == 1)
user = (await session.execute(stmt)).scalar_one()

for a in user.articles:        # ✅ 已经加载好了，不再发 SQL
    print(a.title)
```

**生成的 SQL**：

```sql
SELECT * FROM users WHERE id = 1;
SELECT * FROM articles WHERE author_id IN (1);      -- 第二条，一次捞完
```

### `joinedload` —— 用 JOIN（只有一条 SQL）

```python
stmt = select(User).options(joinedload(User.articles)).where(User.id == 1)
```

**生成的 SQL**：

```sql
SELECT * FROM users LEFT OUTER JOIN articles ON ... WHERE users.id = 1;
```

### 两者怎么选

| | `selectinload` | `joinedload` |
|---|---|---|
| SQL 条数 | 2 条 | 1 条 |
| 适合 | **一对多**（子记录多） | **多对一 / 一对一** |
| 问题 | 无 | 一对多时会产生**笛卡尔积**，数据重复膨胀 |

**记忆**：
- **一对多 → `selectinload`**（父记录少，子记录多）
- **多对一 → `joinedload`**（子记录少，父记录 1 条）

---

## 4. ⚠️ N+1 查询问题

**这是最经典的性能坑**：

```python
# ❌ N+1：查 100 个用户，额外发了 100 条 SQL
users = (await session.execute(select(User).limit(100))).scalars().all()
for u in users:
    print(len(u.articles))     # 每次访问都发一条 SQL
```

```
1 条 SQL（查用户） + 100 条 SQL（每个用户查文章） = 101 条
```

**修复**：

```python
# ✅ 2 条 SQL
stmt = select(User).options(selectinload(User.articles)).limit(100)
users = (await session.execute(stmt)).scalars().all()
for u in users:
    print(len(u.articles))     # 不再发 SQL
```

**面试常问**："什么是 N+1 问题？怎么解决？"
**答**：查询 N 条主记录后，每条又单独查一次关联数据，总共 N+1 条 SQL。解决方法是**预加载**（`selectinload` / `joinedload`），把 N+1 降到 2 条或 1 条。

---

## 5. 其他常用参数

```python
relationship(
    back_populates="author",
    lazy="raise",              # ⭐ 禁止懒加载，误用立刻报错（开发期推荐）
    cascade="all, delete-orphan",   # 删父记录时级联删子记录
)
```

### `lazy="raise"` —— 开发期的好习惯

```python
articles: Mapped[list["Article"]] = relationship(back_populates="author", lazy="raise")
```

**效果**：没预加载就访问 `user.articles` → 立刻抛 `InvalidRequestError`，提示"你忘了 selectinload"。

**为什么好**：比 `MissingGreenlet` 的错误信息清楚得多，**一眼知道哪里错了**。

> 项目 A 里建议给所有关系都加上 `lazy="raise"`，逼自己每次查询都显式想清楚要不要加载关系。

### `cascade` —— 级联操作

```python
cascade="all, delete-orphan"    # 删用户时，自动删掉他所有文章
```

**默认行为**：删父记录时，子记录的外键会变成 NULL（如果可空）或者报外键约束错误。

---

## 6. 常见坑清单

| 坑 | 报错 | 解法 |
|---|---|---|
| 异步懒加载 | `MissingGreenlet` | `selectinload` / `joinedload` |
| N+1 查询 | 不报错，但慢 | 预加载 |
| 一对多用 `joinedload` | 数据重复膨胀 | 改 `selectinload` |
| 只写 ForeignKey 不写 relationship | `user.articles` 不存在 | 补 `relationship` |
| 忘了 `back_populates` | 反向导航失效 | 两边都写 |
| 删父记录报外键错误 | `IntegrityError` | 加 `cascade` 或先删子 |

---

## 7. 自查清单

- [ ] 能写出正确的一对多模型（ForeignKey + relationship + back_populates）
- [ ] 知道 `ForeignKey` 和 `relationship` 的区别
- [ ] 能解释异步里为什么会 `MissingGreenlet`
- [ ] 知道 `selectinload` 和 `joinedload` 该选哪个
- [ ] 能说出什么是 N+1 问题、怎么解决
- [ ] 知道 `lazy="raise"` 有什么用
- [ ] 知道 `cascade` 怎么用
