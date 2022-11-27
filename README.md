# AssemblyAI Transcribe blockifier

This project contains a Steamship Blockifier that transcribes and analyzes audio files via AssemblyAI.

## Configuration

This plugin must be configured with the following fields:

| Parameter | Description | DType | Required |
|-------------------|----------------------------------------------------|--------|--|
| speaker_detection | Enable speaker detection | bool | False |
| enable_audio_intelligence | Enable Audio Intelligence (note that this incurs a higher cost) | False |

## Getting Started

### Usage

To authenticate with Steamship, install the Steamship CLI with:

```bash
> npm install -g @steamship/cli
```

And then login with:

```bash
> ship login
```

```python
from steamship import Steamship, File, MimeTypes
from pathlib import Path

PLUGIN_HANDLE = "assemblyai-s2t-blockifier"
PLUGIN_CONFIG = {
    "speaker_detection": True,
    "enable_audio_intelligence": True
}

ship = Steamship()  # Without arguments, credentials in ~/.steamship.json will be used.
audio_path = Path("FILL_IN")
s2t_plugin_instance = ship.use_plugin(plugin_handle=PLUGIN_HANDLE)
file = File.create(ship, content=audio_path.open("b").read(), mime_type=MimeTypes.MP3)
tag_results = file.tag(plugin_instance=s2t_plugin_instance.handle)
tag_results.wait()

file = tag_results.output.file
for block in file.blocks:
    print(block.text)
```

## Developing

Development instructions are located in [DEVELOPING.md](DEVELOPING.md)

## Testing

Testing instructions are located in [TESTING.md](TESTING.md)

## Deploying

Deployment instructions are located in [DEPLOYING.md](DEPLOYING.md)
