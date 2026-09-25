from chatbot_pipelines.definitions import defs
from chatbot_pipelines.steps import WORKER_IMAGES


def test_code_location_loads():
    assert defs is not None


def test_every_offline_worker_has_an_image():
    assert {f"w{n}" for n in range(1, 8)} <= {name[:2] for name in WORKER_IMAGES}
