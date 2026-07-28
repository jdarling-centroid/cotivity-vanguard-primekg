"""Source-scoped retrieval toolbox shared by REST and asynchronous workers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from vanguard.shared.errors import NotFound
from vanguard.shared.models import NodeType, SearchMode, SourceScope

from .tools import Recorder, Toolbox


def make_scoped_toolbox_factory(
    source_scope: SourceScope,
    upload_ids: list[str] | None = None,
    reference_source_ids: list[str] | None = None,
) -> Callable[[Recorder], Toolbox]:
    """Bind retrieval tools while enforcing the caller-selected ownership scope."""
    from vanguard.api.mcp_server import (
        get_fragment,
        get_node,
        hybrid_search,
        traverse_graph,
    )

    valid_node_types = {item.value for item in NodeType}
    valid_modes = {item.value for item in SearchMode}

    def factory(recorder: Recorder) -> Toolbox:
        def scoped_search(**arguments: Any) -> dict[str, Any]:
            node_types = arguments.get("node_types")
            if isinstance(node_types, list):
                arguments["node_types"] = [
                    value for value in node_types if value in valid_node_types
                ] or None
            modes = arguments.get("modes")
            if isinstance(modes, list):
                arguments["modes"] = [
                    value for value in modes if value in valid_modes
                ] or None
            arguments["source_scope"] = source_scope.value
            if upload_ids is not None:
                arguments["upload_ids"] = upload_ids
            if reference_source_ids is not None:
                arguments["reference_source_ids"] = reference_source_ids
            return hybrid_search(**arguments)

        def scoped_traverse(**arguments: Any) -> dict[str, Any]:
            node_types = arguments.get("node_types")
            if isinstance(node_types, list):
                arguments["node_types"] = [
                    value for value in node_types if value in valid_node_types
                ] or None
            return traverse_graph(**arguments)

        def scoped_fragment(fragment_id: str) -> dict[str, Any]:
            try:
                return get_fragment(fragment_id)
            except NotFound:
                node = get_node(fragment_id)
                return {
                    "node_id": node.get("node_id", fragment_id),
                    "text": node.get("text") or node.get("label") or "",
                    "provenance": node.get("provenance") or {},
                    "reference_source_id": node.get("reference_source_id"),
                }

        return Toolbox(
            recorder,
            hybrid_search=scoped_search,
            traverse_graph=scoped_traverse,
            get_fragment=scoped_fragment,
        )

    return factory
