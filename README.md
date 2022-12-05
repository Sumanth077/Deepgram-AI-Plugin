# DeepgramAI Transcribe blockifier

This project contains a Steamship Blockifier that transcribes and analyzes audio files via DeepgramAI.

## Configuration

This plugin is configured using an API key that is for running the Deepgram AI model. Those keys are supplied via secrets.


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

PLUGIN_HANDLE = "deepgram-s2t-blockifier"


ship = Steamship()  # Without arguments, credentials in ~/.steamship.json will be used.
audio_path = Path("FILL_IN")
s2t_plugin_instance = ship.use_plugin(plugin_handle=PLUGIN_HANDLE)
file = File.create(ship, content=audio_path.open("b").read(), mime_type=MimeTypes.MP3)
blockify_response = file.blockify(plugin_instance=s2t_plugin_instance.handle)
blockify_response.wait(max_timeout_s=3600, retry_delay_s=1)

file = file.refresh()

for block in file.blocks:
    print(block.text)
```

## Developing

Development instructions are located in [DEVELOPING.md](DEVELOPING.md)

## Testing

Testing instructions are located in [TESTING.md](TESTING.md)

## Deploying

Deployment instructions are located in [DEPLOYING.md](DEPLOYING.md)
