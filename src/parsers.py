"""Parsers to extract tags from transcription responses."""
from steamship import Tag


def parse_speaker_tags(transcription_response):
    """Extract speaker tags from transcription response."""
    tags = []
    if "utterances" in transcription_response:
        utterance_index = 0
        for utterance in transcription_response["utterances"] or []:
            utterance_length = len(utterance["text"])
            tags.append(
                Tag.CreateRequest(
                    kind="speaker",
                    start_idx=utterance_index,
                    end_idx=utterance_index + utterance_length,
                    name=utterance["speaker"],
                    value={"start_time": utterance["start"], "end_time": utterance["end"]},
                )
            )
            utterance_index += utterance_length + 1
    return tags


def parse_timestamps(transcription_response):
    """Extract timestamp tags from transcription response."""
    time_idx_to_char_idx = {}
    tags = []
    char_idx = 0
    for word in transcription_response["results"]["channels"][0]["alternatives"][0]['words']:
        word_length = len(word["word"])
        tags.append(
            Tag.CreateRequest(
                kind="timestamp",
                start_idx=char_idx,
                end_idx=char_idx + word_length,
                name=word["word"],
                value={"start_time": word["start"], "end_time": word["end"]},
            )
        )
        time_idx_to_char_idx[word["start"]] = char_idx
        time_idx_to_char_idx[word["end"]] = char_idx + word_length
        char_idx += word_length + 1
    return tags, time_idx_to_char_idx


def parse_entities(transcription_response, time_idx_to_char_idx):
    """Extract entity tags from transcription response."""
    tags = []
    if "entities" in transcription_response:
        for entity in transcription_response["entities"]:
            tags.append(
                Tag.CreateRequest(
                    kind="entity",
                    name=entity["text"],
                    value={
                        "type": entity["entity_type"],
                        "start_time": entity["start"],
                        "end_time": entity["end"],
                    },
                    start_idx=time_idx_to_char_idx[entity["start"]],
                    end_idx=time_idx_to_char_idx[entity["end"]],
                )
            )
    return tags


def parse_chapters(transcription_response, time_idx_to_char_idx):
    """Extract chapters and corresponding summaries from transcription response."""
    tags = []
    if "chapters" in transcription_response:
        for ix, chapter in enumerate(transcription_response["chapters"]):
            tags.append(
                Tag.CreateRequest(
                    kind="chapter",
                    name=f"{ix}",
                    value={
                        "summary": chapter["summary"],
                        "headline": chapter["headline"],
                        "gist": chapter["gist"],
                        "start_time": chapter["start"],
                        "end_time": chapter["end"],
                    },
                    start_idx=time_idx_to_char_idx[chapter["start"]],
                    end_idx=time_idx_to_char_idx[chapter["end"]],
                )
            )
    return tags


def parse_sentiments(transcription_response):
    """Extract sentiment tags from transcription response."""
    tags = []
    if "sentiment_analysis_results" in transcription_response:
        char_idx = 0
        for sentiment in transcription_response["sentiment_analysis_results"]:
            span_text = sentiment["text"]
            tags.append(
                Tag.CreateRequest(
                    kind="sentiment",
                    name=sentiment["sentiment"],
                    value={
                        "confidence": sentiment["confidence"],
                        "start_time": sentiment["start"],
                        "end_time": sentiment["end"],
                    },
                    start_idx=char_idx,
                    end_idx=char_idx + len(span_text),
                )
            )
            char_idx += len(span_text) + 1
    return tags


def parse_topic_summaries(transcription_response):
    """Extract summary from transcription response."""
    tags = []
    summary = transcription_response["results"]["channels"][0]["alternatives"][0]['summaries'][0]['summary']
    tags.append(
                Tag.CreateRequest(
                    kind="topic_summary",
                    name=summary,
                    value={
                        "start_time": None,
                        "end_time": None,
                    },
                    end_idx=None,
                    start_idx=None,
                )
            )
    return tags


def parse_topics(transcription_response):
    """Extract topic tags from transcription response."""
    tags = []
    if "results" in transcription_response.get("iab_categories_result", {}):
        char_idx = 0
        for topic_fragment in transcription_response["iab_categories_result"]["results"]:
            topic_length = len(topic_fragment["text"])
            start_time = topic_fragment["timestamp"]["start"]
            end_time = topic_fragment["timestamp"]["end"]
            for label in topic_fragment["labels"]:
                tags.append(
                    Tag.CreateRequest(
                        kind="topic",
                        name=label["label"],
                        value={
                            "confidence": label["relevance"],
                            "start_time": start_time,
                            "end_time": end_time,
                        },
                        start_idx=char_idx,
                        end_idx=char_idx + topic_length,
                    )
                )
            char_idx += topic_length + 1
    return tags
