import os
import pytest
from sse_starlette.sse import AppStatus

os.environ["LLM_ENABLED"] = "false"


@pytest.fixture(autouse=True)
def fresh_sse_loop():
    AppStatus.should_exit_event = None
    AppStatus.should_exit = False
