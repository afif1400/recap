from datetime import datetime

from PIL import Image

from recap.ingestion.image import load_image_event


def test_loads_image_with_provided_date_and_category(tmp_path):
    p = tmp_path / "fundus.png"
    Image.new("RGB", (100, 100), "white").save(p)
    e = load_image_event(
        str(p),
        category="scan",
        title="Right fundus",
        date_iso="2023-04-01",
        source_id="fundus_2023.png",
    )
    assert e.category == "scan"
    assert e.date == datetime.fromisoformat("2023-04-01T00:00:00+00:00")
    assert e.source == "fundus_2023.png"
    assert "fundus" in e.title.lower()


def test_default_source_id_is_filename(tmp_path):
    p = tmp_path / "ct_chest.png"
    Image.new("RGB", (10, 10), "black").save(p)
    e = load_image_event(str(p), category="scan", title="CT chest", date_iso="2024-01-15")
    assert e.source == "ct_chest.png"


def test_image_path_preserved_in_metadata(tmp_path):
    p = tmp_path / "wound.jpg"
    Image.new("RGB", (10, 10), "red").save(p)
    e = load_image_event(str(p), category="photo", title="Wound day 7", date_iso="2024-06-20")
    assert e.metadata["path"] == str(p)
