# 演示代码

用来「提前感受终点」的小 demo，不是练习。

| 文件 | 演示什么 | 对应知识点 |
|---|---|---|
| [fastapi_demo.py](fastapi_demo.py) | 一个能打字的 AI 聊天应用（前端网页 + 后端服务） | 类、类型提示、装饰器、异步 |

## 运行

```bash
cd ~/Documents/dev/learning-notes
.venv/bin/python python/demos/fastapi_demo.py
```

然后浏览器打开 http://127.0.0.1:8000/ ，按 Ctrl+C 停止。

## 它演示的完整链路

```
你打字 → 网页用 fetch() POST 到 /ask → 后端 Python 函数执行 → 返回 JSON → 网页显示
```

这就是所有 AI 聊天产品的工作原理。W12 要做的 RAG 系统，
就是在这个 demo 的 `ask()` 函数里加上「先检索文档，再让模型基于文档回答」。
