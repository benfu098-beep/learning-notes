"""
W3 练习 3：索引与 EXPLAIN 实战

目标：亲手测出「加索引前后」的差距，并学会看执行计划。

流程：
  ① 造 10 万行数据（已实现）
  ② 无索引查询 → 计时          ← TODO 你来实现
  ③ 建索引
  ④ 有索引查询 → 计时，对比     ← TODO 你来实现
  ⑤ EXPLAIN 看执行计划         ← TODO 你来实现
  ⑥ 索引失效实验（已实现，观察结果）

⚠️ 第一次跑会插入 10 万行，约 10–30 秒。之后再跑会跳过（数据已存在）。

参考讲义：python/05b-index-and-explain.md
"""

import asyncio
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"
TABLE = "perf_test"
ROWS = 100_000
ITERATIONS = 20        # 每个查询跑 20 次取平均，减少抖动

CITIES = ["北京", "上海", "广州", "深圳", "杭州"]


# ================================================================
#  已实现：建表 + 造数据
# ================================================================
async def setup(conn):
    r = await conn.execute(text(f"SELECT COUNT(*) FROM information_schema.tables "
                                f"WHERE table_schema='learning_notes' AND table_name='{TABLE}'"))
    exists = r.scalar() > 0

    if exists:
        r = await conn.execute(text(f"SELECT COUNT(*) FROM {TABLE}"))
        n = r.scalar()
        if n == ROWS:
            print(f"  · {TABLE} 已有 {n:,} 行，跳过建表")
            return
        print(f"  · 行数不对（{n:,}），重建")

    print(f"  · 正在造 {ROWS:,} 行数据…")
    await conn.execute(text(f"DROP TABLE IF EXISTS {TABLE}"))
    await conn.execute(text(f"""
        CREATE TABLE {TABLE} (
            id       INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50)  NOT NULL,
            email    VARCHAR(100) NOT NULL,
            city     VARCHAR(20)  NOT NULL,
            age      INT          NOT NULL,
            bio      VARCHAR(200) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """))

    rows = [
        {
            "username": f"user{i}",
            "email": f"user{i}@example.com",
            "city": CITIES[i % len(CITIES)],
            "age": 20 + (i % 40),
            "bio": f"这是第 {i} 个用户的简介内容",
        }
        for i in range(ROWS)
    ]
    await conn.execute(
        text(f"INSERT INTO {TABLE} (username, email, city, age, bio) "
             f"VALUES (:username, :email, :city, :age, :bio)"),
        rows,
    )
    print(f"  · ✅ 造好 {ROWS:,} 行")


# ================================================================
#  任务 1：无索引查询，测耗时
# ================================================================
async def time_query(conn, email: str) -> float:
    """
    按 email 查一条记录，跑 ITERATIONS 次，返回【平均耗时（毫秒）】。

    正确写法（两行，先 await 再取结果）：
        t0 = time.perf_counter()
        for _ in range(ITERATIONS):
            result = await conn.execute(
                text(f"SELECT id, username FROM {TABLE} WHERE email = :e"),
                {"e": email},
            )
            result.first()
        return (time.perf_counter() - t0) / ITERATIONS * 1000

    ⚠️ 千万不要写成  await conn.execute(...).first()
       因为 .first() 的优先级比 await 高，实际执行的是：
           await (conn.execute(...).first())
       而 execute() 返回的是协程对象，没有 .first() 方法，会报：
           AttributeError: 'coroutine' object has no attribute 'first'
       正确做法要么加括号 (await conn.execute(...)).first()，
       要么拆成两行（推荐，更清楚）。
    """
    t0 = time.perf_counter()
    for _ in range(ITERATIONS):
        result = await conn.execute(
            text(f"SELECT id, username FROM {TABLE} WHERE email = :e"),
            {"e": email},
        )
        result.first()
    cost = (time.perf_counter() - t0) / ITERATIONS * 1000
    return cost


# ================================================================
#  任务 2：给 email 建索引
# ================================================================
async def create_email_index(conn):
    """
    给 email 列建一个普通索引（名字随意，比如 idx_email）。

    TODO: 实现它

    提示：
        await conn.execute(text(f"CREATE INDEX idx_email ON {TABLE} (email)"))
        print("  · ✅ 索引已创建")

    ⚠️ 如果索引已存在会报错。可以先查一下：
        SHOW INDEX FROM {TABLE} WHERE Key_name = 'idx_email'
    """
    await conn.execute(text(f"CREATE INDEX idx_email ON {TABLE} (email)"))
    print("  · ✅ 索引已创建")


# ================================================================
#  任务 3：EXPLAIN 看执行计划
# ================================================================
async def show_explain(conn, email: str) -> dict:
    """
    对「按 email 查询」跑 EXPLAIN，返回 {'type':..., 'key':..., 'rows':..., 'Extra':...}

    TODO: 实现它

    提示：
        r = await conn.execute(text(
            f"EXPLAIN FORMAT=TRADITIONAL SELECT id, username FROM {TABLE} WHERE email = :e"
        ), {"e": email})
        row = r.mappings().first()       # mappings() 让结果能按列名访问
        return {
            "type": row["type"],
            "key": row["key"],
            "rows": row["rows"],
            "Extra": row["Extra"],
        }

    理解：
      type=ALL          → 全表扫描（坏）
      type=ref          → 走索引等值查询（好）
      key=None          → 没用索引
      rows=100000       → 预估要扫 10 万行
    """
    r = await conn.execute(text(
        f"EXPLAIN FORMAT=TRADITIONAL SELECT id, username FROM {TABLE} WHERE email = :e"
    ), {"e": email})
    row = r.mappings().first()       # mappings() 让结果能按列名访问
    return {
        "type": row["type"],
        "key": row["key"],
        "rows": row["rows"],
        "Extra": row["Extra"],
    }


