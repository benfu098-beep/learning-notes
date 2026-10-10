"""
第 2 天练习 ④：上下文管理器

考点：
  - with 语句保证「无论如何都执行清理」
  - contextlib.contextmanager + yield 的位置语义
  - 为什么不能吞掉异常

任务：用 @contextmanager 实现 db_transaction()
  - 进入时打印 "BEGIN"
  - with 块正常结束 → 打印 "COMMIT"
  - with 块抛异常   → 打印 "ROLLBACK"，并把异常【重新抛出】

完成标准：两个场景的自测都符合期望
"""

from contextlib import contextmanager


@contextmanager
def db_transaction():
    """
    TODO: 实现它（把 raise 删掉）

    提示：

        @contextmanager
        def db_transaction():
            print("BEGIN")
            try:
                yield              ← 控制权交给 with 代码块
            except Exception:
                print("ROLLBACK")
                raise              ← ⚠️ 必须重新抛出！否则异常被吞掉
            else:
                print("COMMIT")

    理解 yield 的位置：
      · yield 之前的代码  ≈ __enter__（进入 with 时执行）
      · yield 之后的代码  ≈ __exit__（离开 with 时执行）
      · yield 本身会把控制权交给 with 代码块，等它跑完再回来

    ⚠️ 在 except 里只 print 不 raise，调用方就永远不知道出错了。
       这是很危险的做法，生产代码里绝对不能这么写。
    """
    print("BEGIN")
    try:
        yield
    except Exception:
        print("ROLLBACK")
        raise
    else:
        print("COMMIT")


if __name__ == "__main__":
    print("=" * 54)
    print("  ④ 上下文管理器自测")
    print("=" * 54)

    # ---------- 场景 1：正常结束 ----------
    print("\n【场景 1】with 块正常执行完")
    try:
        print("   --- with 开始 ---")
        with db_transaction():
            print("   >>> 执行业务操作（写数据库）")
        print("   --- with 结束 ---")
        print("   期望顺序：BEGIN → 业务操作 → COMMIT")
        print("   ✅ 如果上面就是这个顺序，通过")
    except NotImplementedError as e:
        print(f"   ⏳ {e}")

    # ---------- 场景 2：中途抛异常 ----------
    print("\n【场景 2】with 块中途抛异常")
    try:
        print("   --- with 开始 ---")
        with db_transaction():
            print("   >>> 执行业务操作")
            raise ValueError("模拟业务出错")
        print("   ❌ 不对：异常被吞掉了，外面没感知到")
    except NotImplementedError:
        print("   ⏳ 还没实现")
    except ValueError as e:
        print("   --- 异常正确传播到了外面 ---")
        print(f"   ✅ 通过：收到 {type(e).__name__}: {e}")
        print("   期望顺序：BEGIN → 业务操作 → ROLLBACK → 异常抛出")
    except Exception as e:
        print(f"   ❌ 异常类型不对：{type(e).__name__}: {e}")

    # ---------- 场景 3：验证「一定会清理」 ----------
    print("\n【场景 3】对比：不用 with 会怎样")
    print("   不用 with 时，如果中间抛异常，close() 就永远不会被调用")
    print("   用 with 时，无论正常还是异常，清理代码都会执行")
    print("   ✅ 这就是上下文管理器存在的意义")
