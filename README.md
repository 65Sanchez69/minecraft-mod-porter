# Minecraft Mod Porting Toolkit

**One-click mod porting:** Load JAR → Pick version → Get ported JAR

## ⚡ Quick Start

### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_app.py
```

### macOS/Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run_app.py
```

## 🎮 How to use

1. Click **📁 Select JAR**
2. Choose your mod file
3. Select **Target version**
4. Click **🚀 PORT MOD**
5. Wait 10-30 seconds
6. Get your ported mod in `output/` folder

## ✅ Supported migrations

```
1.12.2 (Forge) → 1.20.1 (Forge)
1.16.5 (Forge) → 1.20.1 (Forge)
1.20.1 (Forge) → 1.21.1 (Forge)
```

## 📦 What the porter does

✓ Extracts your JAR  
✓ Updates mod metadata (mcmod.info, mods.toml)  
✓ Applies Forge API replacements (classes, packages)  
✓ Updates resource files  
✓ Repackages as new JAR  
✓ Generates detailed report  

## 📂 Output files

In your output folder:
- `ported_[modname]_v[version].jar` — Your ported mod (ready to play)
- `porting_report.json` — Detailed porting log

## ⚠️ Important

- **Test the mod before playing** - Some complex mods may need manual fixes
- **Backup original JAR** - Keep the original file
- **Check the report** - Review what was changed
- **Complex mods** may require additional development work

## 🔧 Build as EXE (Windows)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name ModPorter run_app.py
```

EXE will be in `dist/ModPorter.exe`

## 📋 Troubleshooting

**"JAR not valid" error:**
- Make sure it's a real mod JAR
- Try re-downloading the mod

**"Mod needs Forge X.X.X" after porting:**
- The metadata wasn't fully updated
- Edit porting_report.json and check what went wrong

**Mod crashes in-game:**
- Some mods need code changes beyond bytecode replacement
- Check Minecraft logs for specific errors
- May need to decompile and manually adjust

## License

MIT
