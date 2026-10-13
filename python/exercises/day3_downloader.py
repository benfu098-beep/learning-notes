"""
第 3 天练习 ③：并发下载器（实战版）

任务：
  1. 实现 fetch_one()  —— 请求单个 URL，带异常处理
  2. 实现 fetch_all_concurrent()  —— 并发请求 10 个 URL，带整体超时
  3. 对比「串行」和「并发」的耗时

完成标准：
  · 10 个请求都拿到结果（成功的成功，失败的被正确记录，不中断）
  · 并发耗时明显小于串行

⚠️ 注意：只创建【一个】AsyncClient，让所有请求复用它（连接池）。
   每个请求都新建 client 是常见错误，会慢很多。
"""

import asyncio
import time

import httpx

URLS = [f"https://jsonplaceholder.typicode.com/posts/{i}" for i in range(1, 11)]


# ================================================================
#  任务 1：请求单个 URL
# ================================================================
async def fetch_one(client: httpx.AsyncClient, url: str) -> dict:
    """
    请求单个 URL，返回结果摘要。任何异常都不能往外抛。

    成功时返回： {"url": url, "ok": True,  "bytes": <响应体字节数>}
    失败时返回： {"url": url, "ok": False, "error": "<异常类型>: <信息>"}

    TODO: 实现它（把 raise 删掉）

    提示：

        try:
            resp = await client.get(url)
            resp.raise_for_status()        # 非 2xx 会抛 httpx.HTTPStatusError
            return {"url": url, "ok": True, "bytes": len(resp.content)}
        except Exception as e:
            return {"url": url, "ok": False, "error": f"{type(e).__name__}: {e}"}

    ⚠️ 关键是【不让异常冒出去】—— 否则 gather 会因为一个失败而整体崩掉。
    """
    try:
        resp = await client.get(url)
        resp.raise_for_status()
        return {"url": url, "ok": True, "bytes": len(resp.content)}
    except Exception as e:
        return {"url": url, "ok": False, "error": f"{type(e).__name__}: {e}"}


# ================================================================
#  任务 2：并发请求全部 URL
# ================================================================
async def fetch_all_concurrent() -> tuple[list, float]:
    """
    并发请求 URLS 里的所有地址。

    返回： (结果列表, 耗时秒数)

    TODO: 实现它（把 raise 删掉）

    提示：

        t0 = time.perf_counter()
        async with httpx.AsyncClient(timeout=3.0) as client:
            async with asyncio.timeout(3):                  # 整体超时保护
                results = await asyncio.gather(
                    *(fetch_one(client, u) for u in URLS)
                )
        return list(results), time.perf_counter() - t0

    注意：
      · client 只建一个，放在 async with 里，所有请求共用
      · asyncio.timeout 是 Python 3.11+ 的写法（你用的是 3.12）
    """
    t0 = time.perf_counter()
    async with httpx.AsyncClient(timeout=3.0) as client:
        async with asyncio.timeout(3):  # 整体超时保护
            results = await asyncio.gather(*(fetch_one(client, u) for u in URLS))
    return list(results), time.perf_counter() - t0


# ================================================================
#  对比用：串行版本（已写好，不要改）
# ================================================================
async def fetch_all_serial() -> tuple[list, float]:
    t0 = time.perf_counter()
    results = []
    async with httpx.AsyncClient(timeout=3.0) as client:
        for url in URLS:
            results.append(await fetch_one(client, url))
    return results, time.perf_counter() - t0


# ================================================================
#  自测
# ================================================================
async def main():
    print("=" * 62)
    print("  ③ 并发下载器自测")
    print("=" * 62)
    print(f"  目标：{len(URLS)} 个 URL\n")

    # ---- 第 1 步：单个请求 ----
    print("【第 1 步】fetch_one 能工作吗")
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            one = await fetch_one(client, URLS[0])
        print(f"  → {one}")
        if one.get("ok"):
            print("  ✅ 单个请求成功")
        else:
            print(f"  ⚠️ 请求失败但被正确记录：{one.get('error')}")
    except NotImplementedError:
        print("  ⏳ fetch_one 还没实现，先做任务 1")
        return

    # ---- 第 2 步：并发 ----
    print("\n【第 2 步】并发请求全部")
    try:
        results, cost_concurrent = await fetch_all_concurrent()
    except NotImplementedError:
        print("  ⏳ fetch_all_concurrent 还没实现，做任务 2")
        return

    ok = sum(1 for r in results if r.get("ok"))
    print(f"  成功 {ok}/{len(URLS)}   耗时 {cost_concurrent:.2f} 秒")
    if ok == len(URLS):
        print("  ✅ 全部成功")
    else:
        for r in results:
            if not r.get("ok"):
                print(f"  ⚠️ 失败：{r['url']} → {r.get('error')}")

    # ---- 第 3 步：对比串行 ----
    print("\n【第 3 步】串行 vs 并发")
    _, cost_serial = await fetch_all_serial()
    print(f"  串行耗时：{cost_serial:.2f} 秒")
    print(f"  并发耗时：{cost_concurrent:.2f} 秒")
    if cost_concurrent > 0:
        print(f"  加速比：  {cost_serial / cost_concurrent:.1f}x")

    print()
    print("=" * 62)
    if ok == len(URLS) and cost_concurrent < cost_serial:
        print("  🎉 通过！并发确实比串行快。")
    else:
        print("  还没完全通过，检查上面哪一步不对。")
    print("=" * 62)


if __name__ == "__main__":
    asyncio.run(main())
