"""Test assemblyai-s2t-blockifier via unit tests."""
import pytest as pytest
from steamship import Steamship
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.request import PluginRequest

from src.api import DeepgramAIBlockifier
from test import TEST_DATA
from test.utils import verify_response


def _read_test_audio_file(filename: str) -> str:
    with (TEST_DATA / filename).open("rb") as f:
        return f.read()


@pytest.mark.parametrize("speaker_detection", (True, False))
def test_blockifier(speaker_detection: bool):
    """Test DeepgramAI (S2T) Blockifier without edge cases."""
    client = Steamship()
    blockifier = DeepgramAIBlockifier(client=client)
    request = PluginRequest(
        data=RawDataPluginInput(
            data=_read_test_audio_file("test_conversation.mp3"), default_mime_type="audio/mp3"
        )
    )
    response = blockifier.run(request)

    verify_response(response)
