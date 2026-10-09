"""
第 1 天练习 ④：可变默认参数（Python 最著名的坑之一，面试高频）

任务：
  1. 先运行这个文件，观察 ① 的输出
  2. 用你自己的话解释「为什么」，写在下面的 EXPLANATION 区域
  3. 实现 collect_right，让三次调用互不影响

完成标准：
  运行后 ② 显示「✅ 修复成功」
"""


# ================================================================
#  ① 有问题的版本（别改它，留着做对比）
# ================================================================
def collect_wrong(x, acc=[]):
    acc.append(x)
    return acc


# ================================================================
#  ② 正确版本 —— TODO: 你来写
# ================================================================
def collect_right(x, acc=None):
    """
    提示：
      1. 判断 acc 是不是 None
      2. 是的话，在里面新建一个列表（注意：不能写在参数默认值里！）
      3. append，然后 return
    """
    if acc is None:
        acc = []
        acc.append(x)
    return acc


# ================================================================
#  EXPLANATION —— 用你自己的话解释，不许抄讲义
# ================================================================
#
#  思考角度：
#    · 默认值 [] 是在【函数定义时】创建的，还是【每次调用时】创建的？
#    · 三次调用拿到的 acc，是同一个列表对象还是三个不同的？
#      （运行时看下面打印的 id 就知道了）
#    · 为什么把默认值改成 None 就能解决？
#
#  ── 你的解释（写在这里）──────────────────────────────
# 函数定义时
# 同一个列表对象
# 因为每次调用时都会创建一个新的列表对象，而不是使用同一个默认值对象。
#
#  ──────────────────────────────────────────────────


# ================================================================
#  自测
# ================================================================
if __name__ == "__main__":
    print("=" * 54)
    print("  ① 有问题的版本")
    print("=" * 54)
    print(f"  collect_wrong(1) = {collect_wrong(1)}")
    print(f"  collect_wrong(2) = {collect_wrong(2)}")
    print(f"  collect_wrong(3) = {collect_wrong(3)}")
    print()
    print("  ⚠️ 期望是 [1] / [2] / [3]，但实际不是。")
    print(f"  默认值对象的内存地址（三次调用完全一样）：")
    print(
        f"    id(collect_wrong.__defaults__[0]) = {id(collect_wrong.__defaults__[0])}"
    )
    print()
    print("  ↑ 这就是证据：三次调用用的是【同一个列表对象】")

    print()
    print("=" * 54)
    print("  ② 你的修复版本")
    print("=" * 54)
    try:
        r1 = collect_right(1)
        r2 = collect_right(2)
        r3 = collect_right(3)
        print(f"  collect_right(1) = {r1}")
        print(f"  collect_right(2) = {r2}")
        print(f"  collect_right(3) = {r3}")
        print()
        if r1 == [1] and r2 == [2] and r3 == [3]:
            print("  ✅ 修复成功！三次调用互不影响。")
        else:
            print("  ❌ 还不对，期望是 [1] / [2] / [3]")
    except NotImplementedError as e:
        print(f"  ⏳ 还没实现：{e}")

    print()
    print("=" * 54)
    print("  💡 做完后回头看练习③的这一行：")
    print("     scores: list[float] = field(default_factory=list)")
    print("  现在你应该能解释为什么要用 field(default_factory=...)")
    print("  而不能直接写 = [] 了。")
    print("=" * 54)
