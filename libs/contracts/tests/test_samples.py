import inspect

import pytest
from pydantic import ValidationError

from chatbot_contracts import corpus, escalation, external, query, tools
from chatbot_contracts.base import Model
from chatbot_contracts.samples import SAMPLES, sample_chunk, sample_region


def _contract_models() -> set[type[Model]]:
    modules = (corpus, escalation, external, query, tools)
    return {
        obj
        for module in modules
        for obj in vars(module).values()
        if inspect.isclass(obj) and issubclass(obj, Model) and obj.__module__ == module.__name__
    }


def test_every_record_type_has_a_sample():
    helper_models = {corpus.Extractor, corpus.PageFlags, tools.ToolCallRecord, query.Citation}
    missing = _contract_models() - set(SAMPLES) - helper_models
    assert not missing, f"add a sample factory for {sorted(m.__name__ for m in missing)}"


@pytest.mark.parametrize("model", sorted(SAMPLES, key=lambda m: m.__name__))
def test_sample_round_trips_through_json(model):
    record = SAMPLES[model]()
    assert model.model_validate_json(record.model_dump_json()) == record


def test_records_reject_unknown_fields():
    with pytest.raises(ValidationError):
        sample_region(colour="red")


def test_chunk_pages_must_be_in_order():
    with pytest.raises(ValidationError):
        sample_chunk(page_start=3, page_end=2)
