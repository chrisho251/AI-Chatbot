from chatbot_pipelines.definitions import defs
from chatbot_pipelines.steps import APP_IMAGE, WORKER_COMMANDS


def test_code_location_loads():
    assert defs is not None


def test_every_offline_worker_has_a_command_in_the_app_image():
    assert {f"w{n}" for n in range(1, 8)} <= {name[:2] for name in WORKER_COMMANDS}
    assert all(command.startswith("chatbot-w") for command in WORKER_COMMANDS.values())
    assert APP_IMAGE == "ai-chatbot/api"
