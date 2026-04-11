import asyncio
import time
import uuid

import httpx

API_URL = "http://localhost:8000/api/chat"
WEBHOOK_URL = "http://localhost:8000/webhook/twilio"


async def test_api_chat(client, message, name):
    print(f"[{name}] Sending: {message[:30]}...")
    start = time.time()
    thread_id = f"e2e_test_{uuid.uuid4().hex[:8]}"
    try:
        response = await client.post(
            API_URL, json={"message": message, "thread_id": thread_id}, timeout=45.0
        )
        duration = time.time() - start

        if response.status_code == 200:
            data = response.json()
            reply_len = len(data.get("reply", ""))
            has_pdf = bool(data.get("pdf_url"))
            print(
                f"[{name}] SUCCESS ({duration:.2f}s) | Reply Length: {reply_len} | PDF Generated: {has_pdf}"
            )
            return True, duration
        else:
            print(f"[{name}] FAILED with STATUS {response.status_code} | {response.text}")
            return False, duration
    except Exception as e:
        print(f"[{name}] ERROR: {str(e)}")
        return False, 0.0


async def main():
    print("=== STARTING DEEP E2E REVIEW ===")

    async with httpx.AsyncClient() as client:
        # 1. Standard Case
        res, t1 = await test_api_chat(
            client, "I need a 45 min lesson on the water cycle for 5th graders.", "Standard"
        )

        # 2. Edge Case: Empty String
        res, t2 = await test_api_chat(client, "   ", "EmptyInput")

        # 3. Edge Case: Extremely short string
        res, t3 = await test_api_chat(client, "math", "ShortInput")

        # 4. Concurrency Test (simulate 3 concurrent teachers)
        print("\n--- Running Concurrency Test (3 parallel requests) ---")
        tasks = [
            test_api_chat(client, f"Lesson on gravity for grade {i}", f"Concurrent-{i}")
            for i in range(1, 4)
        ]
        results = await asyncio.gather(*tasks)

        print("\n=== E2E SUMMARY ===")
        print(f"Standard passing: {res}")
        print(f"Concurrency passing: {all(r[0] for r in results)}")


if __name__ == "__main__":
    asyncio.run(main())
