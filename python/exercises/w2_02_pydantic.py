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
    TODO: 给下面三个字段加上 Field 约束
      name  → 长度 1 ~ 20
      age   → 0 <= age <= 150
      email → 用 pattern 简单校验格式：r"^[\\w.+-]+@[\\w-]+\\.[\\w.]+$"

    写法示例：  name: str = Field(min_length=1, max_length=20)

    注意 tags 已经写好了，是给你示范 default_factory 的用法
    （Day 1 学过的可变默认值坑，这里是它的官方解法）
    """
    name: str
    age: int
    email: str
    tags: list[str] = Field(default_factory=list)


@app.post("/users", status_code=201)
async def create_user(user: UserIn):
    """TODO: 返回 user.model_dump()"""
    raise NotImplementedError("请实现 create_user")


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
    假装这是数据库里查出来的一整行（含敏感字段）。

    TODO: 直接 return db_row，让 response_model 帮你过滤

    要求：接口返回的 JSON 里【不能】出现 password 和 internal_note
    """
    db_row = {
        "id": uid,
        "name": "benfu",
        "password": "secret123",
        "internal_note": "内部备注，不应该给前端",
    }
    raise NotImplementedError("请返回 db_row")


# ================================================================
#  任务 3：嵌套模型
# ================================================================
class Address(BaseModel):
    city: str
    street: str


class UserWithAddress(BaseModel):
    """TODO: 定义 name: str 和 address: Address"""


@app.post("/users-with-address", status_code=201)
async def create_with_address(u: UserWithAddress):
    """TODO: 返回 u.model_dump()"""
    raise NotImplementedError("请实现 create_with_address")


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
