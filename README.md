# Suno API Client

A Python client for [Suno AI](https://suno.ai) music generation API. Generate AI music, lyrics, separate vocals, create videos and more - all from command line or a simple GUI.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- 🎵 **Generate Music** - Create songs from text descriptions
- 📝 **Generate Lyrics** - AI-powered lyrics creation
- 🔄 **Extend Tracks** - Continue existing songs
- 🎤 **Vocal Separation** - Split vocals and instruments (2 or 12 stems)
- 🎬 **Create Videos** - Generate music videos with visualizations
- 🔊 **WAV Conversion** - Export to high-quality WAV format
- 💾 **Auto-download** - Save generated files automatically

Works with models: V3.5, V4, V4.5, V4.5+, V5

## Installation

```bash
git clone https://github.com/zachariasz93/suno-api-client.git
cd suno-api-client
pip install -r requirements.txt
```

## Setup

1. Get your API key from [sunoapi.org/api-key](https://sunoapi.org/api-key)
2. Create `key.txt` in the project root and paste your key there

```bash
echo "your-api-key-here" > key.txt
```

## Usage

### Command Line

```bash
# Check your credits
python suno.py credits

# Generate music (simple)
python suno.py generate "upbeat jazz with piano and soft drums"

# Generate with options
python suno.py generate "love song about summer" --model V5 --download

# Custom mode (you provide lyrics)
python suno.py generate "[Verse] Walking down..." --custom --style "Indie Folk" --title "Summer Days"

# Instrumental only
python suno.py generate "epic orchestral soundtrack" --instrumental

# Generate lyrics
python suno.py lyrics "a song about coding at 3am"

# Interactive mode (guided step-by-step)
python suno.py interactive
```

### GUI

```bash
python run_gui.py
```

The GUI has four tabs:

- **Generate Music** - Full control over music generation
- **Generate Lyrics** - Create lyrics separately
- **Process Audio** - Vocal separation, video creation, WAV export
- **History** - Track your generations

### Python API

```python
from src.api import SunoAPI

api = SunoAPI("your-api-key")

# Check credits
print(f"Credits: {api.get_credits()}")

# Generate music
task_id = api.generate_music(
    prompt="chill lofi beat for studying",
    model="V4_5",
    instrumental=True
)

# Wait for result
result = api.wait_for_completion(task_id)

for track in result.tracks:
    print(f"{track.title}: {track.audio_url}")
    api.download_file(track.audio_url, f"downloads/{track.title}.mp3")
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `credits` | Check remaining credits |
| `generate PROMPT` | Generate music from prompt |
| `lyrics PROMPT` | Generate lyrics only |
| `extend AUDIO_ID` | Extend existing track |
| `separate TASK_ID AUDIO_ID` | Separate vocals/instruments |
| `video TASK_ID AUDIO_ID` | Create music video |
| `wav TASK_ID AUDIO_ID` | Convert to WAV |
| `status TASK_ID` | Check task status |
| `download URL` | Download file |
| `interactive` | Guided generation |

Run `python suno.py COMMAND --help` for options.

## Models

| Model | Max Duration | Best For |
|-------|--------------|----------|
| V3_5 | 4 min | Creative diversity |
| V4 | 4 min | Audio quality |
| V4_5 | 8 min | Genre blending |
| V4_5PLUS | 8 min | Rich sound |
| V5 | 8 min | Fast generation |

## Project Structure

```text
├── config/
│   └── settings.py      # Configuration
├── src/
│   ├── api/
│   │   ├── client.py    # API wrapper
│   │   ├── models.py    # Data classes
│   │   └── exceptions.py
│   ├── cli/
│   │   └── commands.py  # CLI commands
│   └── gui/
│       └── app.py       # GUI application
├── downloads/           # Generated files
├── suno.py              # CLI entry point
├── run_gui.py           # GUI entry point
└── requirements.txt
```

## Notes

- Generated files are stored on Suno servers for **15 days**
- Each generation creates **2 song variations**
- Stream URLs available in ~30-40 seconds, full download in 2-3 minutes
- Rate limit: 20 requests per 10 seconds

## Contributing

Feel free to open issues or submit PRs. Keep it simple.

## License

MIT License - do whatever you want with it.

## Disclaimer

This is an unofficial client. Not affiliated with Suno AI. Use responsibly and respect their terms of service.
