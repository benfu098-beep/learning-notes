# W3 补充：事务与锁

> **面试必考，而且项目里一定会用。**
> "扣配额 + 记日志必须在一个事务里" —— 项目 A 就会遇到。

---

## 0. 为什么需要事务

**场景**：账户 A 转 100 块给账户 B。

```sql
UPDATE accounts SET balance = balance - 100 WHERE id = 'A';    -- ①
UPDATE accounts SET balance = balance + 100 WHERE id = 'B';    -- ②
```

**如果第 ② 步执行前系统崩了？**

```
A 少了 100，B 没多 100 → 凭空消失 100 块
```

**事务解决的就是这个问题**：让这两步**要么全成功，要么全失败**。

```sql
BEGIN;
  UPDATE accounts SET balance = balance - 100 WHERE id = 'A';
  UPDATE accounts SET balance = balance + 100 WHERE id = 'B';
COMMIT;      -- 两步都成功才提交
-- 或者 ROLLBACK;  -- 任何一步失败，全部撤销
```

---

## 1. ACID 四个特性

| 特性 | 含义 | 靠什么保证 |
|---|---|---|
| **A**tomicity 原子性 | 要么全做，要么全不做 | undo log（回滚日志） |
| **C**onsistency 一致性 | 数据始终满足业务约束（如余额不为负） | 由应用 + 数据库约束共同保证 |
| **I**solation 隔离性 | 并发事务之间互不干扰 | 锁 + MVCC |
| **D**urability 持久性 | 提交后即使断电也不丢 | redo log（重做日志） |

**面试标准答法**（不要只背四个词，要说清"靠什么实现"）：

> "原子性靠 undo log，持久性靠 redo log，隔离性靠锁和 MVCC，一致性是最终目标，由前三者加业务约束共同保证。"

---

## 2. ⭐ 三种并发问题

| 问题 | 现象 | 例子 |
|---|---|---|
| **脏读** | 读到别的事务**未提交**的数据 | 事务 B 改了余额但还没提交，A 读到了；B 回滚 → A 读到的是假数据 |
| **不可重复读** | 同一事务内，**两次读同一行**结果不同 | A 第一次读余额 100，B 改成 200 并提交，A 再读变成 200 |
| **幻读** | 同一事务内，**两次查同一范围**，行数变了 | A 查"余额>100 的用户"有 3 个，B 插入 1 个并提交，A 再查变成 4 个 |

**区别记忆**：
- 脏读 = 读到**假**数据（未提交）
- 不可重复读 = 同一行**值变了**
- 幻读 = **行数变了**（多了或少了一行）

---

## 3. 四种隔离级别

| 级别 | 脏读 | 不可重复读 | 幻读 | 谁在用 |
|---|---|---|---|---|
| READ UNCOMMITTED | ❌ 可能 | ❌ 可能 | ❌ 可能 | 几乎不用 |
| READ COMMITTED | ✅ 解决 | ❌ 可能 | ❌ 可能 | Oracle 默认、PostgreSQL 默认 |
| **REPEATABLE READ** | ✅ | ✅ 解决 | ⚠️ 部分解决 | **MySQL InnoDB 默认** |
| SERIALIZABLE | ✅ | ✅ | ✅ 解决 | 极端场景 |

**注意：隔离级别越高，并发性能越差。**

**MySQL 的 REPEATABLE READ 为什么能"部分解决"幻读？**
因为它用 **MVCC（快照读）** 让普通 `SELECT` 看到的是事务开始时的快照，所以不会幻读。但**当前读**（`SELECT ... FOR UPDATE`）还是会幻读，靠**间隙锁**解决。

```sql
-- 查看当前隔离级别
SELECT @@transaction_isolation;
-- 默认：REPEATABLE-READ
```

---

## 4. MVCC：MySQL 怎么做到"读不加锁"

**核心思想**：给每行数据存多个版本，读的时候按"事务开始的时间点"挑一个版本。

**每行隐藏两个字段**：

| 字段 | 含义 |
|---|---|
| `DB_TRX_ID` | 最后修改这行的事务 ID |
| `DB_ROLL_PTR` | 指向 undo log 里的旧版本 |

**读取规则（简化版）**：

```
找到这行 → 看它的 DB_TRX_ID
  · 比我的事务 ID 小，且已提交 → 我能看 ✅
  · 比我大（是后来者）→ 顺着 ROLL_PTR 找上一个版本
  · 未提交 → 不看我事务开始时的快照
```

**结果**：普通 `SELECT` 不加锁、不阻塞写，读到的是"我事务开始那一刻的数据"。**这就是 REPEATABLE READ 的实现方式。**

