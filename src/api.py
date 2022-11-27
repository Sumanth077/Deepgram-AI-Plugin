"""AssemblyAI speech-to-text blockifier.

An audio file is loaded and converted into blocks, with tags added according to the plugin configuration.
"""
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Type, Union
from uuid import uuid4

import requests
from steamship import Block, File, Steamship, SteamshipError
from steamship.base import Task, TaskState
from steamship.base.mime_types import MimeTypes
from steamship.data.workspace import SignedUrl, Workspace
from steamship.invocable import Config, InvocableResponse, create_handler
from steamship.plugin.blockifier import Blockifier
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.outputs.block_and_tag_plugin_output import BlockAndTagPluginOutput
from steamship.plugin.request import PluginRequest
from steamship.utils.signed_urls import upload_to_signed_url

from parsers import (
    parse_chapters,
    parse_entities,
    parse_sentiments,
    parse_speaker_tags,
    parse_timestamps,
    parse_topic_summaries,
    parse_topics,
)


class AssemblyAIBlockifierConfig(Config):
    """Config object containing required configuration parameters to initialize a AssemblyAIBlockifier."""

    assembly_api_token: str
    speaker_detection: bool = True
    enable_audio_intelligence: bool = True


class TranscribeJobStatus(str, Enum):
    """Status of the transcription task."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class AssemblyAIBlockifier(Blockifier):
    """Blockifier that transcribes audio files into blocks.

    Attributes
    ----------
    config : AssemblyAIBlockifierConfig
        The required configuration used to instantiate a amazon-s2t-blockifier
    """

    config: AssemblyAIBlockifierConfig

    SUPPORTED_MIME_TYPES = (
        MimeTypes.MP3,
        MimeTypes.WAV,
        "video/mp4",
        "audio/mp4",
        "audio/webm",
        "video/webm",
    )

    BASE_URL = "https://api.assemblyai.com/v2"
    BASE_HEADERS = {
        "content-type": "application/json",
    }

    def config_cls(self) -> Type[Config]:
        """Return the Configuration class."""
        return AssemblyAIBlockifierConfig

    def run(
        self, request: PluginRequest[RawDataPluginInput]
    ) -> Union[InvocableResponse, InvocableResponse[BlockAndTagPluginOutput]]:
        """Transcribe the audio file, store the transcription results in blocks and tags."""
        logging.info("AssemblyAI S2T Blockifier received run request.")
        if request.is_status_check:
            logging.info("Status check.")

            if "transcription_id" not in request.status.remote_status_input:
                raise SteamshipError(message="Status check requests need to provide a valid job id")
            return self._check_transcription_status(
                request.status.remote_status_input["transcription_id"]
            )
        else:
            mime_type = self._check_mime_type(request)
            signed_url = self._upload_audio_file(mime_type, request.data.data)
            transcription_id = self._start_transcription(file_uri=signed_url)
            return self._check_transcription_status(transcription_id)

    def _start_transcription(self, file_uri: str) -> str:
        """Start to transcribe the audio file stored on s3 and return the transcription id."""
        response = requests.post(
            f"{self.BASE_URL}/transcript",
            json={
                "audio_url": file_uri,
                "speaker_labels": self.config.speaker_detection,
                "language_detection": True,
                "auto_highlights": self.config.enable_audio_intelligence,
                "iab_categories": self.config.enable_audio_intelligence,
                "sentiment_analysis": self.config.enable_audio_intelligence,
                "auto_chapters": self.config.enable_audio_intelligence,
                "entity_detection": self.config.enable_audio_intelligence,
            },
            headers={"authorization": self.config.assembly_api_token, **self.BASE_HEADERS},
        )
        return response.json().get("id")

    def _process_transcription_response(
        self, transcription_response: Dict[str, Any]
    ) -> InvocableResponse:
        timestamp_tags, time_idx_to_char_idx = parse_timestamps(transcription_response)

        tags = [
            *timestamp_tags,
            *parse_speaker_tags(transcription_response),
            *parse_topics(transcription_response),
            *parse_topic_summaries(transcription_response),
            *parse_sentiments(transcription_response),
            *parse_chapters(transcription_response, time_idx_to_char_idx),
            *parse_entities(transcription_response, time_idx_to_char_idx),
        ]

        return InvocableResponse(
            data=BlockAndTagPluginOutput(
                file=File.CreateRequest(
                    blocks=[
                        Block.CreateRequest(
                            text=transcription_response["text"],
                            tags=tags,
                        )
                    ]
                )
            )
        )

    def _check_transcription_status(self, transcription_id: str) -> InvocableResponse:
        response = requests.get(
            f"{self.BASE_URL}/transcript/{transcription_id}",
            headers={"authorization": self.config.assembly_api_token, **self.BASE_HEADERS},
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
                    "Please check Assembly AI for error message."
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


handler = create_handler(AssemblyAIBlockifier)
