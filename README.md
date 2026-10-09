# Minecraft Mod Porting Toolkit

**Simple mod porting:** Load a `.jar` mod → select target version → get ported `.jar`

## Quick Start

```bash
# Setup
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run
python run_app.py
```

## How to use

1. Click "Select mod JAR"
2. Choose target Minecraft/Forge version
3. Click "Port mod"
4. Get ported JAR in output folder

## Supported ports

- 1.7.10 → 1.12.2, 1.16.5, 1.20.1, 1.21.1
- 1.12.2 → 1.16.5, 1.20.1, 1.21.1
- 1.16.5 → 1.20.1, 1.21.1
- 1.20.1 → 1.21.1
- 1.21.1 → 26.4

## Optional: AI fixes

Set environment variable for AI-assisted patches:

```bash
export GROQ_API_KEY="your_key"
```

## Output

In output folder you get:
- `ported_mod.jar` — ready to use
- `porting_report.json` — what was changed
- `decompiled/` — source code after porting

## Features

✅ Automatic bytecode analysis  
✅ Known API replacements  
✅ Optional AI patches  
✅ Report generation  
✅ One-click porting  

## License

MIT
