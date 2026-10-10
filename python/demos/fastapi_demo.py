"""
你的第一个 AI 应用 —— 看得见的那种

运行：
    cd ~/Documents/dev/learning-notes
    .venv/bin/python python/demos/fastapi_demo.py

然后用浏览器打开：  http://127.0.0.1:8000/

你会看到一个能打字的聊天界面。
它背后是：网页(前端) → HTTP 请求 → 这个 Python 服务(后端) → HTTP 响应 → 网页显示
"""

import asyncio

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="我的第一个 AI 应用", version="0.1")


# ===============================================================
#  后端部分：一个「回答问题」的接口
# ===============================================================
class AskRequest(BaseModel):
    """定义请求 JSON 的形状：前端必须传一个 question 字段"""
    question: str
    top_k: int = 3


@app.post("/ask")
async def ask(req: AskRequest) -> dict:
    """
    这就是后端接口。前端把问题发过来，这里返回答案。
    W12 你要做的 RAG 系统，就是在这个函数里加「检索文档」的环节。
    """
    await asyncio.sleep(0.6)  # 假装在调用大模型（真实项目里这里会调用 API）
    return {
        "answer": f"（我是假的大模型）你问的是「{req.question}」。"
                  f"真实项目里，这里会返回大模型的回答，而且是一个字一个字流式吐出来。",
        "top_k": req.top_k,
    }


# ===============================================================
#  前端部分：一个网页，它会调用上面的接口
# ===============================================================
CHAT_PAGE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>我的第一个 AI 应用</title>
<style>
  * { box-sizing: border-box; }
  body {
    font-family: -apple-system, "PingFang SC", sans-serif;
    max-width: 720px; margin: 0 auto; padding: 24px 16px;
    background: #f5f5f7; color: #1d1d1f;
  }
  h1 { font-size: 20px; margin: 0 0 4px; }
  .sub { color: #86868b; font-size: 13px; margin-bottom: 20px; }
  .hint {
    background: #fff; border-radius: 12px; padding: 14px 16px;
    font-size: 13px; color: #515154; line-height: 1.7;
    margin-bottom: 20px; border-left: 3px solid #0071e3;
  }
  .hint code { background: #f0f0f2; padding: 1px 5px; border-radius: 4px; }
  #msgs { margin-bottom: 16px; }
  .msg { padding: 12px 16px; border-radius: 14px; margin-bottom: 10px;
         line-height: 1.6; font-size: 15px; white-space: pre-wrap; }
  .me   { background: #0071e3; color: #fff; margin-left: 60px; }
  .bot  { background: #fff; margin-right: 60px; }
  .meta { font-size: 12px; color: #86868b; margin-top: 6px; }
  .row { display: flex; gap: 10px; position: sticky; bottom: 0;
         background: #f5f5f7; padding: 12px 0; }
  input {
    flex: 1; padding: 13px 16px; border-radius: 12px;
    border: 1px solid #d2d2d7; font-size: 15px; outline: none;
  }
  input:focus { border-color: #0071e3; }
  button {
    padding: 13px 22px; border-radius: 12px; border: none;
    background: #0071e3; color: #fff; font-size: 15px;
    cursor: pointer; font-weight: 500;
  }
  button:disabled { background: #b0b0b5; cursor: default; }
</style>
</head>
<body>
  <h1>我的第一个 AI 应用</h1>
  <div class="sub">前端网页 + 后端 Python 服务，跑在你自己电脑上</div>

  <div class="hint">
    <b>现在你能看懂整个链路了：</b><br>
    ① 你在这里打字 → ② 网页用 <code>fetch()</code> 把问题 POST 给
    <code>/ask</code> 接口 → ③ 后端 Python 函数被调用，返回 JSON →
    ④ 网页把 JSON 里的 answer 显示出来<br><br>
    这就是<strong>所有</strong> AI 聊天产品（ChatGPT、豆包、文心一言）的工作原理。
    你 W12 要做的 RAG 知识库，就是在第 ③ 步里加上「先检索文档再回答」。
  </div>

  <div id="msgs"></div>

  <div class="row">
    <input id="q" placeholder="随便问点什么，比如：什么是RAG？" autocomplete="off">
    <button id="btn" onclick="send()">发送</button>
  </div>

<script>
const msgs = document.getElementById('msgs');
const input = document.getElementById('q');
const btn = document.getElementById('btn');

function add(text, cls) {
  const d = document.createElement('div');
  d.className = 'msg ' + cls;
  d.textContent = text;
  msgs.appendChild(d);
  window.scrollTo(0, document.body.scrollHeight);
}

async function send() {
  const q = input.value.trim();
  if (!q) return;

  add(q, 'me');
  input.value = '';
  btn.disabled = true;
  btn.textContent = '思考中';

  try {
    // ★ 关键就这三行：把问题打包成 JSON，POST 给后端接口
    const resp = await fetch('/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: q, top_k: 3 })
    });

    if (!resp.ok) throw new Error('HTTP ' + resp.status);

    const data = await resp.json();   // ★ 拿到后端返回的 JSON
    add(data.answer, 'bot');
  } catch (e) {
    add('出错了：' + e.message, 'bot');
  } finally {
    btn.disabled = false;
    btn.textContent = '发送';
    input.focus();
  }
}

input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
input.focus();
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    """返回上面那个网页。用户访问 / 时看到的就是它。"""
    return CHAT_PAGE


if __name__ == "__main__":
    print("=" * 60)
    print("  打开浏览器访问：  http://127.0.0.1:8000/")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
