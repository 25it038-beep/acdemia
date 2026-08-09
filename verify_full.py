import httpx, json, asyncio

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTc4ZjEzNS0yNGQ5LTRjM2QtOWI3OS00NDU0MGUyYTViNzMiLCJleHAiOjE3ODUxNjc5NDZ9.gibrrMCTjnKlQ5EYcjQH8LcloM4RFwMJQPOwTDHK9Bo"
BASE = "http://localhost:8000"
H = {"Authorization": f"Bearer {TOKEN}"}

async def main():
    async with httpx.AsyncClient(timeout=180) as c:
        # Upload a proper text file
        content = """Data Structures and Algorithms
A data structure is a way of organizing data on a computer so that it can be used effectively.
Arrays are the simplest data structure where elements are stored in contiguous memory locations.
Linked lists consist of nodes where each node contains data and a pointer to the next node.
Stacks follow the Last-In-First-Out (LIFO) principle and are used in function call management.
Queues follow the First-In-First-Out (FIFO) principle and are used in scheduling algorithms.
Trees are hierarchical structures where each node has zero or more children.
Binary trees restrict each node to at most two children - left and right.
Binary Search Trees maintain the property that left child values are less than parent and right child values are greater.
Hash tables use a hash function to map keys to indices for fast O(1) lookup.
Graphs consist of vertices and edges and can represent networks and relationships.
Time complexity measures how an algorithm's runtime grows with input size using Big O notation.
Sorting algorithms like QuickSort, MergeSort, and BubbleSort arrange data in order.
Searching algorithms like Linear Search and Binary Search find elements in data structures.
Dynamic programming breaks problems into overlapping subproblems for efficient solving."""

        files = {"file": ("DSA_Notes.txt", content.encode(), "text/plain")}
        r = await c.post(f"{BASE}/api/files/upload", headers=H, files=files)
        fid = r.json()["id"]
        print(f"Uploaded file: {fid}")

        # Wait for processing
        for i in range(12):
            await asyncio.sleep(5)
            r = await c.get(f"{BASE}/api/files/", headers=H)
            for f in r.json():
                if f["id"] == fid:
                    print(f"  Status: {f['status']}, chunks: {f['chunks']}")
                    if f["status"] == "completed":
                        break
            else:
                continue
            break

        # Check subjects with hierarchy
        r = await c.get(f"{BASE}/api/subjects/", headers=H)
        print(f"\nSubjects: {len(r.json())}")
        for s in r.json():
            print(f"  {s['name']}")

            # Check workflow (needs units/chapters/topics)
            r2 = await c.get(f"{BASE}/api/workflow/{s['id']}", headers=H)
            wf = r2.json()
            print(f"    Workflow: {len(wf.get('nodes', []))} nodes, {len(wf.get('edges', []))} edges")
            for n in wf.get("nodes", [])[:5]:
                print(f"      [{n['type']}] {n['label']}")

            # Check knowledge graph
            r2 = await c.get(f"{BASE}/api/knowledge-graph?subject_id={s['id']}", headers=H)
            kg = r2.json()
            print(f"    Knowledge Graph: {len(kg.get('nodes', []))} nodes, {len(kg.get('edges', []))} edges")
            for n in kg.get("nodes", [])[:5]:
                print(f"      {n['name']}")

        # Generate flashcards from the new subject
        if r.json():
            latest_sid = r.json()[-1]["id"]
            r2 = await c.post(f"{BASE}/api/flashcards/generate", headers=H, json={
                "subject_id": latest_sid, "count": 5
            })
            fc = r2.json()
            print(f"\nFlashcards generated: {fc.get('count', 0)}")

        # Generate quiz
        if r.json():
            latest_sid = r.json()[-1]["id"]
            r2 = await c.post(f"{BASE}/api/tutor/quiz/generate", headers=H, json={
                "subject_id": latest_sid, "title": "Data Structures Quiz",
                "quiz_type": "mcq", "difficulty": "easy", "question_count": 3
            })
            q = r2.json()
            print(f"\nQuiz generated: {q.get('quiz_id', 'N/A')} ({q.get('total_questions', 0)} questions)")

        print("\n=== DONE ===")

asyncio.run(main())
