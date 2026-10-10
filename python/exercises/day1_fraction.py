"""
第 1 天练习 ②：Fraction 分数类

考点：
  - 类的定义与 __init__
  - 魔术方法：__add__ / __eq__ / __repr__
  - self 的含义
  - 用 math.gcd 做约分

运行方式：
  1. VS Code 里点右上角 ▶ 按钮
  2. 或终端执行：
     cd ~/Documents/dev/learning-notes && .venv/bin/python python/exercises/day1_fraction.py

完成标准：
  让文件末尾「自测」的输出全部符合注释里的「期望」。
"""

from math import gcd


class Fraction:
    """分数类，Fraction(1, 2) 表示 1/2"""

    # ------------------------------------------------------------
    def __init__(self, num, den):
        """
        构造：Fraction(1, 2) 会调到这里，num=1，den=2

        self 就是正在创建的这个对象。
        所以 self.num = num 的意思是「把这个对象身上的 num 属性设为 1」。
        """
        if den == 0:
            raise ValueError("分母不能为 0")

        self.num = num
        self.den = den
        self._reduce()  # 构造时立刻约分，后面比较会简单很多

    # ------------------------------------------------------------
    def _reduce(self):
        """
        约分：把 2/4 变成 1/2

        做法：分子分母同除以它们的最大公约数；
             若分母为负，把负号移到分子上（1/-2 → -1/2）。

        注意：本方法不返回任何东西，它直接修改 self 自己。
        """
        g = gcd(self.num, self.den)
        self.num = self.num // g
        self.den = self.den // g
        if self.den < 0:
            self.num, self.den = -self.num, -self.den

    # ------------------------------------------------------------
    def __add__(self, other):
        """
        a + b 时自动调用（此时 self 是 a，other 是 b）

        分数加法：a/b + c/d = (a*d + c*b) / (b*d)

        ⚠️ 返回一个【新的】Fraction 对象，不要修改 self ——
           a + b 不应该改变 a 本身。
        """
        new_num = self.num * other.den + other.num * self.den
        new_den = self.den * other.den
        return Fraction(new_num, new_den)

    # ------------------------------------------------------------
    def __eq__(self, other):
        """
        a == b 时自动调用，返回 True / False

        因为构造时已经约分过（1/2 和 2/4 都会变成 1/2），
        所以直接比较分子和分母即可。
        """
        return self.num == other.num and self.den == other.den

    # ------------------------------------------------------------
    def __repr__(self):
        """
        print(a) 时自动调用

        ⚠️ 是 return 字符串，不是 print ——
           print 会让函数返回 None，导致 TypeError。
        """
        return f"{self.num}/{self.den}"


# ================================================================
#  自测：实现完上面的方法后，输出应该和注释里的「期望」完全一致
# ================================================================
if __name__ == "__main__":
    print("=" * 44)
    print("  Fraction 自测")
    print("=" * 44)

    a = Fraction(1, 2)
    b = Fraction(1, 3)

    print(f"a             = {a}")  # 期望 1/2
    print(f"b             = {b}")  # 期望 1/3
    print(f"a + b         = {a + b}")  # 期望 5/6
    print(f"Fraction(2, 4) = {Fraction(2, 4)}")  # 期望 1/2  ← 约分生效

    print()
    print(f"a == Fraction(2, 4)  -> {a == Fraction(2, 4)}")  # 期望 True
    print(f"a == b               -> {a == b}")  # 期望 False
    print(f"1/2 + 1/2            -> {Fraction(1, 2) + Fraction(1, 2)}")  # 期望 1/1

    print()
    print("以上任何一行不符合「期望」，就说明还没做完。")


# ================================================================
#  加分挑战（做完基础题再看，选做，不写也完全没问题）
# ================================================================
#  1. 支持减法 __sub__、乘法 __mul__
#  2. 支持和整数相加：Fraction(1, 2) + 1
#     提示：在 __add__ 开头判断 other 是不是 int，是就先转成 Fraction(other, 1)
#  3. 实现 __hash__，让 Fraction 能放进 set、能当 dict 的 key
#  4. 实现 __lt__，让分数列表能排序
#  5. 思考题：Fraction(1, 2) + Fraction(1, 2) 输出 1/1 还是 1 更好？
#     想输出 1，该改哪个方法？
