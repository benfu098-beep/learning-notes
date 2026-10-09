"""
第 1 天练习 ③：用 @dataclass 写 Student 类

考点：
  - @dataclass 自动生成 __init__ / __repr__ / __eq__
  - field(default_factory=...) 为什么是必须的  ← 和练习④是同一个坑！
  - @property 计算属性

完成标准：
  运行文件末尾的自测，每一行都符合注释里的「期望」。
"""

from dataclasses import dataclass, field


@dataclass
class Student:
    """学生：姓名、年龄、成绩列表"""

    name: str
    age: int
    scores: list[float] = field(default_factory=list)
    #                       ↑
    #   ⚠️ 为什么不能直接写 scores: list[float] = [] ？
    #      先做完练习④，你就彻底明白了。

    # ------------------------------------------------------------
    @property
    def average(self) -> float:
        """
        平均分（计算属性，用的时候不带括号：s.average）

        TODO: 在这里写代码（把 raise 删掉）

        提示：
          - 没有成绩时返回 0.0，避免除以 0 报错
          - 有成绩时返回 sum(self.scores) / len(self.scores)
        """
        if not self.scores:
            return 0.0
        return sum(self.scores) / len(self.scores)

    # ------------------------------------------------------------
    def add_score(self, score: float) -> None:
        """
        加一个成绩

        TODO: 一行搞定（把 raise 删掉）
        """
        self.scores.append(score)


# ================================================================
#  自测
# ================================================================
if __name__ == "__main__":
    print("=" * 52)
    print("  Student 自测")
    print("=" * 52)

    s1 = Student("小明", 20, [90, 80, 100])
    print(
        f"s1                        = {s1}"
    )  # 期望 Student(name='小明', age=20, scores=[90, 80, 100])
    print(f"s1.average                = {s1.average}")  # 期望 90.0
    print()
    print(f"没成绩时的 average         = {Student('小刚', 19).average}")  # 期望 0.0
    print()
    print(
        f"s1 == Student('小红',21,[90,80,100]) -> {s1 == Student('小红', 21, [90, 80, 100])}"
    )  # 期望 False
    print(
        f"s1 == Student('小明',20,[90,80,100]) -> {s1 == Student('小明', 20, [90, 80, 100])}"
    )  # 期望 True

    print()
    print("-" * 52)
    print("  ⭐ 关键测试：默认参数有没有被所有实例共享？")
    print("-" * 52)
    a = Student("A", 18)
    b = Student("B", 18)
    a.add_score(100)
    print(f"a.scores = {a.scores}   # 期望 [100]")
    print(f"b.scores = {b.scores}   # 期望 []     ← 如果这里是 [100]，说明踩坑了")
    print()
    if a.scores == [100] and b.scores == []:
        print("  ✅ 通过：两个实例的成绩列表是独立的")
    else:
        print("  ❌ 未通过：两个实例共享了同一个列表")
        print("     检查一下是不是把 field(default_factory=list) 写成了 = []")


# ================================================================
#  加分挑战（选做）
# ================================================================
#  1. 加一个 letter_grade 属性：平均分 >=90 返回 "A"，>=80 返回 "B"...
#  2. 加一个 highest 属性返回最高分（空列表返回 None）
#  3. 想想：@dataclass 默认生成的 __eq__ 比较了哪些字段？
#     如果只想按 name 判断相等，该怎么办？（提示：eq=False + 自己写）
