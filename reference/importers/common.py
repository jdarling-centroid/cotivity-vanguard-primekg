from __future__ import annotations

import hashlib
import os
from typing import TYPE_CHECKING

from ..ids import new_id
from ..repository import Repository

if TYPE_CHECKING:
    from ..adapters.base import Embedder


def file_sha256(path: str, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        while chunk := source.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_reference_source(
    repo: Repository,
    *,
    reference_source_id: str,
    name: str,
    source_kind: str,
    version: str,
    source_path: str,
) -> tuple[str, bool]:
    """Register a reference work and return ``(checksum, should_import)``.

    Oracle, rather than a filesystem marker, is authoritative. A ready source
    with the same checksum is skipped; changed or incomplete sources are cleared
    and rebuilt without ever creating an upload or publishing a PDF queue event.
    """
    checksum = file_sha256(source_path)
    current = repo.get_reference_source(reference_source_id)
    if current and current.state == "ready" and current.checksum_sha256 == checksum:
        return checksum, False
    if current and current.checksum_sha256 == checksum:
        # Deterministic node/fragment/edge identifiers make an interrupted load
        # resumable. Re-scan the source and let the bulk writers skip rows that
        # already committed; embedding indexing independently selects only
        # fragments that do not yet have an embedding.
        repo.update_reference_source(reference_source_id, "importing")
        return checksum, True
    if current:
        repo.clear_reference_source(reference_source_id)
    repo.register_reference_source(
        reference_source_id=reference_source_id,
        name=name,
        source_kind=source_kind,
        version=version,
        source_object_path=source_path,
        checksum_sha256=checksum,
        byte_size=os.path.getsize(source_path),
        metadata={"role": "reference_work"},
    )
    repo.update_reference_source(reference_source_id, "importing")
    return checksum, True


def index_reference_fragments(
    repo: Repository, reference_source_id: str, embedder: Embedder, batch_size: int = 32
) -> int:
    """Embed every unindexed fragment owned by one reference source."""
    sql = """
        SELECT f.fragment_id, f.node_id, f.fragment_text
        FROM fragments f JOIN nodes n ON n.node_id = f.node_id
        WHERE n.reference_source_id = :1
          AND NOT EXISTS (SELECT 1 FROM embeddings e WHERE e.fragment_id = f.fragment_id)
        ORDER BY f.created_at
    """
    indexed = 0
    with repo._conn.cursor() as cursor:  # noqa: SLF001 - importer/repository transaction
        cursor.execute(sql, [reference_source_id])
        while rows := cursor.fetchmany(batch_size):
            texts = []
            for _fragment_id, _node_id, value in rows:
                if hasattr(value, "read"):
                    value = value.read()
                texts.append(str(value or "")[:12000])
            results = embedder.embed_batch(texts)
            payload = [
                {
                    "embedding_id": new_id(), "node_id": node_id,
                    "fragment_id": fragment_id, "embedding_model": result.model,
                    # The canonical source text lives in fragments. Repeating
                    # it in every embedding roughly doubles corpus text storage.
                    "embedding_version": result.version, "source_text": None,
                    "embedding": result.vector,
                }
                for (fragment_id, node_id, _), text, result in zip(rows, texts, results, strict=True)
            ]
            errors = repo.bulk_create_embeddings(payload)
            if errors:
                sample = "; ".join(message for _, message in errors[:3])
                raise RuntimeError(
                    f"failed to store {len(errors)} embeddings for {reference_source_id}: {sample}"
                )
            indexed += len(payload)
            repo._conn.commit()  # noqa: SLF001
    return indexed


def sync_fragment_text_index(repo: Repository) -> None:
    """Make newly imported reference fragments immediately available to Oracle Text."""
    with repo._conn.cursor() as cursor:  # noqa: SLF001 - importer/repository transaction
        cursor.callproc("CTX_DDL.SYNC_INDEX", ["FRAGMENTS_TEXT_IX"])
