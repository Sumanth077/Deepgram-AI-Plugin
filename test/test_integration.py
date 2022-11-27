"""Test assemblyai-s2t-blockifier via integration tests."""
import random
import string
from test import TEST_DATA
from test.utils import load_config, verify_file

import pytest
from steamship import File, PluginInstance, Steamship, Task, TaskState
from steamship.base.mime_types import MimeTypes

BLOCKIFIER_HANDLE = "s2t-blockifier-default"
ENVIRONMENT = "prod"


@pytest.fixture
def steamship() -> Steamship:
    """Instantiate a Steamship client."""
    return Steamship(profile=ENVIRONMENT)


def random_name() -> str:
    """Returns a random name suitable for a handle that has low likelihood of colliding with another.

    Output format matches test_[a-z0-9]+, which should be a valid handle.
    """
    letters = string.digits + string.ascii_letters
    return f"test_{''.join(random.choice(letters) for _ in range(10))}".lower()  # noqa: S311


@pytest.fixture
def plugin_instance(steamship: Steamship) -> PluginInstance:
    """Instantiate a plugin instance."""
    plugin_instance = steamship.use_plugin(
        plugin_handle=BLOCKIFIER_HANDLE,
        instance_handle=random_name(),
        config=load_config(),
        fetch_if_exists=False,
    )
    assert plugin_instance is not None
    assert plugin_instance.id is not None
    return plugin_instance


def test_blockifier(steamship: Steamship, plugin_instance: PluginInstance):
    """Test the AssemblyAI Blockifier via an integration test."""
    audio_path = TEST_DATA / "test_conversation.mp3"
    file = File.create(steamship, content=audio_path.open("rb").read(), mime_type=MimeTypes.MP3)

    blockify_task = file.blockify(plugin_instance=plugin_instance.handle)
    blockify_task.wait(max_timeout_s=3600, retry_delay_s=1)

    assert isinstance(blockify_task, Task)
    assert blockify_task.state == TaskState.succeeded
    file = blockify_task.output.file

    verify_file(file)
