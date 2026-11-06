"""
W3 练习 4：事务与锁

任务：
  ① 实现转账（原子性：要么两边都变，要么都不变）
  ② 验证「余额不足时自动回滚」
  ③ 观察当前隔离级别

完成标准：自测全部 ✅

参考讲义：python/05c-transaction-and-lock.md

⚠️ 核心：转账的两步必须在【同一个事务】里，
   而且读余额时要加锁（FOR UPDATE），否则并发会超卖。
"""

import asyncio

from sqlalchemy import Numeric, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)


# ================================================================
#  任务 1：转账
# ================================================================
async def transfer(session: AsyncSession, from_id: str, to_id: str, amount: float) -> None:
    """
    从 from_id 转 amount 到 to_id。

    要求：
      · 余额不足 → raise ValueError("余额不足")
      · 成功 → 两边余额都更新
      · 任何一步失败 → 两边都不变（自动回滚）

    TODO: 实现它

    提示（用 async with session.begin() 包住整个事务）：

        async with session.begin():
            a = await session.get(Account, from_id, with_for_update=True)
            b = await session.get(Account, to_id, with_for_update=True)

            if a is None or b is None:
                raise ValueError("账户不存在")
            if float(a.balance) < amount:
                raise ValueError("余额不足")

            a.balance = float(a.balance) - amount
            b.balance = float(b.balance) + amount

    关键点：
      · async with session.begin()  →  进入时 BEGIN，正常退出自动 COMMIT，
                                       抛异常自动 ROLLBACK
      · with_for_update=True        →  SELECT ... FOR UPDATE，加排他锁
                                       防止并发转账时两边都读到旧余额
    """
    async with session.begin():
        a = await session.get(Account, from_id, with_for_update=True)
        b = await session.get(Account, to_id, with_for_update=True)

        if a is None or b is None:
            raise ValueError("账户不存在")
        if float(a.balance) < amount:
            raise ValueError("余额不足")

        a.balance = float(a.balance) - amount
        b.balance = float(b.balance) + amount


# ================================================================
#  任务 2：查隔离级别
# ================================================================
async def get_isolation_level(session: AsyncSession) -> str:
    """
    TODO: 返回当前事务隔离级别（字符串，比如 "REPEATABLE-READ"）

    提示：
        r = await session.execute(text("SELECT @@transaction_isolation"))
        return r.scalar()
    """
    c = await session.execute(text("SELECT @@transaction_isolation"))
    return c.scalar()


# ================================================================
#  自测
# ================================================================
async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    P = F = 0

    def ck(name, cond, detail=""):
        nonlocal P, F
        if cond:
            P += 1
            print(f"  ✅ {name}")
        else:
            F += 1
            print(f"  ❌ {name}" + (f"   {detail}" if detail else ""))

    async def reset():
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS accounts"))
            await conn.run_sync(Base.metadata.create_all)
        async with Session() as s:
            s.add_all([Account(id="A", balance=1000), Account(id="B", balance=0)])
            await s.commit()

    async def balances() -> tuple[float, float]:
        async with Session() as s:
            a = await s.get(Account, "A")
            b = await s.get(Account, "B")
            return float(a.balance), float(b.balance)

    # ---------- 任务 2：隔离级别 ----------
    print("=" * 64)
    print("  任务 2：当前隔离级别")
    print("=" * 64)
    try:
        await reset()
        async with Session() as s:
            lvl = await get_isolation_level(s)
        print(f"  MySQL 默认隔离级别：{lvl}")
        ck("能读到隔离级别", bool(lvl), str(lvl))
        ck("是 REPEATABLE-READ（MySQL 默认）", lvl.upper().replace("_", "-") == "REPEATABLE-READ", str(lvl))
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    # ---------- 任务 1-1：正常转账 ----------
    print()
    print("=" * 64)
    print("  任务 1-1：正常转账 A → B  300")
    print("=" * 64)
    await reset()
    print(f"  转账前：A={await balances()}")
    try:
        async with Session() as s:
            await transfer(s, "A", "B", 300)
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    a, b = await balances()
    print(f"  转账后：A=({a}, {b})")
    ck("A 扣了 300", a == 700, f"A={a}")
    ck("B 加了 300", b == 300, f"B={b}")
    ck("A + B 总额不变（1000）", a + b == 1000, f"合计 {a + b}")

    # ---------- 任务 1-2：余额不足 → 回滚 ----------
    print()
    print("=" * 64)
    print("  任务 1-2：余额不足 A → B  5000（应该整个回滚）")
    print("=" * 64)
    await reset()
    print(f"  转账前：A={await balances()}")
    try:
        async with Session() as s:
            await transfer(s, "A", "B", 5000)
        print("  ❌ 没有抛异常，应该报余额不足")
        F += 1
    except ValueError as e:
        print(f"  ✅ 正确抛出：{e}")
        P += 1

    a, b = await balances()
    print(f"  转账后：A=({a}, {b})")
    ck("A 没变（回滚了）", a == 1000, f"A={a}")
    ck("B 没变（回滚了）", b == 0, f"B={b}")

    # ---------- 事务边界 ----------
    print()
    print("=" * 64)
    print("  额外验证：事务的原子性")
    print("=" * 64)
    await reset()
    print("  模拟：扣了 A 的钱，然后抛异常")
    try:
        async with Session() as s:
            async with s.begin():
                acc = await s.get(Account, "A", with_for_update=True)
                acc.balance = float(acc.balance) - 999      # 先改了
                raise RuntimeError("模拟中途崩溃")            # 再抛异常
    except RuntimeError:
        pass
    a, b = await balances()
    print(f"  结果：A={a}, B={b}")
    ck("★ 改动被自动回滚（A 仍是 1000）", a == 1000, f"A={a}")

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS accounts"))
    await engine.dispose()

    print()
    print("=" * 64)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 64)
    if F == 0 and P > 0:
        print("  🎉 全部通过！你已经掌握事务的原子性和自动回滚了。")
    print()
    print("  💡 想一想：如果把 with_for_update=True 去掉，会出什么问题？")
    print("     （提示：两个请求同时转账，都读到 A=1000，都以为够扣 800）")


if __name__ == "__main__":
    asyncio.run(main())
