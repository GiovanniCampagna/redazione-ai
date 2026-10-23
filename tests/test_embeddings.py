import pytest

from redazione_ai.ingest.embeddings import content_hash, embed


def test_content_hash_e_deterministico():
    assert content_hash("Milano") == content_hash("Milano")


def test_content_hash_cambia_se_cambia_il_testo():
    assert content_hash("Milano") != content_hash("Milano.")


def test_content_hash_ha_64_caratteri():
    assert len(content_hash("qualsiasi testo")) == 64


@pytest.mark.integration
def test_embed_restituisce_un_vettore_da_768_per_testo():
    vectors = embed(["Il Duomo di Milano", "San Siro"])
    assert len(vectors) == 2
    assert all(len(v) == 768 for v in vectors)


@pytest.mark.integration
def test_embed_funziona_con_piu_lotti():
    testi = [f"Articolo numero {i}" for i in range(70)]
    vectors = embed(testi)
    assert len(vectors) == 70
