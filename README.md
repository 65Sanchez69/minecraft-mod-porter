# Minecraft Mod Porting Toolkit

A Python desktop application for helping port Forge mods between Minecraft versions, with a GUI and optional AI-assisted fixes.

## Features

- Select source mod directory
- Choose source and target Forge/Minecraft versions
- Analyze Java mod sources
- Apply known API replacement rules for common porting changes
- Optional AI-assisted patch suggestions (Groq API if configured)
- Generate a ported output folder and a JAR-style artifact
- Save a porting report with findings

## Supported example flows

- 1.7.10 -> 1.20.1
- 1.12.2 -> 1.21.1
- 1.21.1 -> 26.4

## Project structure

```text
minecraft-mod-porter/
├── app/
│   ├── __init__.py
│   ├── ai_client.py
│   ├── main.py
│   ├── porting_engine.py
│   ├── ui.py
│   └── version_maps.py
├── .gitignore
├── README.md
├── requirements.txt
└── run_app.py
```

## Requirements

- Python 3.10+
- PySide6
- requests

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run_app.py
```

## Optional AI setup

To enable Groq AI patch suggestions, create an environment variable:

```bash
export GROQ_API_KEY="your_key_here"
```

On Windows PowerShell:

```powershell
$env:GROQ_API_KEY="your_key_here"
```

## How it works

1. User selects a mod project folder.
2. The app inspects Java files for common compatibility problems.
3. A version mapping table applies known Forge/Minecraft API replacements.
4. If AI is enabled, the app attempts to call the Groq API for deeper fixes.
5. The tool writes a patched output directory and a packaged artifact.

## Important note

This project is a practical MVP and automation starter for Forge porting. It is not a magic solution that can perfectly port every mod in one click. Real-worldMinecraft mod porting still requires manual review, especially for custom registries, rendering, networking, and world logic.

## Developer note

The code is intentionally structured so you can later add:

- Gradle project generation
- real bytecode scanning
- MC version-specific API mapping tables
- mod build automation
- richer AI prompts

## License

MIT
