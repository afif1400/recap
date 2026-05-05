from recap.reasoner import EXTRACT_SYSTEM, SYNTHESIZE_SYSTEM, two_stage


def test_two_stage_pipes_extract_into_synthesize():
    captured: dict = {}

    def fake_extract(system, user):
        captured["extract_system"] = system
        captured["extract_user"] = user
        return "Cr 1.4 mg/dL on 2022-03-14 [src:lab.pdf]"

    def fake_synth(system, user):
        captured["synth_system"] = system
        captured["synth_user"] = user
        return "Creatinine first crossed normal in March 2022 [src:lab.pdf]."

    out = two_stage(
        "When did kidney function decline?",
        "Patient records block",
        extract_fn=fake_extract,
        synthesize_fn=fake_synth,
    )
    assert out == "Creatinine first crossed normal in March 2022 [src:lab.pdf]."

    # Extract sees the records + question
    assert "Patient records block" in captured["extract_user"]
    assert "When did kidney function decline?" in captured["extract_user"]
    assert captured["extract_system"] == EXTRACT_SYSTEM

    # Synthesize sees the extracted evidence
    assert "Cr 1.4 mg/dL on 2022-03-14 [src:lab.pdf]" in captured["synth_user"]
    assert "When did kidney function decline?" in captured["synth_user"]
    assert captured["synth_system"] == SYNTHESIZE_SYSTEM


def test_citations_survive_the_pipeline():
    """The whole point of two-stage is that MedGemma's [src:...] markers
    flow through Qwen's synthesis intact, so the gateway can parse them."""
    def fake_extract(s, u):
        return "Cr 1.4 [src:lab_2022.pdf#p1] eGFR 52 [src:lab_2022.pdf#p1]"

    def fake_synth(s, u):
        return "She crossed the CKD threshold [src:lab_2022.pdf#p1]."

    out = two_stage("when?", "block", extract_fn=fake_extract, synthesize_fn=fake_synth)
    assert "[src:lab_2022.pdf#p1]" in out


def test_evidence_string_is_passed_verbatim_to_synth():
    """If MedGemma returns text with leading/trailing whitespace,
    we strip it before feeding to Qwen so no double-empty-lines slip through."""
    seen = []

    def fake_extract(s, u):
        return "  evidence text  \n\n"

    def fake_synth(s, u):
        seen.append(u)
        return "answer"

    two_stage("q", "b", extract_fn=fake_extract, synthesize_fn=fake_synth)
    assert "  evidence text  " not in seen[0]
    assert "evidence text" in seen[0]
