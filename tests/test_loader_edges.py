from vanguard_primekg.load_primekg import directed_edge_rows, edge_id


def test_loader_materializes_both_directions_with_native_relation_fields() -> None:
    rows = directed_edge_rows("10", "20", "drug_protein", "carrier")
    assert rows == [
        {
            "edge_id": edge_id("10", "20", "drug_protein", "carrier"),
            "source_node_id": "pk_n_10",
            "target_node_id": "pk_n_20",
            "predicate": "drug_protein",
            "display_relation": "carrier",
        },
        {
            "edge_id": edge_id("20", "10", "drug_protein", "carrier"),
            "source_node_id": "pk_n_20",
            "target_node_id": "pk_n_10",
            "predicate": "drug_protein",
            "display_relation": "carrier",
        },
    ]


def test_loader_does_not_duplicate_self_loop() -> None:
    assert len(directed_edge_rows("10", "10", "protein_protein", "ppi")) == 1
