"""
W3 练习 5：关系与异步加载

这个练习分四步：
  ① 定义一对多关系（ForeignKey + relationship）
  ② 【故意踩坑】不加预加载，触发 MissingGreenlet 报错
  ③ 用 selectinload 修复
  ④ 用 joinedload 从子查父

完成标准：自测全部 ✅

参考讲义：python/05d-relationship.md

⚠️ 任务 2 的"失败"是【预期行为】——自测会检查它确实报错，
   证明你理解了"异步里不能懒加载"。
"""

import asyncio

from sqlalchemy import ForeignKey, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    joinedload,
    mapped_column,
    relationship,
    selectinload,
)

DATABASE_URL = "mysql+aiomysql://root:123456@127.0.0.1:3306/learning_notes"


class Base(DeclarativeBase):
    pass


# ================================================================
#  任务 1：定义关系
# ================================================================
class User(Base):
    __tablename__ = "rel_users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)

    # TODO 1: 加 articles 关系
    # articles: Mapped[list["Article"]] = relationship(back_populates="author")


class Article(Base):
    __tablename__ = "rel_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))

    # TODO 2: 加 author_id（外键，指向 User.id）
    # author_id: Mapped[int] = mapped_column(ForeignKey("rel_users.id"))

    # TODO 3: 加 author 关系（反向）
    # author: Mapped["User"] = relationship(back_populates="articles")


# ================================================================
#  任务 4：不加预加载 —— 预期会崩
# ================================================================
async def lazy_load_broken(session: AsyncSession, user_id: int):
    """
    故意不预加载，直接访问 user.articles。

    要求：按下面这样写（就是要它崩）

        user = await session.get(User, user_id)
        return [a.title for a in user.articles]      # ← 这里会抛 MissingGreenlet

    TODO: 实现它（照上面两行写）

    这个函数【不会】成功，自测会检查它抛出了 MissingGreenlet。
    """
    raise NotImplementedError("请实现 lazy_load_broken")


# ================================================================
#  任务 5：用 selectinload 修复
# ================================================================
async def load_with_articles(session: AsyncSession, user_id: int) -> list[str]:
    """
    TODO: 用 selectinload 预加载，返回该用户所有文章的标题列表

    提示：
        stmt = (
            select(User)
            .options(selectinload(User.articles))
            .where(User.id == user_id)
        )
        user = (await session.execute(stmt)).scalar_one_or_none()
        if user is None:
            return []
        return [a.title for a in user.articles]

    注意：这里能成功，是因为 selectinload 在【查询时】就把 articles 捞进来了，
          后面访问 user.articles 不再发 SQL。
    """
    raise NotImplementedError("请实现 load_with_articles")


# ================================================================
#  任务 6：用 joinedload 从子查父
# ================================================================
async def load_article_with_author(session: AsyncSession, article_id: int):
    """
    TODO: 查一篇文章，同时把它的 author 加载出来，返回 author 的 username

    提示：
        stmt = (
            select(Article)
            .options(joinedload(Article.author))
            .where(Article.id == article_id)
        )
        article = (await session.execute(stmt)).scalar_one_or_none()
        if article is None:
            return None
        return article.author.username

    为什么这里用 joinedload 而不是 selectinload？
      因为"多对一"：一篇文章只有一个作者，JOIN 不会产生数据膨胀。
    """
    raise NotImplementedError("请实现 load_article_with_author")


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

    # ---------- 任务 1：模型检查 ----------
    print("=" * 66)
    print("  任务 1：关系定义")
    print("=" * 66)
    ck("User 有 articles 关系", hasattr(User, "articles"),
       "缺 relationship(back_populates='author')")
    ck("Article 有 author 关系", hasattr(Article, "author"),
       "缺 relationship(back_populates='articles')")
    has_fk = any(fk.target_fullname == "rel_users.id" for fk in Article.__table__.foreign_keys)
    ck("Article.author_id 是指向 rel_users.id 的外键", has_fk, "缺 ForeignKey('rel_users.id')")

    if F:
        print("\n  先修好模型再继续。")
        await engine.dispose()
        return

    # ---------- 准备数据 ----------
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS rel_articles"))
        await conn.execute(text("DROP TABLE IF EXISTS rel_users"))
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as s:
        u = User(username="benfu")
        s.add(u)
        await s.commit()
        await s.refresh(u)
        uid = u.id
        s.add_all([
            Article(title="第一篇文章", author_id=uid),
            Article(title="第二篇文章", author_id=uid),
            Article(title="第三篇文章", author_id=uid),
        ])
        await s.commit()
    print(f"\n  · 已造数据：1 个用户（id={uid}）、3 篇文章")

    # ---------- 任务 4：故意崩 ----------
    print()
    print("=" * 66)
    print("  任务 4：不加预加载 → 应该崩")
    print("=" * 66)
    try:
        async with Session() as s:
            await lazy_load_broken(s, uid)
        print("  ⚠️ 竟然没崩？说明关系没生效（或 lazy='select' 没触发）")
        F += 1
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return
    except Exception as e:
        name = type(e).__name__
        if "MissingGreenlet" in name or "MissingGreenlet" in str(e):
            print(f"  ✅ 成功触发 {name}（这正是我们想让你看到的）")
            print("     ↑ 异步里访问未加载的关系 → 隐式 IO → 报错")
            P += 1
        else:
            print(f"  ⚠️ 抛了别的异常：{name}: {str(e)[:80]}")
            F += 1

    # ---------- 任务 5：selectinload ----------
    print()
    print("=" * 66)
    print("  任务 5：selectinload 预加载 → 应该成功")
    print("=" * 66)
    try:
        async with Session() as s:
            titles = await load_with_articles(s, uid)
        print(f"  拿到 {len(titles)} 篇：{titles}")
        ck("返回 3 篇文章", len(titles) == 3, f"实际 {len(titles)}")
        ck("标题正确", set(titles) == {"第一篇文章", "第二篇文章", "第三篇文章"}, str(titles))
    except NotImplementedError as e:
        print(f"  ⏳ {e}")
        await engine.dispose()
        return

    # ---------- 任务 6：joinedload ----------
    print()
    print("=" * 66)
    print("  任务 6：joinedload 从文章查作者")
    print("=" * 66)
    try:
        async with engine.connect() as conn:
            r = await conn.execute(text("SELECT id FROM rel_articles ORDER BY id LIMIT 1"))
            aid = r.scalar()
        async with Session() as s:
            name = await load_article_with_author(s, aid)
        print(f"  文章 id={aid} 的作者是：{name}")
        ck("能通过 article.author 拿到用户名", name == "benfu", f"实际 {name!r}")
        async with Session() as s:
            none_name = await load_article_with_author(s, 99999)
        ck("文章不存在返回 None", none_name is None, f"实际 {none_name!r}")
    except NotImplementedError as e:
        print(f"  ⏳ {e}")

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS rel_articles"))
        await conn.execute(text("DROP TABLE IF EXISTS rel_users"))
    await engine.dispose()

    print()
    print("=" * 66)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 66)
    if F == 0 and P > 0:
        print("  🎉 全部通过！你已经掌握异步 ORM 的关系加载了。")
    print()
    print("  💡 记住这个报错：MissingGreenlet")
    print("     → 看到它，第一反应就是「关系没预加载」")
    print("     → 一对多用 selectinload，多对一用 joinedload")


if __name__ == "__main__":
    asyncio.run(main())
