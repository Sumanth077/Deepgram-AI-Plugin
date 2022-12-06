"""DeepgramAI speech-to-text blockifier.

An audio file is loaded and converted into blocks, with tags added according to the plugin configuration.
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Type, Union
from uuid import uuid4

import requests
from deepgram import Deepgram
from steamship import Block, File, Steamship, SteamshipError
from steamship.base import Task, TaskState
from steamship.base.mime_types import MimeTypes
from steamship.data.workspace import SignedUrl, Workspace
from steamship.invocable import Config, InvocableResponse
from steamship.plugin.blockifier import Blockifier
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.outputs.block_and_tag_plugin_output import BlockAndTagPluginOutput
from steamship.plugin.request import PluginRequest
from steamship.utils.signed_urls import upload_to_signed_url

from parsers import (
    parse_topic_summaries,
)


class DeepgramAIBlockifierConfig(Config):
    """Config object containing required configuration parameters to initialize a DeepgramAIBlockifier."""

    deepgram_api_token: str


class TranscribeJobStatus(str, Enum):
    """Status of the transcription task."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class DeepgramAIBlockifier(Blockifier):
    """Blockifier that transcribes audio files into blocks.

    Attributes
    ----------
    config : DeepgramAIBlockifierConfig
        The required configuration used to instantiate a amazon-s2t-blockifier
    """

    config: DeepgramAIBlockifierConfig

    SUPPORTED_MIME_TYPES = (
        MimeTypes.MP3,
        MimeTypes.WAV,
        "video/mp4",
        "audio/mp4",
        "audio/webm",
        "video/webm",
    )

    BASE_URL = "https://api.deepgram.com/v1"
    BASE_HEADERS = {
        "content-type": "application/json",
    }

    def config_cls(self) -> Type[Config]:
        """Return the Configuration class."""
        return DeepgramAIBlockifierConfig

    def run(
            self, request: PluginRequest[RawDataPluginInput]
    ) -> Union[InvocableResponse, InvocableResponse[BlockAndTagPluginOutput]]:
        """Transcribe the audio file, store the transcription results in blocks and tags."""
        logging.info("DeepgramAI S2T Blockifier received run request.")
        if request.is_status_check:
            logging.info("Status check.")

            if "transcription_id" not in request.status.remote_status_input:
                raise SteamshipError(message="Status check requests need to provide a valid job id")
            return self._check_transcription_status(
                request.status.remote_status_input.get("transcription_id"))

        mime_type = self._check_mime_type(request)
        signed_url = self._upload_audio_file(mime_type, request.data.data)
        transcription_response = self._start_transcription(file_uri=signed_url)
        return self._process_transcription_response(transcription_response)

    def _start_transcription(self, file_uri: str) -> str:
        """Start to transcribe the audio file stored on s3 and return the JSON response."""
        response = Deepgram(self.config.deepgram_api_token).transcription.sync_prerecorded(
            source={
                "url": file_uri},
            options={"punctuate": True, "diarize": True, "detect_topics": True, "summarize": True, "model": "general"}

        )
        return response

    def _process_transcription_response(
            self, transcription_response: Dict[str, Any]
    ) -> InvocableResponse:
        # timestamp_tags, time_idx_to_char_idx = parse_timestamps(transcription_response)
        tags = [
            # *timestamp_tags,
            *parse_topic_summaries(transcription_response)
        ]
        return InvocableResponse(
            data=BlockAndTagPluginOutput(
                file=File.CreateRequest(
                    blocks=[
                        Block.CreateRequest(
                            text=transcription_response["results"]["channels"][0]["alternatives"][0]['transcript'],
                            tags=tags,
                        )
                    ]
                )
            )
        )

    def _check_transcription_status(self, transcription_id: str) -> InvocableResponse:
        response = requests.get(
            f"{self.BASE_URL}/listen/{transcription_id}",
            headers={"authorization": self.config.deepgram_api_token, **self.BASE_HEADERS},
        )

        transcription_response = response.json()
        job_status = transcription_response["status"]
        logging.info(f"Job {transcription_id} has status {job_status}.")

        if job_status in {
            TranscribeJobStatus.COMPLETED,
            TranscribeJobStatus.ERROR,
        }:
            if job_status == TranscribeJobStatus.COMPLETED:
                return self._process_transcription_response(transcription_response)
            else:
                raise SteamshipError(
                    message="Transcription was unsuccessful. "
                            "Please check Deepgram AI for error message."
                )
        else:
            return InvocableResponse(
                status=Task(
                    state=TaskState.running,
                    remote_status_message="Transcription job ongoing.",
                    remote_status_input={"transcription_id": transcription_id},
                )
            )

    def _upload_audio_file(self, mime_type: str, data: bytes) -> str:
        media_format = mime_type.split("/")[1]
        unique_file_id = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{uuid4()}.{media_format}"
        ship_client = (
            Steamship(profile="staging")
            if "docker" in str(self.client.config.api_base)
            else self.client
        )
        workspace = Workspace.get(client=ship_client)

        writing_signed_url = workspace.create_signed_url(
            SignedUrl.Request(
                bucket=SignedUrl.Bucket.PLUGIN_DATA,
                filepath=unique_file_id,
                operation=SignedUrl.Operation.WRITE,
            )
        ).signed_url
        upload_to_signed_url(writing_signed_url, data)

        return workspace.create_signed_url(
            SignedUrl.Request(
                bucket=SignedUrl.Bucket.PLUGIN_DATA,
                filepath=unique_file_id,
                operation=SignedUrl.Operation.READ,
            )
        ).signed_url

    def _check_mime_type(self, request: PluginRequest) -> str:
        mime_type = request.data.default_mime_type
        if mime_type not in self.SUPPORTED_MIME_TYPES:
            raise SteamshipError(
                "Unsupported mimeType. "
                f"The following mimeTypes are supported: {self.SUPPORTED_MIME_TYPES}"
            )
        return mime_type
