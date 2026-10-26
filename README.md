# learning-notes

2028 届 CS 学生的求职学习笔记。目标：**2027 年 3–5 月拿到暑期实习 offer（AI 应用开发 / Python 后端）**。

## ▶️ 下次从这里开始（2026-10-26 周一）

> **⚠️ 计划已调整**：10/15–10/26 因期中考试中断 11 天，W2–W5 压缩，
> 但**项目 A 开始时间（11/16）一天不动**。原 W5 的「练手项目」已砍掉。

**当前进度**：W2 练习 1 完成了 1/3（任务 1 路径参数 ✅）

### 今天要做的事（约 2 小时，做完 W2 就追上了）

- [ ] **1. 任务 2：查询参数**（2 行）—— [w2_01_routing.py](python/exercises/w2_01_routing.py)
      ```python
      data = [x for x in ITEMS if q in x["name"]] if q else ITEMS
      return {"total": len(data), "items": data[skip : skip + limit]}
      ```
      对照视频 **P7**
- [ ] **2. 任务 3：请求体**（1 行）
      ```python
      return {"created": item.model_dump()}
      ```
      对照视频 **P8、P9**
- [ ] **3. 跑自测** → 看到 `通过 13  失败 0`
- [ ] **4. 提交** → `git add -A && git commit -m "完成 W2 练习1" && git push`
- [ ] **5. （有余力）做 w2_02_pydantic.py**

### 运行命令（记住：用 .venv 的 python）

```bash
cd ~/Documents/dev/learning-notes
.venv/bin/python python/exercises/w2_01_routing.py
```

### 调整后的时间表

| 周 | 日期 | 内容 | 备注 |
|---|---|---|---|
| ~~W0–W1~~ | 10/08–10/18 | 地基：Python 速通 + asyncio | ✅ 完成 |
| **W2 收尾** | **10/26–10/27** | FastAPI 入门（2 个练习） | 🔵 现在 |
| W3 | 10/28–11/03 | 数据库（PostgreSQL + SQLAlchemy） | 压缩到 6 天 |
| W4 | 11/04–11/09 | Redis + 异步任务 | 压缩到 6 天 |
| W5 | 11/10–11/15 | 工程化收尾 | ❌ 砍掉练手项目 |
| **W6** | **11/16** | **项目 A 开始** | ✅ **守住，不动** |

---

## 进度看板

## 进度看板

## 进度看板

| 阶段 | 周期 | 主题 | 状态 |
|---|---|---|---|
| 一 · 地基 | 10/08–10/18 | Python 速通 + 异步编程 | ✅ **完成**（提前 4 天） |
| 二 · Web 核心 | 10/19–11/15 | FastAPI + PostgreSQL + Redis | 🔵 进行中 |
| 三 · 项目 A | 11/16–12/27 | LLM 统一网关 | ⬜ |
| 四 · 项目 B | 12/28–02/07 | RAG 知识库平台 | ⬜ |
| 五 · 冲刺 | 02/08–02/28 | 八股 + 简历 + 模拟面试 | ⬜ |

## 目录

| 目录 | 内容 | 说明 |
|---|---|---|
| [python/](python/) | Python 速通讲义 | 面向 C/C++ 背景编写 |
| [速查卡](python/cheatsheet.md) | 语法速查 | 卡住时 10 秒查到答案 |
| [leetcode/](leetcode/) | 算法题解 | 目标 200–300 题 |
| [interview/](interview/) | 面试八股 | 含 11 道 LLM 场景题 |
| [projects/](projects/) | 项目复盘 | 架构决策 + 量化数据 |

## 每日节奏

- 主线 2–3h：按阶段学技术、推进项目
- 副线 1–2h：刷算法题（考笔试手感，靠积累，突击无效）

---

*每天提交代码——贡献图本身就是简历的一部分。*
