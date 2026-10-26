"""
W2 练习 2：Pydantic 校验与响应模型

任务：
  1. 用 Field 给字段加约束
  2. 用 response_model 过滤敏感字段（重要！）
  3. 用嵌套模型

完成标准：自测全部 ✅
"""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

app = FastAPI(title="W2 练习2：Pydantic")


# ================================================================
#  任务 1：字段约束
# ================================================================
class UserIn(BaseModel):
    """
创建用户的请求体模型，带字段约束。
    """
    name: str = Field(min_length=1, max_length=20)
    age: int = Field(ge=0, le=150)
    email: str = Field(pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    tags: list[str] = Field(default_factory=list)


@app.post("/users", status_code=201)
async def create_user(user: UserIn):
    """返回接收到的用户数据。"""
    return user.model_dump()


# ================================================================
#  任务 2：响应模型（防止数据泄露）
# ================================================================
class UserOut(BaseModel):
    """只暴露 id 和 name —— 注意【没有】password"""
    id: int
    name: str


@app.get("/users/{uid}", response_model=UserOut)
async def get_user(uid: int):
    """
查询用户信息。

response_model=UserOut 会自动过滤掉 db_row 里未声明的字段
（password、internal_note），这是防数据泄露的关键手段。
    """
    db_row = {
        "id": uid,
        "name": "benfu",
        "password": "secret123",
        "internal_note": "内部备注，不应该给前端",
    }
    return db_row


# ================================================================
#  任务 3：嵌套模型
# ================================================================
class Address(BaseModel):
    city: str
    street: str


class UserWithAddress(BaseModel):
    """带嵌套地址的用户模型。"""
    name: str
    address: Address

@app.post("/users-with-address", status_code=201)
async def create_with_address(u: UserWithAddress):
    """返回接收到的数据（含嵌套的 address）。"""
    return u.model_dump()


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
            P += 1; print(f"  ✅ {name}")
        else:
            F += 1; print(f"  ❌ {name}" + (f"   {detail}" if detail else ""))

    print("=" * 60)
    print("  任务 1：字段约束")
    print("=" * 60)
    ok = {"name": "benfu", "age": 20, "email": "a@b.com"}
    r = client.post("/users", json=ok)
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("正常数据 → 201", r.status_code == 201, f"实际 {r.status_code}")
        ck("name 为空 → 422", client.post("/users", json={**ok, "name": ""}).status_code == 422)
        ck("name 超长 → 422", client.post("/users", json={**ok, "name": "x" * 21}).status_code == 422)
        ck("age 为负 → 422", client.post("/users", json={**ok, "age": -1}).status_code == 422)
        ck("age 过大 → 422", client.post("/users", json={**ok, "age": 200}).status_code == 422)
        ck("email 格式错 → 422", client.post("/users", json={**ok, "email": "not-an-email"}).status_code == 422)
        ck("tags 默认空列表", client.post("/users", json=ok).json().get("tags") == [])

    print()
    print("=" * 60)
    print("  任务 2：响应模型过滤")
    print("=" * 60)
    r = client.get("/users/7")
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("GET /users/7 → 200", r.status_code == 200, f"实际 {r.status_code}")
        d = r.json()
        ck("包含 id 和 name", d.get("id") == 7 and d.get("name") == "benfu", str(d))
        ck("⭐ 不含 password", "password" not in d, str(d))
        ck("⭐ 不含 internal_note", "internal_note" not in d, str(d))

    print()
    print("=" * 60)
    print("  任务 3：嵌套模型")
    print("=" * 60)
    payload = {"name": "benfu", "address": {"city": "北京", "street": "长安街"}}
    r = client.post("/users-with-address", json=payload)
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("嵌套数据 → 201", r.status_code == 201, f"实际 {r.status_code}")
        ck("能拿到嵌套字段", r.json().get("address", {}).get("city") == "北京", str(r.json()))
        ck("嵌套缺字段 → 422",
           client.post("/users-with-address", json={"name": "x", "address": {}}).status_code == 422)

    print()
    print("=" * 60)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 60)
    if SKIP:
        print(f"  ⏳ 还有 {SKIP} 个任务没实现（通过 {P}）")
    elif F == 0 and P > 0:
        print("  🎉 全部通过！")