---

## 5. 锁

### 按粒度分

| 锁 | 范围 | 场景 |
|---|---|---|
| **表锁** | 整张表 | MyISAM；或显式 `LOCK TABLES` |
| **行锁** | 一行 | InnoDB 默认，并发度高 |
| **间隙锁** | 索引上两个值之间的"空隙" | 防幻读，REPEATABLE READ 下生效 |

### 按模式分

| 锁 | 含义 | SQL |
|---|---|---|
| **共享锁 S** | 读了不许别人改 | `SELECT ... LOCK IN SHARE MODE` |
| **排他锁 X** | 我改谁也别动 | `SELECT ... FOR UPDATE` / `UPDATE` / `DELETE` |

### ⭐ 快照读 vs 当前读

| | 语句 | 加锁吗 | 读到什么 |
|---|---|---|---|
| **快照读** | 普通 `SELECT` | ❌ 不加锁 | 事务开始时的快照（MVCC） |
| **当前读** | `SELECT ... FOR UPDATE` / `UPDATE` / `DELETE` | ✅ 加锁 | 最新已提交数据 |

**这是最容易混的概念**：

```sql
-- 事务 A
BEGIN;
SELECT balance FROM accounts WHERE id = 1;      -- 快照读，不加锁，看到 100
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;  -- 当前读，加排他锁

-- 事务 B（此时）
UPDATE accounts SET balance = 200 WHERE id = 1;  -- 被阻塞！等 A 释放锁
```

---

## 6. 死锁

**场景**：

```
事务 A: 锁住行 1  → 请求行 2
事务 B: 锁住行 2  → 请求行 1
        ↑ 互相等待，永远解不开
```

**MySQL 会自动检测并杀掉一个**：

```
ERROR 1213 (40001): Deadlock found when trying to get lock;
try restarting transaction
```

**怎么避免？**

| 方法 | 说明 |
|---|---|
| **统一加锁顺序** | 所有事务都按 id 从小到大锁 → 不会循环等待 |
| **缩短事务** | 事务里不要做网络请求、不要等用户输入 |
| **降低隔离级别** | 必要时用 READ COMMITTED 减少间隙锁 |
| **加超时** | `innodb_lock_wait_timeout` |

**最重要的是第二条**：**事务里绝对不要有耗时操作**。否则锁持有时间变长，死锁概率飙升。

---

## 7. SQLAlchemy 里怎么用事务

### 自动事务（async_sessionmaker 默认）

```python
async with SessionLocal() as session:
    session.add(user)
    await session.commit()          # 这里才真正提交
    # 出异常自动 rollback
```

**`async with Session()` 退出时会自动 rollback 未提交的改动。**

### 显式事务块（推荐，边界清晰）

```python
async with SessionLocal() as session:
    async with session.begin():      # 进入即 BEGIN
        session.add(t1)
        session.add(t2)
        # 正常退出 → 自动 COMMIT
        # 抛异常   → 自动 ROLLBACK
```

### 转账的完整写法

```python
async def transfer(session, from_id: int, to_id: int, amount: float):
    async with session.begin():
        a = await session.get(Account, from_id, with_for_update=True)   # ← 加锁！
        b = await session.get(Account, to_id, with_for_update=True)

        if a.balance < amount:
            raise ValueError("余额不足")     # 抛异常 → 自动回滚

        a.balance -= amount
        b.balance += amount
    # 退出 with 自动 commit
```

**`with_for_update=True` = `SELECT ... FOR UPDATE`** —— 这就是加锁，防止并发转账时"两个事务都读到 100，都以为够扣"。

---

## 8. 常见坑

| 坑 | 后果 | 解决 |
|---|---|---|
| 事务里做网络请求 | 锁持有时间极长，并发崩 | 把 IO 移到事务外 |
| 忘了加锁 | 并发扣款超卖 | `with_for_update` |
| 异常被吞掉 | 该回滚的没回滚 | 别用 `try/except` 静默 |
| 事务太长 | 锁等待、死锁 | 拆小 |
| 在 `async with session.begin()` 里再 commit | 报错 | 只让上下文管理器提交 |

---

## 9. 自查清单

- [ ] 能说清 ACID 各自靠什么实现
- [ ] 能区分脏读 / 不可重复读 / 幻读
- [ ] 知道 MySQL 默认隔离级别是 REPEATABLE READ
- [ ] 知道 MVCC 靠什么实现（undo log + 事务 ID）
- [ ] 能区分快照读和当前读
- [ ] 知道 `FOR UPDATE` 是干什么的
- [ ] 知道怎么避免死锁
- [ ] 能在 SQLAlchemy 里正确写事务
