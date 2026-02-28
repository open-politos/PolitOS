"""Knowledge Base: YAML files are the source of truth, ChromaDB is a derived search index.

Files in knowledge-base/ are the canonical store. ChromaDB is rebuilt from those
files on each call to index_knowledge_base() and is used only for semantic search.
File-based functions (load_all_entries, get_entry_by_id, list_entries) read directly
from disk with no ChromaDB dependency.
"""

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


def load_all_entries(root: Path | None = None) -> list[KBEntry]:
    """Load all KB entries from YAML/MD files on disk. No ChromaDB dependency."""
    root = root or PROJECT_ROOT
    kb_dir = root / "knowledge-base"

    entries: list[KBEntry] = []
    if not kb_dir.exists():
        return entries

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

    return entries


def get_entry_by_id(entry_id: str, root: Path | None = None) -> KBEntry | None:
    """Find a single KB entry by its ID, reading directly from files."""
    for entry in load_all_entries(root):
        if entry.id == entry_id:
            return entry
    return None


def list_entries(root: Path | None = None) -> list[KBEntry]:
    """List all KB entries from files. Alias for load_all_entries."""
    return load_all_entries(root)


def index_knowledge_base(root: Path | None = None) -> int:
    """Rebuild the ChromaDB search index from knowledge-base/ files.

    Performs a clean rebuild: deletes the existing collection and recreates it
    from the current files on disk. This ensures deleted files don't leave
    stale entries in the index.
    """
    global _collection
    root = root or PROJECT_ROOT
    entries = load_all_entries(root)

    # Clean rebuild: delete and recreate the collection
    collection = _get_collection(root)
    _client.delete_collection(COLLECTION_NAME)  # type: ignore[union-attr]
    _collection = _client.get_or_create_collection(  # type: ignore[union-attr]
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    if not entries:
        return 0

    _collection.add(
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
    """Search the knowledge base by semantic similarity.

    If the ChromaDB index is empty but files exist on disk, triggers a rebuild
    automatically so the index is transparent to callers.
    """
    root = root or PROJECT_ROOT
    collection = _get_collection(root)
    if collection.count() == 0:
        # Auto-rebuild if files exist but index is empty
        if load_all_entries(root):
            index_knowledge_base(root)
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
