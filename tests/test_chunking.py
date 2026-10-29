from itertools import pairwise

from redazione_ai.ingest.chunking import split_into_chunks


def test_testo_vuoto_restituisce_lista_vuota():
    assert split_into_chunks("") == []
    assert split_into_chunks("   \n\n  ") == []


def test_testo_corto_resta_un_solo_chunk():
    testo = "Milano è il capoluogo della Lombardia."
    assert split_into_chunks(testo) == [testo]


def test_nessun_chunk_supera_max_chars():
    testo = ("Lorem ipsum dolor sit amet. " * 40 + "\n\n") * 5
    chunks = split_into_chunks(testo, max_chars=800, overlap=100)
    assert len(chunks) > 1
    assert all(len(c) <= 800 for c in chunks)


def test_preferisce_tagliare_tra_paragrafi():
    par_a = "A" * 500
    par_b = "B" * 500
    chunks = split_into_chunks(par_a + "\n\n" + par_b, max_chars=800, overlap=100)
    assert chunks[0] == par_a


def test_chunk_consecutivi_si_sovrappongono():
    testo = "".join(str(i % 10) for i in range(3000))
    chunks = split_into_chunks(testo, max_chars=800, overlap=100)
    for prima, dopo in pairwise(chunks):
        assert prima[-100:] == dopo[:100]


def test_non_spezza_le_parole():
    testo = "parola " * 300
    chunks = split_into_chunks(testo, max_chars=800, overlap=100)
    assert all(c.endswith("parola") for c in chunks)


def test_non_si_blocca_con_taglio_su_start_piu_overlap():
    testo = "A" * 100 + " " + "B" * 1000
    chunks = split_into_chunks(testo, max_chars=800, overlap=100)
    assert len(chunks) >= 2
