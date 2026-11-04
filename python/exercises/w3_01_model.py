"""
W3 练习 1：定义 ORM 模型并建表

任务：
  1. 补全 User 模型的字段定义（6 个字段）
  2. 用 create_all 建表
  3. 跑自测，验证表结构是否正确

完成标准：自测全部 ✅

参考讲义：python/05-sqlalchemy-orm.md 第 2 节「定义模型」
"""

import asyncio
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func, inspect, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"


class Base(DeclarativeBase):
    pass


# ================================================================
#  任务 1：补全字段
# ================================================================
class User(Base):
    """
    用户表。

    TODO: 补全下面 5 个字段的 mapped_column(...)

    要求：
      id         主键，自增
      username   字符串，最长 50，唯一，加索引
      email      字符串，最长 100，【可为空】
      is_active  布尔，Python 层默认 True
      created_at 时间，用【数据库层】默认值（server_default=func.now()）
      bio        大文本，【可为空】

    ⚠️ 关键点：
      · `Mapped[str]` → NOT NULL；`Mapped[str | None]` → 可为 NULL
      · 时间用 server_default，不要用 default=datetime.now

    写法示例：
      id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    """
    __tablename__ = "users"

    # TODO 1: id —— 主键，自增
    # id: Mapped[int] = ...

    # TODO 2: username —— 最长 50，唯一，索引
    # username: Mapped[str] = ...

    # TODO 3: email —— 最长 100，可为空
    # email: Mapped[???] = ...

    # TODO 4: is_active —— 布尔，默认 True
    # is_active: Mapped[bool] = ...

    # TODO 5: created_at —— 数据库层默认 now()
    # created_at: Mapped[datetime] = ...

    # TODO 6: bio —— 大文本，可为空
    # bio: Mapped[???] = ...
    pass


# ================================================================
#  任务 2：建表
# ================================================================
async def create_tables(engine):
    """
    删掉旧表再重建（方便反复练习）。

    TODO: 实现它

    提示：
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS users"))
            await conn.run_sync(Base.metadata.create_all)

    为什么用 run_sync？
      Base.metadata.create_all 是同步方法，异步 engine 里要通过 run_sync 调用。
    """
    raise NotImplementedError("请实现 create_tables")


# ================================================================
#  自测
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

    print("=" * 60)
    print("  任务 1：模型字段定义")
    print("=" * 60)

    cols = User.__table__.columns
    names = [c.name for c in cols]
    print(f"  你定义了 {len(names)} 个字段：{names}")
    print()

    ck("有 6 个字段", len(names) == 6, f"实际 {len(names)} 个")

    c = User.__table__.columns.get("id")
    ck("id 是主键且自增", c is not None and c.primary_key and c.autoincrement in (True, "auto"),
       str(c) if c else "缺失")

    c = User.__table__.columns.get("username")
    ck("username 唯一", c is not None and c.unique, "缺 unique")
    ck("username 有索引", c is not None and c.index, "缺 index")
    ck("username 长度 50", c is not None and getattr(c.type, "length", None) == 50,
       f"实际 {getattr(c.type,'length',None) if c else '缺失'}")

    c = User.__table__.columns.get("email")
    ck("email 可为空", c is not None and c.nullable, "应为 nullable=True")
    ck("email 长度 100", c is not None and getattr(c.type, "length", None) == 100,
       f"实际 {getattr(c.type,'length',None) if c else '缺失'}")

    c = User.__table__.columns.get("is_active")
    ck("is_active 是布尔", c is not None and isinstance(c.type, Boolean), str(type(c.type)) if c else "缺失")

    c = User.__table__.columns.get("created_at")
    ck("created_at 有 server_default", c is not None and c.server_default is not None,
       "用了 default 而非 server_default？")

    c = User.__table__.columns.get("bio")
    ck("bio 可为空", c is not None and c.nullable, "应为 nullable=True")
    ck("bio 是大文本", c is not None and isinstance(c.type, Text), str(type(c.type)) if c else "缺失")

    print()
    print("=" * 60)
    print("  任务 2：建表")
    print("=" * 60)
    try:
        await create_tables(engine)
        print("  ✅ create_tables 执行成功")
        P += 1
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    # 从数据库里确认表真的建出来了
    async with engine.connect() as conn:
        r = await conn.execute(text("SHOW TABLES LIKE 'users'"))
        ck("数据库里存在 users 表", r.first() is not None)

        r = await conn.execute(text("SHOW CREATE TABLE users"))
        ddl = r.first()[1]
        print()
        print("  实际建表语句：")
        for line in ddl.split("\n"):
            print(f"    {line}")

    await engine.dispose()

    print()
    print("=" * 60)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 60)
    if F == 0:
        print("  🎉 全部通过！")


if __name__ == "__main__":
    asyncio.run(main())
