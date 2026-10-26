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
    要求：
      GET /users/1   → 200  {"user_id": 1, "name": "小明"}
      GET /users/99  → 404  {"detail": "用户 99 不存在"}

    TODO

    提示：
      · user_id 已经是 int 了（FastAPI 按注解自动转换），不用自己转
      · 不存在时： raise HTTPException(status_code=404, detail=f"用户 {user_id} 不存在")
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
    要求：
      GET /items                 → 前 10 个，total=20
      GET /items?skip=5&limit=3  → 第 6~8 个
      GET /items?q=item-2        → 只返回 name 里含 "item-2" 的

    返回：{"total": <过滤后的总数>, "items": <当前页>}

    TODO

    提示：
      data = [x for x in ITEMS if q in x["name"]] if q else ITEMS
      page = data[skip : skip + limit]
    """
    raise NotImplementedError("请实现 list_items")


# ================================================================
#  任务 3：请求体
# ================================================================
class ItemIn(BaseModel):
    name: str
    price: float


@app.post("/items", status_code=201)
async def create_item(item: ItemIn):
    """
    要求：
      POST {"name":"book","price":30}     → 201  {"created": {...}}
      POST {"name":"book"}                → 422（price 必填）
      POST {"name":"book","price":"abc"}  → 422（类型错）

    后两种是 FastAPI 自动做的，你一行校验都不用写。

    TODO

    提示：
      · item 已经是 ItemIn 实例，用 item.name / item.price
      · 返回 {"created": item.model_dump()}
    """
    raise NotImplementedError("请实现 create_item")


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
