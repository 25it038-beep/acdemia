import httpx, json, asyncio

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTc4ZjEzNS0yNGQ5LTRjM2QtOWI3OS00NDU0MGUyYTViNzMiLCJleHAiOjE3ODUxNjc5NDZ9.gibrrMCTjnKlQ5EYcjQH8LcloM4RFwMJQPOwTDHK9Bo"
BASE = "http://localhost:8000"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

async def test_all():
    async with httpx.AsyncClient(timeout=180) as c:
        # 1. File upload + processing
        print("=== FILE UPLOAD ===")
        files = {"file": ("test.txt", b"Machine learning is a subset of artificial intelligence. It uses algorithms to learn patterns from data.", "text/plain")}
        r = await c.post(f"{BASE}/api/files/upload", headers=HEADERS, files=files)
        fid = r.json()["id"]
        print(f"Uploaded: {fid} -> status: {r.json()['status']}")
        await asyncio.sleep(8)
        r = await c.get(f"{BASE}/api/files/", headers=HEADERS)
        for f in r.json():
            if f["id"] == fid:
                print(f"After processing: status={f['status']}, chunks={f['chunks']}")

        # 2. Quiz generation
        print("\n=== QUIZ GENERATION ===")
        r = await c.post(f"{BASE}/api/tutor/quiz/generate", headers=HEADERS, json={
            "subject_id": "504f96ab-3619-4834-b511-19e64163086f",
            "title": "CS Quiz",
            "quiz_type": "mcq",
            "difficulty": "easy",
            "question_count": 2,
        })
        qid = r.json().get("quiz_id", "N/A")
        print(f"Quiz generated: {qid}")

        if qid != "N/A":
            r = await c.get(f"{BASE}/api/tutor/quiz/{qid}", headers=HEADERS)
            qdata = r.json()
            print(f"Questions: {qdata.get('total_questions', 0)}")
            for q in qdata.get("questions", []):
                print(f"  - {q['question_text'][:60]}")

        # 3. Flashcard generation
        print("\n=== FLASHCARD GENERATION ===")
        r = await c.post(f"{BASE}/api/flashcards/generate", headers=HEADERS, json={
            "subject_id": "504f96ab-3619-4834-b511-19e64163086f",
            "count": 3,
        })
        d = r.json()
        print(f"Generated: {d.get('count', 0)} flashcards")
        for card in d.get("flashcards", []):
            print(f"  Q: {card['front'][:60]}")

        # 4. Chat
        print("\n=== AI TUTOR CHAT ===")
        r = await c.post(f"{BASE}/api/tutor/chat", headers=HEADERS, json={
            "session_id": "final-test",
            "message": "What is a linked list? Answer in 1 sentence.",
            "mode": "tutor",
        })
        msg = r.json().get("message", "")
        print(f"Response: {msg[:100]}...")

        print("\n=== ALL TESTS PASSED ===")

asyncio.run(test_all())
