"""
W2 练习 3（综合）：APIRouter + Depends + 全局异常处理

这个练习把讲义里「只讲过没练过」的三样东西，拼成一个能跑的小服务。

  ① APIRouter       路由分组，统一注册
  ② Depends         认证逻辑抽出来，多个接口共用
  ③ 全局异常处理器   统一错误格式，任何地方抛 BizError 都返回同一个结构

场景：一个简易「用户中心」
  · 大部分接口需要 token 认证
  · 有余额不足这类业务异常
  · 有不需要认证的公开接口

完成标准：运行后自测全部 ✅
"""

from typing import Any

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

# ================================================================
#  基础设施（已给出，不用改）
# ================================================================
app = FastAPI(title="W2 练习 3：分层实践")

# 假装是数据库
USERS = {
    1: {"id": 1, "name": "小明", "balance": 100.0},
    2: {"id": 2, "name": "小红", "balance": 0.0},
}

# token → 用户名
TOKENS = {"token-admin": "admin", "token-user": "benfu"}


class Resp(BaseModel):
    """统一响应格式 —— 真实项目里所有接口都返回这个结构"""
    code: int = 0
    message: str = "ok"
    data: Any = None


class BizError(Exception):
    """业务异常 —— 由全局处理器统一转成 Resp 格式"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class WithdrawIn(BaseModel):
    """取款请求体"""
    amount: float


# ================================================================
#  任务 1：把认证逻辑做成「依赖」
# ================================================================
async def current_user(x_token: str = Header(...)) -> str:
    """
    从请求头 X-Token 读取并校验 token，返回用户名。

    各接口通过 Depends(current_user) 复用它；校验失败直接 401，
    接口函数根本不会被执行。
    """
    user = TOKENS.get(x_token)
    if user is None:
        raise HTTPException(status_code=401, detail="无效的 token")
    return user



# ================================================================
#  任务 2：用 APIRouter 组织路由
# ================================================================
#  为什么用 APIRouter 而不是直接 @app.get？
#    真实项目有几十个接口，全写在 main.py 里会乱成一团。
#    APIRouter 让你按模块分组（用户、订单、文档…），最后统一 include 到 app。
#    这里用一个文件模拟"两个模块"。
# ================================================================

users_router = APIRouter(prefix="/users", tags=["用户"])


@users_router.get("/me")
async def get_me(user: str = Depends(current_user)) -> Resp:
    """
    返回当前登录用户（user 由 Depends 自动注入）。
    """
    return Resp(data={"user": user})


@users_router.get("/{uid}")
async def get_user(uid: int, user: str = Depends(current_user)) -> Resp:
    """
    查询指定用户；不存在则抛 BizError(404)。
    """
    info = USERS.get(uid)
    if info is None:
        raise BizError(404, f"用户 {uid} 不存在")
    return Resp(data=info)


@users_router.post("/{uid}/withdraw")
async def withdraw(uid: int, body: WithdrawIn, user: str = Depends(current_user)) -> Resp:
    """
    取款。

    校验顺序不能乱：用户存在 → 金额合法 → 余额充足。
    """
    info = USERS.get(uid)
    if info is None:
        raise BizError(404, f"用户 {uid} 不存在")
    if body.amount <= 0:
        raise BizError(400, "金额必须大于 0")
    if info["balance"] < body.amount:
        raise BizError(1001, "余额不足")
    info["balance"] -= body.amount
    return Resp(data={"balance": info["balance"]})


public_router = APIRouter(prefix="/public", tags=["公开"])


@public_router.get("/health")
async def health() -> Resp:
    """
    健康检查，不需要认证。
    """
    return Resp(data={"status": "ok"})


# 统一注册到 app（这一步就是 APIRouter 的意义）
app.include_router(users_router)
app.include_router(public_router)


# ================================================================
#  任务 3：全局异常处理器
# ================================================================
@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError) -> JSONResponse:
    """
    把任何地方抛出的 BizError 统一转成
    {code, message, data} 格式，HTTP 状态码固定 400。
    """
    return JSONResponse(
        status_code=400,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


# ================================================================
#  自测
# ================================================================
if __name__ == "__main__":
    client = TestClient(app, raise_server_exceptions=False)
    P = F = 0
    SKIP = 0

    def ck(name, cond, detail=""):
        global P, F
        if cond:
            P += 1
            print(f"  ✅ {name}")
        else:
            F += 1
            print(f"  ❌ {name}" + (f"   {detail}" if detail else ""))

    AUTH = {"X-Token": "token-admin"}

    print("=" * 62)
    print("  任务 2-1：不需要认证的公开接口")
    print("=" * 62)
    r = client.get("/public/health")
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("GET /public/health → 200", r.status_code == 200, f"实际 {r.status_code}")
        ck("返回统一格式 code=0", r.json().get("code") == 0, str(r.json()))
        ck("data.status = ok", r.json().get("data", {}).get("status") == "ok", str(r.json()))

    print()
    print("=" * 62)
    print("  任务 1：认证依赖")
    print("=" * 62)
    r = client.get("/users/me")
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("不带 token → 422（Header 必填）", r.status_code == 422, f"实际 {r.status_code}")
        r = client.get("/users/me", headers={"X-Token": "bad"})
        ck("错误 token → 401", r.status_code == 401, f"实际 {r.status_code}")
        r = client.get("/users/me", headers=AUTH)
        ck("正确 token → 200", r.status_code == 200, f"实际 {r.status_code}")
        if r.status_code == 200:
            ck("能拿到当前用户", r.json().get("data", {}).get("user") == "admin", str(r.json()))

    print()
    print("=" * 62)
    print("  任务 2-2：查用户（正常 + 业务异常）")
    print("=" * 62)
    r = client.get("/users/1", headers=AUTH)
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("GET /users/1 → 200", r.status_code == 200, f"实际 {r.status_code}")
        ck("data.name = 小明", r.json().get("data", {}).get("name") == "小明", str(r.json()))
        r = client.get("/users/99", headers=AUTH)
        ck("查不存在的用户 → 400", r.status_code == 400, f"实际 {r.status_code}")
        if r.status_code == 400:
            ck("⭐ 统一格式里有 code=404", r.json().get("code") == 404, str(r.json()))
            ck("⭐ 统一格式里有 message", "用户 99" in r.json().get("message", ""), str(r.json()))

    print()
    print("=" * 62)
    print("  任务 2-3：取款（三种业务异常）")
    print("=" * 62)
    r = client.post("/users/1/withdraw", json={"amount": 30}, headers=AUTH)
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("正常取款 → 200", r.status_code == 200, f"实际 {r.status_code}")
        if r.status_code == 200:
            ck("余额从 100 扣到 70", r.json().get("data", {}).get("balance") == 70.0, str(r.json()))

        r = client.post("/users/1/withdraw", json={"amount": -5}, headers=AUTH)
        ck("负数金额 → 400", r.status_code == 400, f"实际 {r.status_code}")
        ck("code = 400", r.json().get("code") == 400, str(r.json()))

        r = client.post("/users/2/withdraw", json={"amount": 50}, headers=AUTH)
        ck("余额不足 → 400", r.status_code == 400, f"实际 {r.status_code}")
        ck("⭐ code = 1001（自定义业务码）", r.json().get("code") == 1001, str(r.json()))

        r = client.post("/users/99/withdraw", json={"amount": 10}, headers=AUTH)
        ck("用户不存在 → code=404", r.json().get("code") == 404, str(r.json()))

    print()
    print("=" * 62)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 62)
    if SKIP:
        print(f"  ⏳ 还有 {SKIP} 个任务没实现（通过 {P}）")
    elif F == 0 and P > 0:
        print("  🎉 全部通过！")

    print()
    print("=" * 62)
    print("  自查（做完后再看）")
    print("=" * 62)
    print("  1. 三个接口为什么要重复写 Depends(current_user)？")
    print("     → 因为它们都需要认证；写成依赖就不用每个函数里手写一遍校验")
    print()
    print("  2. BizError 和 HTTPException 有什么区别？")
    print("     → HTTPException 是 FastAPI 自带的，返回 {detail: ...}")
    print("       BizError 是你自定义的，能带业务码，还能统一格式")
    print()
    print("  3. APIRouter 的价值在哪？")
    print("     → 多个接口按模块分组；main.py 只需要 include_router")
