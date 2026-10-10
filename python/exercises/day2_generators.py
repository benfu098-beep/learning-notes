"""
第 2 天练习 ②：生成器

考点：
  - yield 的执行流程（调用函数时不执行，next 时才跑）
  - 生成器 vs 列表的内存差异
  - itertools.islice 限制无限序列

完成标准：运行后自测全部 ✅
"""

import sys
from itertools import islice


def fib():
    """
    无限斐波那契生成器：1, 1, 2, 3, 5, 8, 13, 21, 34, 55, ...

    ⚠️ 它会无限产出，绝不能写 list(fib())，必须用 islice 或 break 限制。
    """
    a, b = 1, 1
    while True:
        yield a
        a, b = b, a + b


def first_n_squares(n: int):
    """
    产出 0 到 (n-1) 的平方：0, 1, 4, 9, 16, ...
    """
    a, b = 0, 0
    while a < n:
        yield b * b
        a += 1
        b += 1


def loud_generator():
    """演示「惰性」用的生成器（这个我已经写好了，你观察行为就行）"""
    print("      >>> 生成器开始执行了！")
    for i in range(3):
        print(f"      >>> 产出 {i}")
        yield i


if __name__ == "__main__":
    print("=" * 54)
    print("  ② 生成器自测")
    print("=" * 54)

    # ---- 1. 基本用法 ----
    print("\n【1】用 islice 取前 10 个斐波那契数")
    try:
        got = list(islice(fib(), 10))
        want = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
        print(f"   实际: {got}")
        print(f"   期望: {want}")
        print(f"   {'✅ 通过' if got == want else '❌ 不对'}")
    except NotImplementedError as e:
        print(f"   ⏳ {e}")

    # ---- 2. first_n_squares ----
    print("\n【2】first_n_squares(5)")
    try:
        got = list(first_n_squares(5))
        want = [0, 1, 4, 9, 16]
        print(f"   实际: {got}")
        print(f"   期望: {want}")
        print(f"   {'✅ 通过' if got == want else '❌ 不对'}")
    except NotImplementedError as e:
        print(f"   ⏳ {e}")

    # ---- 3. 验证「惰性」 ----
    print("\n【3】验证惰性：调用生成器函数时，函数体会不会立刻执行？")
    print("   正在创建生成器对象 g = loud_generator() …")
    g = loud_generator()
    print("   ↑ 上面【没有】任何 >>> 输出，说明函数体还没跑")
    print("   现在开始 next()：")
    for _ in g:
        pass
    print("   ✅ 结论：生成器函数调用时只创建对象，遇到 next() 才真正执行")

    # ---- 4. 内存对比 ----
    print("\n【4】内存占用对比（10 万个数字）")
    lst = [x for x in range(100_000)]
    gen = (x for x in range(100_000))
    print(f"   列表      ：{sys.getsizeof(lst):>8,} 字节")
    print(f"   生成器表达式：{sys.getsizeof(gen):>8,} 字节")
    print("   ↑ 生成器几乎不占内存，因为它不把所有元素都造出来")

    print()
    print("   注意：上面用的是「生成器表达式」(x for x in ...)，圆括号，")
    print("        和列表推导式 [x for x in ...] 只差一个括号，但内存差几十万倍。")
