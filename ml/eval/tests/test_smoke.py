from chatbot_eval.golden_set import GoldenItem


def test_golden_item_shape():
    item = GoldenItem(item_id="g1", level=1, question="q", reference_answer="a")
    assert item.reference_chunk_ids == []
