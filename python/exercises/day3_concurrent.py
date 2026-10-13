"""
第 3 天练习 ②：把串行改成并发

任务：
  下面的 main() 现在是【串行】的，耗时约 3 秒。
  把它改成并发，让耗时降到约 1 秒。

完成标准：
  自测显示「✅ 通过」（耗时 < 1.5 秒，且三个结果都正确）

提示：
  · 想想 asyncio.gather 怎么用
  · 改成并发后，返回值要还是 [r1, r2, r3] 这个顺序
"""

import asyncio
import time

TARGET = 1.5  # 耗时低于这个值算通过（串行是 3 秒）


async def task(name, sec):
    await asyncio.sleep(sec)
    return f"{name} done"


async def main():
    t0 = time.perf_counter()

    # TODO: 把下面三行【串行】的 await 改成【并发】
    results = await asyncio.gather(
        task("A", 1),
        task("B", 1),
        task("C", 1),
    )
    cost = time.perf_counter() - t0
    return results, cost


if __name__ == "__main__":
    print("=" * 56)
    print("  ② 串行 → 并发 自测")
    print("=" * 56)

    results, cost = asyncio.run(main())

    print(f"\n  返回值: {results}")
    print(f"  耗时:   {cost:.2f} 秒   （目标 < {TARGET} 秒）")
    print()

    want = ["A done", "B done", "C done"]
    ok_result = results == want
    ok_time = cost < TARGET

    print(f"  {'✅' if ok_result else '❌'} 结果正确（顺序应为 {want}）")
    print(f"  {'✅' if ok_time else '❌'} 耗时达标（实际 {cost:.2f} 秒）")
    print()
    if ok_result and ok_time:
        print("  🎉 通过！你已经会用 asyncio.gather 做并发了。")
    else:
        print("  还没通过。提示：三个 await 排成一排就是串行，")
        print("  要让它们同时开始 —— 想想 asyncio.gather。")
