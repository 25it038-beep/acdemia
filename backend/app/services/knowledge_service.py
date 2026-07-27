import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    from neo4j import AsyncGraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False
    AsyncGraphDatabase = None
    logger.info("neo4j driver not installed. Using SQLite fallback for knowledge graph.")


class KnowledgeGraphService:
    """Knowledge graph with Neo4j primary, SQLite fallback."""

    def __init__(self):
        self.driver = None
        self._connect()

    def _connect(self):
        if HAS_NEO4J and settings.NEO4J_URI and settings.NEO4J_URI.strip():
            try:
                self.driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
            except Exception as e:
                logger.warning(f"Neo4j connection failed (non-critical): {e}")

    async def close(self):
        await self.driver.close()

    async def ensure_constraints(self):
        async with self.driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE",
                "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Subject) REQUIRE s.id IS UNIQUE",
            ]
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning(f"Constraint error: {e}")

    async def add_concept(
        self,
        concept_id: str,
        name: str,
        topic: str,
        difficulty: int = 1,
        importance: int = 5,
        properties: Optional[dict] = None,
    ):
        async with self.driver.session() as session:
            await session.run(
                """
                MERGE (c:Concept {id: $id})
                SET c.name = $name,
                    c.topic = $topic,
                    c.difficulty = $difficulty,
                    c.importance = $importance,
                    c.updated_at = timestamp()
                """,
                id=concept_id,
                name=name,
                topic=topic,
                difficulty=difficulty,
                importance=importance,
            )
            if properties:
                await session.run(
                    "MATCH (c:Concept {id: $id}) SET c += $props",
                    id=concept_id,
                    props=properties,
                )

    async def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str = "related_to",
        weight: float = 1.0,
    ):
        async with self.driver.session() as session:
            await session.run(
                f"""
                MATCH (a:Concept {{id: $source_id}})
                MATCH (b:Concept {{id: $target_id}})
                MERGE (a)-[r:{relation_type.upper()}]->(b)
                SET r.weight = $weight,
                    r.updated_at = timestamp()
                """,
                source_id=source_id,
                target_id=target_id,
                weight=weight,
            )

    async def get_concept_graph(self, user_id: str, subject_id: Optional[str] = None) -> Dict[str, Any]:
        # Try Neo4j first
        if self.driver:
            try:
                async with self.driver.session() as session:
                    query = """
                    MATCH (c:Concept)
                    OPTIONAL MATCH (c)-[r]->(related:Concept)
                    RETURN c, collect(DISTINCT {source: c.id, target: related.id, type: type(r), weight: r.weight}) as edges
                    """
                    if subject_id:
                        query = query.replace("MATCH (c:Concept)", f"MATCH (c:Concept {{subject_id: '{subject_id}'}})")

                    result = await session.run(query)
                    records = await result.fetch()

                    nodes = {}
                    edges = []
                    for record in records:
                        c = record["c"]
                        node_id = c.get("id", "")
                        if node_id and node_id not in nodes:
                            nodes[node_id] = {
                                "id": node_id,
                                "name": c.get("name", ""),
                                "topic": c.get("topic", ""),
                                "difficulty": c.get("difficulty", 1),
                                "importance": c.get("importance", 5),
                            }
                        for edge in record.get("edges", []):
                            if edge.get("source") and edge.get("target"):
                                edges.append({
                                    "source": edge["source"],
                                    "target": edge["target"],
                                    "type": edge.get("type", "related_to"),
                                    "weight": edge.get("weight", 1.0),
                                })

                    return {"nodes": list(nodes.values()), "edges": edges}
            except Exception as e:
                logger.warning(f"Neo4j query failed, falling back to SQLite: {e}")

        # SQLite fallback: read concepts from database
        from app.core.database import async_session_factory
        from app.models.models import Concept as ConceptModel, Topic, Chapter, Unit, Subject
        from sqlalchemy import select

        async with async_session_factory() as db:
            stmt = select(ConceptModel)
            if subject_id:
                stmt = stmt.join(Topic).join(Chapter).join(Unit).where(Unit.subject_id == subject_id)

            result = await db.execute(stmt)
            concepts = result.scalars().all()

            nodes = []
            edges = []
            for c in concepts:
                nodes.append({
                    "id": str(c.id),
                    "name": c.name,
                    "topic": c.topic.name if c.topic else "",
                    "difficulty": c.difficulty or 1,
                    "importance": c.importance or 5,
                })
                if c.parent_concept_id:
                    edges.append({
                        "source": str(c.parent_concept_id),
                        "target": str(c.id),
                        "type": "prerequisite",
                        "weight": 1.0,
                    })

            return {"nodes": nodes, "edges": edges}

    async def get_learning_path(self, user_id: str, target_concept: str) -> List[Dict]:
        if not self.driver:
            return []
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH path = shortestPath(
                    (start:Concept)-[:PREREQUISITE*]->(target:Concept {id: $target})
                )
                WHERE start.prerequisite IS NULL OR start.prerequisite = []
                RETURN [n in nodes(path) | {id: n.id, name: n.name, difficulty: n.difficulty}] as path,
                       [r in relationships(path) | type(r)] as relations
                """,
                target=target_concept,
            )
            record = await result.single()
            if record:
                return [
                    {"node": n, "relation": record["relations"][i] if i < len(record["relations"]) else None}
                    for i, n in enumerate(record["path"])
                ]
            return []


knowledge_graph = KnowledgeGraphService()