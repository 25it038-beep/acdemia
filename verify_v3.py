import httpx, json, asyncio

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0OTc4ZjEzNS0yNGQ5LTRjM2QtOWI3OS00NDU0MGUyYTViNzMiLCJleHAiOjE3ODUxNzE1OTB9.VT7-tQKTO7M3uzB2CBcOatmqdY5nDrR4VmpwnwR2e8A"
BASE = "http://localhost:8000"
H = {"Authorization": f"Bearer {TOKEN}"}

async def main():
    async with httpx.AsyncClient(timeout=180) as c:
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
Searching algorithms like Linear Search and Binary Search find elements in data structures."""

        # Upload
        r = await c.post(f"{BASE}/api/files/upload", headers=H, files={"file": ("DSA.txt", content.encode(), "text/plain")})
        d = r.json()
        fid = d.get("id")
        if not fid:
            print(f"Upload failed: {d}")
            return
        print(f"Uploaded: {fid[:8]}...")

        # Wait for completion
        for i in range(15):
            await asyncio.sleep(4)
            r = await c.get(f"{BASE}/api/files/", headers=H)
            for f in r.json():
                if f["id"] == fid:
                    s = f"{f['status']} ({f['chunks']} chunks)"
                    break
            else:
                s = "not in list"
            print(f"  [{i+1}] {s}")
            if "completed" in s:
                break

        # Subjects
        r = await c.get(f"{BASE}/api/subjects/", headers=H)
        subs = r.json()
        print(f"\nSubjects: {len(subs)}")
        for s in subs:
            print(f"  '{s['name']}' - {s['unit_count']} units, {s['file_count']} files")

            # Workflow
            r2 = await c.get(f"{BASE}/api/workflow/{s['id']}", headers=H)
            wf = r2.json()
            print(f"    Workflow: {len(wf.get('nodes',[]))} nodes")
            for n in wf.get("nodes",[])[:6]:
                print(f"      [{n['type']}] {n['label']}")

            # Knowledge graph
            r2 = await c.get(f"{BASE}/api/knowledge-graph?subject_id={s['id']}", headers=H)
            kg = r2.json()
            print(f"    Knowledge Graph: {len(kg.get('nodes',[]))} concepts")
            for n in kg.get("nodes",[])[:6]:
                print(f"      {n['name']}")

            # Flashcards
            r2 = await c.post(f"{BASE}/api/flashcards/generate", headers=H, json={"subject_id": s["id"], "count": 3})
            fc = r2.json()
            print(f"    Flashcards: {fc.get('count',0)} generated")

            # Quiz
            r2 = await c.post(f"{BASE}/api/tutor/quiz/generate", headers=H, json={"subject_id": s["id"], "title": f"{s['name']} Quiz", "quiz_type": "mcq", "difficulty": "easy", "question_count": 2})
            q = r2.json()
            print(f"    Quiz: {q.get('quiz_id','')[:8]}... ({q.get('total_questions',0)} questions)")

        print("\n=== DONE ===")

asyncio.run(main())
