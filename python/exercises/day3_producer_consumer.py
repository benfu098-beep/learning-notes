"""
第 3 天练习 ④：生产者-消费者（asyncio.Queue）

场景：
  一个生产者不断往队列里放任务，两个消费者并发从队列里取任务处理。

任务：
  1. 实现 producer()  —— 放 5 个数字，最后放【两个 None】当结束信号
  2. 实现 consumer()  —— 不断取，直到拿到 None 就退出

完成标准：
  · 两个消费者并发处理（输出会交错）
  · 5 个数字全被处理，且没有被处理两次
  · 总耗时明显小于串行（生产者 2.5 秒 + 消费者 1.5 秒）

⚠️ 经典陷阱：2 个消费者就需要 2 个结束信号。
   只放 1 个 None 的话，另一个消费者会永远卡在 get() 上。
"""

import asyncio
import time

PRODUCE_COUNT = 5
CONSUMER_COUNT = 2


# ================================================================
#  任务 1：生产者
# ================================================================
async def producer(queue: asyncio.Queue) -> None:
    """
    每 0.5 秒往队列放一个数字（0 到 PRODUCE_COUNT-1），
    最后放 CONSUMER_COUNT 个 None 作为结束信号。

    TODO: 实现它（把 raise 删掉）

    提示：

        for i in range(PRODUCE_COUNT):
            await asyncio.sleep(0.5)
            await queue.put(i)
            print(f"  [生产者] 放入 {i}")

        for _ in range(CONSUMER_COUNT):      # ⚠️ 每个消费者一个
            await queue.put(None)
        print("  [生产者] 结束")

    注意：queue.put() 是【异步】的（队列满时会等待），要写 await。
    """
    raise NotImplementedError("请实现 producer")


# ================================================================
#  任务 2：消费者
# ================================================================
async def consumer(name: str, queue: asyncio.Queue) -> list:
    """
    不断从队列取数字，每处理一个花 0.3 秒，直到拿到 None（结束信号）退出。

    返回：这个消费者处理过的所有数字组成的列表

    TODO: 实现它（把 raise 删掉）

    提示：

        got = []
        while True:
            item = await queue.get()         # 异步取
            if item is None:                 # 结束信号
                print(f"  [{name}] 收到结束信号，退出")
                break
            got.append(item)
            print(f"  [{name}] 处理 {item}")
            await asyncio.sleep(0.3)         # 模拟处理耗时
        return got

    注意：queue.get() 也是异步的。
    """
    raise NotImplementedError("请实现 consumer")


# ================================================================
#  自测
# ================================================================
async def main():
    print("=" * 62)
    print("  ④ 生产者-消费者 自测")
    print("=" * 62)

    queue: asyncio.Queue = asyncio.Queue()
    t0 = time.perf_counter()

    try:
        results = await asyncio.gather(
            producer(queue),
            consumer("消费者-1", queue),
            consumer("消费者-2", queue),
        )
    except NotImplementedError as e:
        print(f"\n  ⏳ {e}")
        return

    cost = time.perf_counter() - t0
    got1, got2 = results[1], results[2]
    all_got = sorted(got1 + got2)

    print()
    print("-" * 62)
    print(f"  消费者-1 处理了：{sorted(got1)}")
    print(f"  消费者-2 处理了：{sorted(got2)}")
    print(f"  总共处理：      {all_got}")
    print(f"  总耗时：        {cost:.2f} 秒")
    print()

    want = list(range(PRODUCE_COUNT))
    ok_all = all_got == want
    ok_no_dup = len(all_got) == len(set(all_got))
    ok_time = cost < 4.0

    print(f"  {'✅' if ok_all else '❌'} 5 个数字全部被处理")
    print(f"  {'✅' if ok_no_dup else '❌'} 没有重复处理")
    print(f"  {'✅' if ok_time else '❌'} 耗时合理（{cost:.2f} 秒 < 4 秒）")
    print()
    if ok_all and ok_no_dup and ok_time:
        print("  🎉 通过！你已经会用 asyncio.Queue 做生产者-消费者了。")


if __name__ == "__main__":
    asyncio.run(main())
