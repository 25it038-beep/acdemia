import httpx, json, asyncio

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTc4ZjEzNS0yNGQ5LTRjM2QtOWI3OS00NDU0MGUyYTViNzMiLCJleHAiOjE3ODUxNjc5NDZ9.gibrrMCTjnKlQ5EYcjQH8LcloM4RFwMJQPOwTDHK9Bo"
BASE = "http://localhost:8000"
H = {"Authorization": f"Bearer {TOKEN}"}

async def test():
    async with httpx.AsyncClient(timeout=60) as c:
        # Files status
        r = await c.get(f"{BASE}/api/files/", headers=H)
        print("=== FILES ===")
        for f in r.json():
            print(f"  {f['original_filename']}: {f['status']} ({f['chunks']} chunks)")

        # Subjects
        r = await c.get(f"{BASE}/api/subjects/", headers=H)
        print("\n=== SUBJECTS ===")
        for s in r.json():
            print(f"  {s['name']} (id: {s['id'][:8]}...) files: {s['file_count']}")

        # Knowledge graph (requires subject_id)
        if r.json():
            sid = r.json()[0]["id"]
            r2 = await c.get(f"{BASE}/api/knowledge-graph?subject_id={sid}", headers=H)
            print(f"\n=== KNOWLEDGE GRAPH ===")
            print(f"  Status: {r2.status_code}, response: {json.dumps(r2.json())[:200]}")

        # Workflow
        if r.json():
            sid = r.json()[0]["id"]
            r2 = await c.get(f"{BASE}/api/workflow/{sid}", headers=H)
            print(f"\n=== WORKFLOW ===")
            print(f"  Status: {r2.status_code}, response: {json.dumps(r2.json())[:200]}")

        # Study plans
        r2 = await c.get(f"{BASE}/api/study-plans", headers=H)
        print(f"\n=== STUDY PLANS ===")
        print(f"  Status: {r2.status_code}, response: {json.dumps(r2.json())[:200]}")

        # Health
        r2 = await c.get(f"{BASE}/api/health", headers=H)
        print(f"\n=== HEALTH ===")
        print(f"  {json.dumps(r2.json())}")

        # Quiz history
        r2 = await c.get(f"{BASE}/api/tutor/quiz/", headers=H)
        print(f"\n=== QUIZZES ===")
        print(f"  Status: {r2.status_code}, response: {json.dumps(r2.json())[:200]}")

        print("\n=== DONE ===")

asyncio.run(test())