# ================================================================
#  已实现：索引失效实验
# ================================================================
async def invalidation_tests(conn):
    cases = [
        ("正常等值查询",
         f"SELECT id FROM {TABLE} WHERE email = 'user50000@example.com'"),
        ("① 对索引列用函数",
         f"SELECT id FROM {TABLE} WHERE SUBSTRING(email, 1, 4) = 'user'"),
        ("② 隐式类型转换（city 是 varchar，传数字）",
         f"SELECT id FROM {TABLE} WHERE age = '25'"),
        ("③ 前导模糊匹配",
         f"SELECT id FROM {TABLE} WHERE email LIKE '%user50000%'"),
        ("④ 只有后缀能匹配",
         f"SELECT id FROM {TABLE} WHERE email LIKE 'user50000%'"),
        ("⑤ OR 连接了无索引列",
         f"SELECT id FROM {TABLE} WHERE email = 'user50000@example.com' OR city = '北京'"),
    ]
    print(f"  {'场景':<42} {'type':<8} {'key':<14} rows")
    print("  " + "-" * 82)
    for name, sql in cases:
        r = await conn.execute(text("EXPLAIN FORMAT=TRADITIONAL " + sql))
        row = r.mappings().first()
        key = row["key"] if row["key"] else "NULL"
        print(f"  {name:<42} {row['type']:<8} {key:<14} {row['rows']}")


# ================================================================
#  主流程
# ================================================================
async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    P = F = 0

    def ck(name, cond, detail=""):
        nonlocal P, F
        if cond:
            P += 1
            print(f"  ✅ {name}")
        else:
            F += 1
            print(f"  ❌ {name}" + (f"   {detail}" if detail else ""))

    async with engine.begin() as conn:
        print("=" * 84)
        print("  ① 准备数据")
        print("=" * 84)
        await setup(conn)

    email = "user50000@example.com"

    # ---------- 无索引 ----------
    print()
    print("=" * 84)
    print("  ② 无索引查询")
    print("=" * 84)
    async with engine.connect() as conn:
        await conn.execute(text(f"DROP INDEX idx_email ON {TABLE}")) if False else None
        # 先确保没有索引
        r = await conn.execute(text(f"SHOW INDEX FROM {TABLE} WHERE Key_name='idx_email'"))
        if r.first():
            await conn.execute(text(f"DROP INDEX idx_email ON {TABLE}"))
            print("  · 已删除旧索引")
        await conn.commit()
        try:
            t_no_index = await time_query(conn, email)
            print(f"  平均耗时：{t_no_index:.2f} ms")
        except NotImplementedError as e:
            print(f"  ⏳ {e}")
            await engine.dispose()
            return

    # ---------- 建索引 ----------
    print()
    print("=" * 84)
    print("  ③ 给 email 建索引")
    print("=" * 84)
    async with engine.begin() as conn:
        try:
            await create_email_index(conn)
        except NotImplementedError as e:
            print(f"  ⏳ {e}")
            await engine.dispose()
            return

    # ---------- 有索引 ----------
    print()
    print("=" * 84)
    print("  ④ 有索引查询")
    print("=" * 84)
    async with engine.connect() as conn:
        t_with_index = await time_query(conn, email)
        print(f"  平均耗时：{t_with_index:.2f} ms")
        print()
        if t_no_index > 0:
            print(f"  ⚡ 提速 {t_no_index / t_with_index:.0f} 倍"
                  f"（{t_no_index:.1f}ms → {t_with_index:.1f}ms）")

        ck("有索引确实更快", t_with_index < t_no_index,
           f"{t_with_index:.2f} vs {t_no_index:.2f}")

    # ---------- EXPLAIN ----------
    print()
    print("=" * 84)
    print("  ⑤ EXPLAIN 执行计划")
    print("=" * 84)
    async with engine.connect() as conn:
        try:
            plan = await show_explain(conn, email)
            for k, v in plan.items():
                print(f"  {k:<8} = {v}")
            ck("EXPLAIN 用的是索引（key 不为空）", plan["key"] is not None, str(plan["key"]))
            ck("type 不是 ALL（没走全表扫描）", plan["type"] != "ALL", str(plan["type"]))
            ck("预估扫描行数很小", int(plan["rows"]) < 100, str(plan["rows"]))
        except NotImplementedError as e:
            print(f"  ⏳ {e}")

    # ---------- 索引失效 ----------
    print()
    print("=" * 84)
    print("  ⑥ 索引失效实验（看看哪些情况下 key 变成 NULL）")
    print("=" * 84)
    async with engine.connect() as conn:
        await invalidation_tests(conn)

    await engine.dispose()

    print()
    print("=" * 84)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 84)
    if F == 0 and P > 0:
        print("  🎉 全部通过！你已经会用 EXPLAIN 判断索引有没有生效了。")
    print()
    print("  💡 做完后想一想：")
    print("     · 上面④索引失效实验里，哪几种是你写代码时会真实踩到的？")
    print("     · 如果 WHERE 是 age > 25 AND city = '北京'，该建什么索引？")


if __name__ == "__main__":
    asyncio.run(main())
