"""
W2 练习 1：路由的三种参数

FastAPI 的参数有三个来源，先分清它们，后面写接口就顺了：

  ① 路径参数   /users/{user_id}        —— 标识「哪个资源」
  ② 查询参数   /items?skip=0&limit=10  —— 过滤、分页、排序
  ③ 请求体     POST 的 JSON body       —— 提交结构化数据

完成标准：运行后自测全部 ✅（用 TestClient，不用启动服务器）
"""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI(title="W2 练习1：路由")

# 假装这是数据库
USERS = {1: "小明", 2: "小红", 3: "小刚"}
ITEMS = [{"name": f"item-{i}", "price": float(i * 10)} for i in range(1, 21)]


# ================================================================
#  任务 1：路径参数
# ================================================================
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    """
    根据 user_id 查询用户；不存在则返回 404。
    """
    id_list = [1,2,3]
    if user_id not in id_list:
        raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
    return {"user_id": user_id, "name": USERS[user_id]}
    

# ================================================================
#  任务 2：查询参数
# ================================================================
@app.get("/items")
async def list_items(skip: int = 0, limit: int = 10, q: str | None = None):
    """
    分页列出商品，支持按关键词 q 过滤。

    返回 {"total": 过滤后的总条数, "items": 当前页数据}。
    （total 必须是【过滤后】的总数，否则前端算不出页数。）
    """
    data = [x for x in ITEMS if q in x["name"]] if q else ITEMS
    page = data[skip : skip + limit]
    return {"total": len(data), "items": page}


# ================================================================
#  任务 3：请求体
# ================================================================
class ItemIn(BaseModel):
    name: str
    price: float


@app.post("/items", status_code=201)
async def create_item(item: ItemIn):
    """
    新建商品。请求体由 ItemIn 模型自动校验，无需手写校验代码。
    """
    return {"created": item.model_dump()}


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
    print("  任务 1：路径参数")
    print("=" * 60)
    r = client.get("/users/1")
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("GET /users/1 → 200", r.status_code == 200, f"实际 {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            ck("包含 user_id 和 name", d.get("user_id") == 1 and d.get("name") == "小明", str(d))
        ck("GET /users/99 → 404", client.get("/users/99").status_code == 404)
        ck("GET /users/abc → 422（自动类型校验）", client.get("/users/abc").status_code == 422)

    print()
    print("=" * 60)
    print("  任务 2：查询参数")
    print("=" * 60)
    r = client.get("/items")
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("GET /items → 200", r.status_code == 200, f"实际 {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            ck("默认返回前 10 个", len(d.get("items", [])) == 10, f"实际 {len(d.get('items', []))}")
            ck("total = 20", d.get("total") == 20, f"实际 {d.get('total')}")
        d = client.get("/items?skip=5&limit=3").json()
        ck("skip/limit 生效", d.get("items") == ITEMS[5:8], str(d.get("items")))
        d = client.get("/items?q=item-2").json()
        ck("q 过滤生效", all("item-2" in x["name"] for x in d.get("items", [])) and d.get("total", 0) > 0)

    print()
    print("=" * 60)
    print("  任务 3：请求体")
    print("=" * 60)
    r = client.post("/items", json={"name": "book", "price": 30})
    if r.status_code == 500:
        print("  ⏳ 还没实现（返回 500）")
        SKIP += 1
    else:
        ck("POST 正常 → 201", r.status_code == 201, f"实际 {r.status_code}")
        if r.status_code == 201:
            ck("返回 created", "created" in r.json(), str(r.json()))
        ck("缺字段 → 422（自动）", client.post("/items", json={"name": "book"}).status_code == 422)
        ck("类型错 → 422（自动）",
           client.post("/items", json={"name": "book", "price": "abc"}).status_code == 422)

    print()
    print("=" * 60)
    print(f"  通过 {P}  失败 {F}")
    print("=" * 60)
    if SKIP:
        print(f"  ⏳ 还有 {SKIP} 个任务没实现（通过 {P}）")
    elif F == 0 and P > 0:
        print("  🎉 全部通过！")
