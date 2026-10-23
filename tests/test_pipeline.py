import json

from redazione_ai.ingest.pipeline import read_articles


def test_read_articles_legge_un_articolo_per_riga(tmp_path):
    file = tmp_path / "articoli.jsonl"
    righe = [
        {"source_id": "1", "title": "Duomo"},
        {"source_id": "2", "title": "San Siro"},
    ]
    file.write_text("\n".join(json.dumps(r) for r in righe), encoding="utf-8")

    articoli = list(read_articles(file))

    assert len(articoli) == 2
    assert articoli[1]["title"] == "San Siro"


def test_read_articles_salta_le_righe_vuote(tmp_path):
    file = tmp_path / "articoli.jsonl"
    file.write_text('{"source_id": "1"}\n\n{"source_id": "2"}\n', encoding="utf-8")

    assert len(list(read_articles(file))) == 2
