from recap.ingestion.pdf import load_pdf


def test_extracts_pages_with_text_and_metadata():
    pages = load_pdf("tests/fixtures/tiny_lab.pdf")
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert "Creatinine" in pages[0].text
    assert "1.4 mg/dL" in pages[0].text


def test_pages_have_source_id():
    pages = load_pdf("tests/fixtures/tiny_lab.pdf", source_id="lab_2022-03-14.pdf")
    assert pages[0].source_id == "lab_2022-03-14.pdf"


def test_default_source_id_is_filename():
    pages = load_pdf("tests/fixtures/tiny_lab.pdf")
    assert pages[0].source_id == "tiny_lab.pdf"
