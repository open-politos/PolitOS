"""Knowledge Base backed by ChromaDB. Indexes knowledge-base/ YAML/MD files."""

from dataclasses import dataclass
from pathlib import Path

import chromadb
import yaml

from src.core.config import PROJECT_ROOT

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None

COLLECTION_NAME = "politos_kb"


@dataclass
class KBEntry:
    id: str
    domain: str
    title: str
    content: str
    approved_by: str | None = None
    approved_date: str | None = None
    version: int = 1
    metadata: dict | None = None


def _get_collection(root: Path | None = None) -> chromadb.Collection:
    global _client, _collection
    if _collection is not None:
        return _collection

    root = root or PROJECT_ROOT
    persist_dir = str(root / "data" / "chromadb")
    _client = chromadb.PersistentClient(path=persist_dir)
    _collection = _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def _parse_yaml_entry(path: Path) -> KBEntry | None:
    """Parse a YAML knowledge base entry."""
    try:
        data = yaml.safe_load(path.read_text())
    except (yaml.YAMLError, UnicodeDecodeError):
        return None

    if not isinstance(data, dict) or "id" not in data:
        return None

    return KBEntry(
        id=data["id"],
        domain=data.get("domain", "general"),
        title=data.get("title", path.stem),
        content=data.get("content", ""),
        approved_by=data.get("approved_by"),
        approved_date=str(data["approved_date"]) if data.get("approved_date") else None,
        version=data.get("version", 1),
    )


def _parse_markdown_entry(path: Path) -> KBEntry | None:
    """Parse a Markdown knowledge base file. Uses filename as ID."""
    try:
        content = path.read_text()
    except UnicodeDecodeError:
        return None

    # Extract title from first heading if present
    title = path.stem
    for line in content.split("\n"):
        if line.startswith("# "):
            title = line[2:].strip()
            break

    domain = path.parent.name if path.parent.name != "knowledge-base" else "general"

    return KBEntry(
        id=f"kb-{domain}-{path.stem}",
        domain=domain,
        title=title,
        content=content,
    )


def index_knowledge_base(root: Path | None = None) -> int:
    """Scan knowledge-base/ and index all entries into ChromaDB. Returns count."""
    root = root or PROJECT_ROOT
    kb_dir = root / "knowledge-base"
    collection = _get_collection(root)

    entries: list[KBEntry] = []
    if kb_dir.exists():
        for path in kb_dir.rglob("*"):
            if path.is_dir() or path.name.startswith(".") or path.name == "README.md":
                continue
            entry = None
            if path.suffix in (".yaml", ".yml"):
                entry = _parse_yaml_entry(path)
            elif path.suffix == ".md":
                entry = _parse_markdown_entry(path)
            if entry and entry.content:
                entries.append(entry)

    if not entries:
        return 0

    # Upsert all entries
    collection.upsert(
        ids=[e.id for e in entries],
        documents=[e.content for e in entries],
        metadatas=[
            {
                "domain": e.domain,
                "title": e.title,
                "approved_by": e.approved_by or "",
                "approved_date": e.approved_date or "",
                "version": e.version,
            }
            for e in entries
        ],
    )

    return len(entries)


def search(query: str, n_results: int = 5, root: Path | None = None) -> list[KBEntry]:
    """Search the knowledge base by semantic similarity."""
    collection = _get_collection(root)
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[query], n_results=min(n_results, collection.count()))

    entries = []
    if results and results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            entries.append(
                KBEntry(
                    id=doc_id,
                    domain=meta.get("domain", "general"),
                    title=meta.get("title", ""),
                    content=results["documents"][0][i] if results["documents"] else "",
                    approved_by=meta.get("approved_by") or None,
                    approved_date=meta.get("approved_date") or None,
                    version=meta.get("version", 1),
                )
            )

    return entries


def get_position(topic: str, root: Path | None = None) -> KBEntry | None:
    """Get the most relevant KB entry for a topic. Returns None if no good match."""
    results = search(topic, n_results=1, root=root)
    return results[0] if results else None


def list_topics(root: Path | None = None) -> list[str]:
    """List all topic titles in the knowledge base."""
    collection = _get_collection(root)
    if collection.count() == 0:
        return []

    all_entries = collection.get(include=["metadatas"])
    return [m.get("title", "") for m in (all_entries.get("metadatas") or []) if m]


def reset(root: Path | None = None) -> None:
    """Reset the collection (useful for re-indexing)."""
    global _collection
    collection = _get_collection(root)
    root = root or PROJECT_ROOT
    _client = chromadb.PersistentClient(path=str(root / "data" / "chromadb"))
    _client.delete_collection(COLLECTION_NAME)
    _collection = None
