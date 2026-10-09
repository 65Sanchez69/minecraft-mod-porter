# Minecraft Mod Porting Toolkit

**Simplest mod porting ever:** Load JAR → Pick version → Get ported JAR

## Installation

### Requirements
- Python 3.10 or higher
- pip

### Setup (Windows)

```bash
# Open Command Prompt and navigate to project folder
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_app.py
```

### Setup (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_app.py
```

## How to use

1. Click **"📁 Select JAR"** to load your mod
2. The app auto-detects the Minecraft version (or you select it manually)
3. Pick **Target version** from the dropdown
4. Click **"🚀 Port mod"**
5. Wait a few seconds
6. Get your ported mod in the output folder

## Supported ports

```
1.7.10  → 1.12.2, 1.16.5, 1.20.1, 1.21.1
1.12.2  → 1.16.5, 1.20.1, 1.21.1
1.16.5  → 1.20.1, 1.21.1
1.20.1  → 1.21.1
1.21.1  → 26.4
```

## What happens during porting

- Extracts your JAR
- Applies known API replacements (class names, method calls)
- Updates resource files (.json, .properties, .xml)
- Repackages as new JAR
- Generates detailed porting report

## Output files

In your output folder you'll find:
- `ported_[modname]_v[version].jar` — Your ported mod (ready to use)
- `porting_report.json` — Detailed list of what was changed

## Optional: AI assistance

Enable "AI suggestions" checkbox if you have Groq API:

```bash
# Set environment variable
export GROQ_API_KEY="your_key_here"
```

On Windows:
```powershell
$env:GROQ_API_KEY="your_key_here"
```

Then restart the app.

## Troubleshooting

**App won't start:**
```bash
pip install --upgrade PySide6 requests
```

**JAR not recognized:**
- Make sure it's a valid mod JAR (not corrupted)
- Try selecting source version manually

**Port failed:**
- Check porting_report.json for details
- Some complex mods may need manual fixes after porting

## Building as EXE (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "ModPorter" run_app.py
```

Your EXE will be in `dist/ModPorter.exe`

## License

MIT
