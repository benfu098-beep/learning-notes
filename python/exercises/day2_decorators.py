"""
第 2 天练习 ③⑥：装饰器

考点：
  - 闭包：内层函数记住外层变量
  - 装饰器 = 接收函数、返回新函数
  - functools.wraps 的作用
  - 带参数的装饰器（三层嵌套）

两个任务：
  ③ @count_calls        统计函数被调用次数
  ⑥ @retry(times=N)     失败自动重试

完成标准：运行后两个自测都 ✅
"""

import functools
import time


# ================================================================
#  ③ @count_calls —— 统计调用次数
# ================================================================
def count_calls(func):
    """
    让被装饰的函数多出一个 .calls 属性，记录它被调用了多少次。

    用法：
        @count_calls
        def hello():
            return "hi"

        hello(); hello()
        print(hello.calls)     # 2

    TODO: 实现它（把 raise 删掉）

    提示（三步）：
      1. @functools.wraps(func)          ← 保留原函数的名字和文档
         def wrapper(*args, **kwargs):
             wrapper.calls += 1          ← 计数
             return func(*args, **kwargs)  ← 调用原函数并返回结果
      2. wrapper.calls = 0               ← 初始化计数器
      3. return wrapper                  ← 返回新函数

    ⚠️ wrapper.calls = 0 必须在 return wrapper 之前写，
       因为 return 之后就再也拿不到 wrapper 这个变量了。
    """
    raise NotImplementedError("请实现 count_calls")


# ================================================================
#  ⑥ @retry(times=N) —— 失败自动重试（带参数的装饰器）
# ================================================================
def retry(times: int = 3, delay: float = 0.05):
    """
    被装饰的函数如果抛异常，就等 delay 秒后重试，最多重试 times 次。
    最后一次仍失败，就把异常抛出去。

    用法：
        @retry(times=3, delay=0.05)
        def flaky():
            ...

    TODO: 实现它（把 raise 删掉）

    提示：带参数的装饰器需要【三层嵌套】

        def retry(times, delay):          ← 第 1 层：接收装饰器的参数
            def decorator(func):          ← 第 2 层：接收被装饰的函数
                @functools.wraps(func)
                def wrapper(*args, **kwargs):   ← 第 3 层：真正被调用时执行
                    for attempt in range(times):
                        try:
                            return func(*args, **kwargs)
                        except Exception:
                            if attempt == times - 1:
                                raise        # 最后一次还失败，抛出去
                            time.sleep(delay)
                return wrapper
            return decorator              ← 注意返回的是 decorator，不是 wrapper

    ⚠️ 最常见的错误：最外层 return 了 wrapper 而不是 decorator。
    """
    raise NotImplementedError("请实现 retry")


# ================================================================
#  自测
# ================================================================
if __name__ == "__main__":
    print("=" * 54)
    print("  ③⑥ 装饰器自测")
    print("=" * 54)

    # ---------- ③ ----------
    print("\n【③】@count_calls")
    try:
        @count_calls
        def hello():
            return "hi"

        print(f"   刚定义时 hello.calls = {hello.calls}")   # 期望 0
        hello(); hello(); hello()
        print(f"   调用 3 次后 = {hello.calls}")             # 期望 3
        print(f"   函数名还在吗: {hello.__name__}")          # 期望 hello（functools.wraps 的功劳）

        ok = (hello.calls == 3 and hello.__name__ == "hello")
        print(f"   {'✅ 通过' if ok else '❌ 不对'}")
    except NotImplementedError as e:
        print(f"   ⏳ {e}")

    # ---------- ⑥ ----------
    print("\n【⑥】@retry(times=3)")
    try:
        counter = {"n": 0}

        @retry(times=3, delay=0.05)
        def flaky():
            counter["n"] += 1
            if counter["n"] < 3:
                raise ValueError(f"第 {counter['n']} 次故意失败")
            return "第三次成功了"

        result = flaky()
        print(f"   返回值: {result}")
        print(f"   实际尝试次数: {counter['n']}")
        ok1 = (result == "第三次成功了" and counter["n"] == 3)
        print(f"   {'✅ 通过' if ok1 else '❌ 不对'}")
    except NotImplementedError as e:
        print(f"   ⏳ {e}")
        ok1 = False

    # ---------- ⑥ 边界：一直失败要抛异常 ----------
    print("\n【⑥-2】一直失败时，应该把异常抛出来（而不是静默返回 None）")
    try:
        @retry(times=2, delay=0.01)
        def always_fail():
            raise RuntimeError("永远失败")

        always_fail()
        print("   ❌ 不对：没有抛异常，说明异常被吞掉了")
    except NotImplementedError:
        print("   ⏳ 还没实现")
    except RuntimeError as e:
        print(f"   ✅ 通过：正确抛出了 {type(e).__name__}: {e}")
    except Exception as e:
        print(f"   ❌ 抛出的异常类型不对：{type(e).__name__}: {e}")

    print()
    print("   💡 思考：如果 wrapper 里写成 print(e) 而不是 raise，")
    print("      调用方就永远发现不了错误——这叫「吞异常」，是生产事故的常见来源。")
