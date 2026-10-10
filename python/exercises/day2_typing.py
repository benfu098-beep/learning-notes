"""
第 2 天练习 ⑤：类型提示（⭐ 最重要，FastAPI 的命脉）

考点：
  - 基本注解、容器泛型、`str | None`
  - 类型提示【运行时不做检查】
  - 用 mypy 做静态检查

三个任务：
  1. 给 process_users 补全类型注解
  2. 观察「类型提示不做运行时检查」
  3. 用 mypy 检查，让错误暴露出来

完成标准：
  · mypy 检查通过（0 error）
  · 做完后你能解释：类型提示到底是谁在用？
"""

from typing import TypedDict


class User(TypedDict):
    """一个用户的结构（TypedDict 用来给字典定义「形状」）"""
    name: str
    role: str


# ================================================================
#  任务 1：给这个函数补全类型注解
# ================================================================
def process_users(users, default_role, verbose):
    """
    TODO: 给参数和返回值补上类型注解

    参数：
      users        —— 用户列表，类型是 list[User]
      default_role —— 默认角色，类型是 str
      verbose      —— 是否打印，类型是 bool

    返回：
      dict[str, str]   —— 映射：姓名 → 角色

    写法参考（Python 3.10+ 推荐）：

        def process_users(
            users: list[User],
            default_role: str,
            verbose: bool,
        ) -> dict[str, str]:
    """
    result = {}
    for u in users:
        result[u["name"]] = u.get("role", default_role)
    if verbose:
        print(f"   处理了 {len(result)} 个用户")
    return result


# ================================================================
#  任务 2：验证「类型提示运行时不做检查」
# ================================================================
def add(a: int, b: int) -> int:
    """这个函数的注解说得明明白白：只接受 int，返回 int"""
    return a + b


if __name__ == "__main__":
    print("=" * 58)
    print("  ⑤ 类型提示自测")
    print("=" * 58)

    # ---------- 任务 1 ----------
    print("\n【任务 1】process_users 正常工作")
    data: list[User] = [
        {"name": "benfu", "role": "dev"},
        {"name": "lily", "role": "pm"},
    ]
    got = process_users(data, "guest", True)
    want = {"benfu": "dev", "lily": "pm"}
    print(f"   结果: {got}")
    print(f"   {'✅ 通过' if got == want else '❌ 不对'}")

    # ---------- 任务 2 ----------
    print("\n【任务 2】类型提示运行时不做检查（重点！）")
    print("   add 的注解是 (a: int, b: int) -> int")
    print("   现在我们传两个字符串进去：")
    result = add("hello", "world")
    print(f'   add("hello", "world") = {result!r}')
    print("   ↑ 没有报错！Python 解释器压根不看类型注解")

    # ---------- 任务 3 ----------
    print("\n【任务 3】要发现问题，必须用静态检查工具")
    print("   在终端里执行：")
    print()
    print("     cd ~/Documents/dev/learning-notes")
    print("     .venv/bin/python -m mypy python/exercises/day2_typing.py")
    print()
    print("   如果注解补全了，会看到：Success: no issues found")
    print("   如果故意传错类型，mypy 会报 error（但程序照样能跑）")

    print()
    print("=" * 58)
    print("  💡 核心认知")
    print("=" * 58)
    print("  类型提示是给【工具】和【框架】看的，不是给解释器看的：")
    print("    · mypy / ruff  → 静态检查，提前发现 bug")
    print("    · FastAPI      → 读注解自动做参数校验、生成 API 文档")
    print("    · Pydantic     → 读注解做数据校验和序列化")
    print()
    print("  所以对你要走的方向来说，类型提示不是「风格问题」，是硬性要求。")
