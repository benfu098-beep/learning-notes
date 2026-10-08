"""
第 0 天：环境自检
目的：确认 VS Code + Python 能正常跑起来。

运行方式（三选一）：
  1. VS Code 里点右上角的 ▶ 按钮
  2. VS Code 里右键 → Run Python File in Terminal
  3. 终端里执行： cd ~/Documents/dev/learning-notes && .venv/bin/python python/exercises/day0_hello.py

看到「环境 OK」就说明一切正常，可以开始第 1 天讲义了。
"""

import sys
from datetime import datetime

# ---- 1. 基本输出（对比 C 的 printf / C++ 的 cout）----
print("=" * 46)
print("  Python 环境自检")
print("=" * 46)

print(f"Python 版本：{sys.version.split()[0]}")
print(f"解释器路径：{sys.executable}")
print(f"当前时间：{datetime.now():%Y-%m-%d %H:%M:%S}")

# ---- 2. 感受一下 Python 和 C/C++ 的差异 ----
print("\n--- 顺便感受 Python 的写法 ---")

# 推导式：C++ 里要 for 循环 + push_back
squares = [x * x for x in range(1, 6)]
print(f"1~5 的平方（列表推导式）：{squares}")

# 字典：查找是 O(1)
scores = {"算法": 90, "Python": 85}
print(f"字典取值（.get 更安全）：{scores.get('数据库', '暂无')}")

# f-string：比 printf 好看
name, age = "benfu", 20
print(f"f-string 示例：{name} 今年 {age} 岁")

# ---- 3. 确认能写文件（后面要写笔记）----
print("\n--- 自检结果 ---")
print("✅ 环境 OK，可以开始第 1 天讲义了！")
print("\n下一步：打开 python/01-mindset-and-oop.md")
