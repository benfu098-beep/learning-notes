"""
W3 练习 2：异步 CRUD（增删改查）

任务：实现四个函数
  · create_user   新增
  · get_by_username   按用户名查
  · update_email  改邮箱
  · delete_user   删除

完成标准：自测全部 ✅

参考讲义：python/05-sqlalchemy-orm.md 第 4 节「CRUD 四件套」

⚠️ 关键要求：所有函数都要用 AsyncSession，且必须 commit
"""

import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"


# ================================================================
#  任务 1：新增
# ================================================================
async def create_user(session: AsyncSession, username: str, email: str | None = None):
    """
    新建一个用户，返回带有数据库生成 id 的 User 对象。

    TODO: 实现它

    提示（三步）：
        user = User(username=username, email=email)
        session.add(user)
        await session.commit()
        await session.refresh(user)      # ← 必须！否则 user.id 可能拿不到
        return user

    ⚠️ 为什么需要 refresh？
        commit 之后对象可能被标记过期，refresh 会重新从数据库读一次，
        确保 id、created_at 这些数据库生成的字段都有值。
    """
    raise NotImplementedError("请实现 create_user")


# ================================================================
#  任务 2：条件查询
# ================================================================
async def get_by_username(session: AsyncSession, username: str):
    """
    按用户名查一个用户，查不到返回 None。

    TODO: 实现它

    提示：
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    理解 scalar_one_or_none()：
      0 条 → None；1 条 → User；多条 → 抛异常（说明唯一约束没生效）
    """
    raise NotImplementedError("请实现 get_by_username")


# ================================================================
#  任务 3：更新
# ================================================================
async def update_email(session: AsyncSession, username: str, new_email: str) -> bool:
    """
    改用户邮箱。成功返回 True，用户不存在返回 False。

    TODO: 实现它

    提示：
        user = await get_by_username(session, username)
        if user is None:
            return False
        user.email = new_email          # 直接改属性
        await session.commit()          # ← 必须 commit 才生效
        return True

    理解：ORM 会自动比对，只 UPDATE 变化的字段。
    """
    raise NotImplementedError("请实现 update_email")


# ================================================================
#  任务 4：删除
# ================================================================
async def delete_user(session: AsyncSession, username: str) -> bool:
    """
    删除用户。成功返回 True，不存在返回 False。

    TODO: 实现它

    提示：
        user = await get_by_username(session, username)
        if user is None:
            return False
        await session.delete(user)
        await session.commit()
        return True
    """
    raise NotImplementedError("请实现 delete_user")


# ================================================================
#  自测（模型定义在这里给出，不用改）
# ================================================================
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(100), nullable=True)


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    P = F = 0

    def ck(name, cond, detail=""):
        nonlocal P, F
        if cond:
            P += 1
            print(f"  ✅ {name}")
        else:
            F += 1
            print(f"  ❌ {name}" + (f"   {detail}" if detail else ""))

    # 准备干净的 users 表
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS users"))
        await conn.run_sync(Base.metadata.create_all)

    print("=" * 60)
    print("  任务 1：新增")
    print("=" * 60)
    try:
        async with SessionLocal() as s:
            u = await create_user(s, "benfu", "benfu@test.com")
        ck("create_user 返回对象", u is not None)
        ck("拿到数据库生成的 id", getattr(u, "id", None) is not None, f"id={getattr(u,'id',None)}")
        ck("username 正确", getattr(u, "username", None) == "benfu")
        ck("email 正确", getattr(u, "email", None) == "benfu@test.com")
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    print()
    print("=" * 60)
    print("  任务 2：按用户名查询")
    print("=" * 60)
    try:
        async with SessionLocal() as s:
            found = await get_by_username(s, "benfu")
            notfound = await get_by_username(s, "不存在的人")
        ck("能查到刚建的用户", found is not None and found.username == "benfu")
        ck("查不到时返回 None", notfound is None, f"实际 {notfound!r}")
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    print()
    print("=" * 60)
    print("  任务 3：更新邮箱")
    print("=" * 60)
    try:
        async with SessionLocal() as s:
            ok = await update_email(s, "benfu", "new@test.com")
        ck("更新返回 True", ok is True)
        async with SessionLocal() as s:
            u = await get_by_username(s, "benfu")
        ck("邮箱真的改了", u is not None and u.email == "new@test.com",
           f"实际 {getattr(u,'email',None)}")
        async with SessionLocal() as s:
            ok2 = await update_email(s, "不存在的人", "x@y.com")
        ck("更新不存在的用户返回 False", ok2 is False)
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    print()
    print("=" * 60)
    print("  任务 4：删除")
    print("=" * 60)
    try:
        async with SessionLocal() as s:
            ok = await delete_user(s, "benfu")
        ck("删除返回 True", ok is True)
        async with SessionLocal() as s:
            gone = await get_by_username(s, "benfu")
        ck("删完真的查不到了", gone is None, f"实际 {gone!r}")
        async with SessionLocal() as s:
            ok2 = await delete_user(s, "不存在的人")
        ck("删除不存在的返回 False", ok2 is False)
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    await engine.dispose()

    print()
    print("=" * 60)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 60)
    if F == 0:
        print("  🎉 全部通过！你已经会用异步 ORM 做增删改查了。")


if __name__ == "__main__":
    asyncio.run(main())
