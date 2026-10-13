"""
第 3 天练习 ①：感受「阻塞事件循环」（Day 3 最重要的一课）

任务：
  1. 直接运行，看两种写法的耗时对比
  2. 跑之前先【猜一下】：两种写法各要多久？
  3. 把预测和实际填进文件末尾的「我的记录」

核心结论：
  在 async def 里调用【同步阻塞】函数，会卡死整个事件循环。
"""

import asyncio
import time


# ================================================================
#  A. 错误写法：async def 里用【同步阻塞】的 time.sleep
# ================================================================
async def blocking_task(name, delay):
    time.sleep(delay)              # ❌ 阻塞！这期间事件循环完全停摆
    return f"{name} 完成"


async def run_blocking():
    t0 = time.perf_counter()
    results = await asyncio.gather(
        blocking_task("A", 1),
        blocking_task("B", 1),
        blocking_task("C", 1),
    )
    return results, time.perf_counter() - t0


# ================================================================
#  B. 正确写法：用【异步】的 await asyncio.sleep
# ================================================================
async def async_task(name, delay):
    await asyncio.sleep(delay)     # ✅ 等待时让出控制权，别的任务能跑
    return f"{name} 完成"


async def run_async():
    t0 = time.perf_counter()
    results = await asyncio.gather(
        async_task("A", 1),
        async_task("B", 1),
        async_task("C", 1),
    )
    return results, time.perf_counter() - t0


async def main():
    print("=" * 62)
    print("  三个任务，每个都需要 1 秒")
    print("=" * 62)

    print("\n  正在跑 A（time.sleep）……")
    _, cost_bad = await run_blocking()
    print(f"  A. time.sleep()            → {cost_bad:.2f} 秒")

    print("\n  正在跑 B（await asyncio.sleep）……")
    _, cost_good = await run_async()
    print(f"  B. await asyncio.sleep()   → {cost_good:.2f} 秒")

    print()
    print("=" * 62)
    print(f"  A 比 B 慢 {cost_bad / cost_good:.1f} 倍")
    print("=" * 62)
    print("""
  为什么？

    time.sleep()      是【同步阻塞】—— 它让整个事件循环干等着，
                      其他两个任务一点机会都没有，只能排队。

    asyncio.sleep()   会主动【让出控制权】—— 事件循环立刻转去跑
                      其他任务，等时间到了再回来。

  一句话：异步的前提是「等待时要让出控制权」。
          同步阻塞函数不让出，异步就退化成串行。
""")

    # 判定
    print("-" * 62)
    if cost_bad >= 2.9:
        print("  ✅ A 耗时约 3 秒 —— 符合预期（串行了）")
    if cost_good <= 1.2:
        print("  ✅ B 耗时约 1 秒 —— 符合预期（真并发）")


# ================================================================
#  我的记录（自己填）
# ================================================================
#  跑之前我的预测：
#    A (time.sleep)          = ______ 秒
#    B (asyncio.sleep)       = ______ 秒
#
#  实际结果：
#    A = ______ 秒    B = ______ 秒
#
#  用你自己的话解释为什么 A 会慢（不许抄上面的）：
#
#
#
#  ⭐ 进阶思考：如果把 time.sleep 换成 requests.get()，
#     或者一个很耗 CPU 的循环（比如算 100 万次素数），
#     在 async def 里会怎样？该怎么解决？
#     （提示：asyncio.to_thread / 多进程）


if __name__ == "__main__":
    asyncio.run(main())
