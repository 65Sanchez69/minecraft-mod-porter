import json
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional


class IndustrialCraftRules:
    """Dedicated migration rules for IndustrialCraft-like Forge mods."""

    # Core replacements used in many IC2/IndustrialCraft mods
    IC2_RULES = [
        (b"net/minecraftforge/fml/common/registry/GameRegistry", b"net/minecraftforge/registries/ForgeRegistries"),
        (b"net/minecraft/item/ItemStack", b"net/minecraft/world/item/ItemStack"),
        (b"net/minecraft/entity/player/EntityPlayer", b"net/minecraft/world/entity/player/Player"),
        (b"net/minecraft/entity/player/EntityPlayerMP", b"net/minecraft/server/level/ServerPlayer"),
        (b"net/minecraft/world/World", b"net/minecraft/world/level/Level"),
        (b"net/minecraft/world/WorldServer", b"net/minecraft/server/level/ServerLevel"),
        (b"net/minecraft/util/math/BlockPos", b"net/minecraft/core/BlockPos"),
        (b"net/minecraft/tileentity/TileEntity", b"net/minecraft/world/level/block/entity/BlockEntity"),
        (b"net/minecraft/inventory/Container", b"net/minecraft/world/inventory/AbstractContainerMenu"),
        (b"net/minecraft/client/gui/GuiScreen", b"net/minecraft/client/gui/screens/Screen"),
        (b"net/minecraft/block/Block", b"net/minecraft/world/level/block/Block"),
        (b"net/minecraft/item/Item", b"net/minecraft/world/item/Item"),
        (b"net/minecraftforge/fml/common/eventhandler/Event", b"net/minecraftforge/eventbus/api/Event"),
        (b"net/minecraftforge/common/MinecraftForge", b"net/minecraftforge/common/MinecraftForge"),
        (b"IC2", b"IC2"),
    ]


class ForgeMetadataFixer:
    """Fixes mcmod.info, mods.toml and Forge metadata."""

    @staticmethod
    def find_mod_info_files(extract_path: Path) -> List[Path]:
        files: List[Path] = []
        for pattern in ["mcmod.info", "mods.toml", "META-INF/mods.toml", "META-INF/MANIFEST.MF"]:
            files.extend(extract_path.rglob(pattern))
        return files

    @staticmethod
    def fix_mod_metadata(extract_path: Path, target_version: str) -> List[str]:
        warnings: List[str] = []

        for meta_file in ForgeMetadataFixer.find_mod_info_files(extract_path):
            try:
                text = meta_file.read_text(encoding="utf-8", errors="ignore")
                new_text = text

                # Update mcmod.info JSON
                try:
                    obj = json.loads(text)
                    if isinstance(obj, list):
                        for item in obj:
                            if isinstance(item, dict):
                                item["mcversion"] = target_version
                        new_text = json.dumps(obj, indent=2)
                    elif isinstance(obj, dict):
                        obj["mcversion"] = target_version
                        new_text = json.dumps(obj, indent=2)
                except Exception:
                    pass

                # Update mods.toml
                new_text = re.sub(r'mcversion\s*=\s*"[^"]*"', f'mcversion = "{target_version}"', new_text)
                new_text = re.sub(r'forge_version\s*=\s*"[^"]*"', f'forge_version = "{target_version}"', new_text)

                if new_text != text:
                    meta_file.write_text(new_text, encoding="utf-8")
                    warnings.append(f"Updated metadata: {meta_file.relative_to(extract_path).as_posix()}")
            except Exception as exc:
                warnings.append(f"Could not update metadata {meta_file.name}: {str(exc)[:80]}")

        return warnings


class AppPortingEngine:
    """Full porting engine with targeted industrial craft handling."""

    @staticmethod
    def port_jar(jar_path: str, source_version: str, target_version: str, output_dir: str) -> Dict[str, Any]:
        jar_file = Path(jar_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not jar_file.exists():
            raise FileNotFoundError(f"JAR not found: {jar_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            extract_path = tmp_path / "extracted"
            extract_path.mkdir()

            try:
                with zipfile.ZipFile(jar_file, "r") as zf:
                    zf.extractall(extract_path)
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid JAR file: {jar_path}")

            # Step 1: metadata fixes
            metadata_warnings = ForgeMetadataFixer.fix_mod_metadata(extract_path, target_version)

            # Step 2: apply industrial craft relevant replacements
            rules = IndustrialCraftRules.IC2_RULES
            class_files = list(extract_path.rglob("*.class"))
            patched_classes = 0
            detection_log: List[str] = []

            for path in class_files:
                try:
                    content = path.read_bytes()
                    original = content
                    for old, new in rules:
                        content = content.replace(old, new)
                    if content != original:
                        path.write_bytes(content)
                        patched_classes += 1
                        detection_log.append(f"Patched class: {path.relative_to(extract_path).as_posix()}")
                except Exception as exc:
                    detection_log.append(f"Warning class: {path.name}: {str(exc)[:80]}")

            # Step 3: update resources
            resource_files = list(extract_path.rglob("*.json")) + list(extract_path.rglob("*.properties")) + list(extract_path.rglob("*.xml"))
            resource_updates = 0
            for res in resource_files:
                try:
                    text = res.read_text(encoding="utf-8", errors="ignore")
                    original = text
                    for old, new in rules:
                        try:
                            old_str = old.decode("utf-8")
                            new_str = new.decode("utf-8")
                            text = text.replace(old_str, new_str)
                        except Exception:
                            pass
                    if text != original:
                        res.write_text(text, encoding="utf-8")
                        resource_updates += 1
                except Exception:
                    pass

            # Step 4: write final JAR
            output_jar = output_path / f"ported_{jar_file.stem}_v{target_version}.jar"
            with zipfile.ZipFile(output_jar, "w", zipfile.ZIP_DEFLATED) as zf_out:
                for file in extract_path.rglob("*"):
                    if file.is_file():
                        zf_out.write(file, file.relative_to(extract_path))

            report = {
                "source_version": source_version,
                "target_version": target_version,
                "input_jar": jar_file.name,
                "output_jar": output_jar.name,
                "patched_classes": patched_classes,
                "resource_updates": resource_updates,
                "metadata_fixes": metadata_warnings,
                "detection_log": detection_log[:200],
                "status": "completed",
                "note": "This is a best-effort automated port; complex mods may still require manual fixes."
            }

            report_path = output_path / "porting_report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

            return {
                "jar_path": str(output_jar),
                "report_path": str(report_path),
                "report": report,
                "success": True,
            }
