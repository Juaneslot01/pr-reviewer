import asyncio

from dotenv import load_dotenv

from app.services.llm import review_diff


async def main() -> None:
    load_dotenv()
    fake_diff = """diff --git a/foo.py b/foo.py
index 1234567..89abcde 100644
--- a/foo.py
+++ b/foo.py
@@ -1,2 +1,2 @@
-print("hi")
+print("hello")
"""
    result = await review_diff(fake_diff)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
