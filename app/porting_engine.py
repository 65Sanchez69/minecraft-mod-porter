import json
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ModMetadataEditor:
    """Parse and edit mod metadata files (mcmod.info, mods.toml, etc)."""

    @staticmethod
    def find_metadata_file(extract_path: Path) -> Optional[Path]:
        """Find mcmod.info or mods.toml."""
        for name in ["mcmod.info", "mods.toml", "META-INF/MANIFEST.MF"]:
            file_path = extract_path / name
            if file_path.exists():
                return file_path
        return None

    @staticmethod
    def update_mcmod_info(content: str, target_version: str) -> str:
        """Update mcmod.info JSON metadata."""
        try:
            data = json.loads(content)
            if isinstance(data, list):
                for mod in data:
                    if "mcversion" in mod:
                        mod["mcversion"] = target_version
            elif isinstance(data, dict):
                if "mcversion" in data:
                    data["mcversion"] = target_version
            return json.dumps(data, indent=2)
        except Exception:
            return content

    @staticmethod
    def update_mods_toml(content: str, target_version: str) -> str:
        """Update mods.toml TOML metadata."""
        # Update [[mods]] section mcversion
        pattern = r'mcversion\s*=\s*["\'].*?["\']'
        content = re.sub(pattern, f'mcversion = "{target_version}"', content)

        # Update dependencies
        pattern = r'("forge":"[0-9]+-[0-9]+\.[0-9]+\.[0-9]+)'
        if target_version == "1.20.1":
            content = re.sub(pattern, r'"forge":"47-0.0.0', content)
        elif target_version == "1.21.1":
            content = re.sub(pattern, r'"forge":"51-0.0.0', content)
        elif target_version == "26.4":
            content = re.sub(pattern, r'"forge":"52-0.0.0', content)

        return content


class BytecodeReplacer:
    """Smart bytecode string replacement with proper encoding."""

    # Comprehensive rules for common migrations
    MIGRATION_RULES = {
        ("1.12.2", "1.20.1"): [
            # Package changes
            (b"net/minecraftforge/fml/common/registry/", b"net/minecraftforge/registries/"),
            (b"net/minecraft/entity/player/EntityPlayer", b"net/minecraft/world/entity/player/Player"),
            (b"net/minecraft/entity/player/EntityPlayerMP", b"net/minecraft/server/level/ServerPlayer"),
            (b"net/minecraft/world/WorldServer", b"net/minecraft/server/level/ServerLevel"),
            (b"net/minecraft/world/World", b"net/minecraft/world/level/Level"),
            (b"net/minecraft/client/gui/GuiScreen", b"net/minecraft/client/gui/screens/Screen"),
            (b"net/minecraft/inventory/Container", b"net/minecraft/world/inventory/AbstractContainerMenu"),
            (b"net/minecraft/tileentity/TileEntity", b"net/minecraft/world/level/block/entity/BlockEntity"),
            (b"net/minecraft/block/Block", b"net/minecraft/world/level/block/Block"),
            (b"net/minecraft/item/Item", b"net/minecraft/world/item/Item"),
            # Common class name replacements
            (b"EntityPlayer", b"Player"),
            (b"EntityPlayerMP", b"ServerPlayer"),
            (b"WorldServer", b"ServerLevel"),
            (b"TileEntity", b"BlockEntity"),
            (b"GuiScreen", b"Screen"),
            (b"Container", b"AbstractContainerMenu"),
            (b"ItemStack", b"ItemStack"),
        ],
        ("1.16.5", "1.20.1"): [
            (b"net/minecraft/entity/player/ServerPlayerEntity", b"net/minecraft/server/level/ServerPlayer"),
            (b"net/minecraft/entity/player/PlayerEntity", b"net/minecraft/world/entity/player/Player"),
            (b"net/minecraft/world/server/ServerWorld", b"net/minecraft/server/level/ServerLevel"),
            (b"net/minecraft/world/World", b"net/minecraft/world/level/Level"),
            (b"net/minecraft/client/gui/screen/Screen", b"net/minecraft/client/gui/screens/Screen"),
            (b"net/minecraft/inventory/container/Container", b"net/minecraft/world/inventory/AbstractContainerMenu"),
            (b"net/minecraft/tileentity/TileEntity", b"net/minecraft/world/level/block/entity/BlockEntity"),
            (b"ServerPlayerEntity", b"ServerPlayer"),
            (b"PlayerEntity", b"Player"),
            (b"ServerWorld", b"ServerLevel"),
            (b"TileEntity", b"BlockEntity"),
        ],
        ("1.20.1", "1.21.1"): [
            (b"net/minecraft/world/inventory/AbstractContainerMenu", b"net/minecraft/world/inventory/AbstractContainerMenu"),
            (b"net/minecraft/client/gui/screens/Screen", b"net/minecraft/client/gui/screens/Screen"),
            # Minimal changes between these versions
        ],
        ("1.21.1", "26.4"): [
            # Future compatibility layer
        ],
    }

    @staticmethod
    def apply_rules(jar_path: str, source_version: str, target_version: str, output_dir: str) -> Dict[str, object]:
        """Apply bytecode replacements to JAR."""
        jar_file = Path(jar_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not jar_file.exists():
            raise FileNotFoundError(f"JAR not found: {jar_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            extract_path = tmp_path / "extracted"
            extract_path.mkdir()

            # Extract JAR
            try:
                with zipfile.ZipFile(jar_file, "r") as zf:
                    zf.extractall(extract_path)
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid or corrupted JAR file: {jar_path}")

            # Update metadata
            metadata_file = ModMetadataEditor.find_metadata_file(extract_path)
            if metadata_file:
                try:
                    content = metadata_file.read_text(encoding="utf-8")
                    if metadata_file.name == "mcmod.info":
                        updated = ModMetadataEditor.update_mcmod_info(content, target_version)
                    elif metadata_file.name == "mods.toml":
                        updated = ModMetadataEditor.update_mods_toml(content, target_version)
                    else:
                        updated = content
                    metadata_file.write_text(updated, encoding="utf-8")
                except Exception as e:
                    print(f"Warning: Could not update metadata: {e}")

            # Get rules for this migration
            rules = BytecodeReplacer.MIGRATION_RULES.get((source_version, target_version), [])

            if not rules:
                raise ValueError(
                    f"No migration rules found for {source_version} -> {target_version}. "
                    "This version combination may not be supported yet."
                )

            detections: List[str] = []
            patched_count = 0

            # Process class files
            class_files = list(extract_path.rglob("*.class"))
            for class_file in class_files:
                try:
                    content = class_file.read_bytes()
                    original_content = content

                    for old_bytes, new_bytes in rules:
                        content = content.replace(old_bytes, new_bytes)

                    if content != original_content:
                        class_file.write_bytes(content)
                        patched_count += 1
                        rel_path = class_file.relative_to(extract_path).as_posix()
                        detections.append(f"✓ Patched: {rel_path}")
                except Exception as e:
                    rel_path = class_file.relative_to(extract_path).as_posix()
                    detections.append(f"⚠ Warning - {rel_path}: {str(e)[:60]}")

            # Process resource files
            resource_files = (
                list(extract_path.rglob("*.json"))
                + list(extract_path.rglob("*.properties"))
                + list(extract_path.rglob("*.xml"))
            )
            resources_updated = 0

            for res_file in resource_files:
                try:
                    content = res_file.read_text(encoding="utf-8", errors="ignore")
                    original = content

                    for old_bytes, new_bytes in rules:
                        try:
                            old_str = old_bytes.decode("utf-8", errors="ignore")
                            new_str = new_bytes.decode("utf-8", errors="ignore")
                            content = content.replace(old_str, new_str)
                        except Exception:
                            pass

                    if content != original:
                        res_file.write_text(content, encoding="utf-8")
                        resources_updated += 1
                except Exception as e:
                    detections.append(f"⚠ Resource warning - {res_file.name}: {str(e)[:60]}")

            # Repackage JAR
            output_jar = output_path / f"ported_{jar_file.stem}_v{target_version}.jar"
            with zipfile.ZipFile(output_jar, "w", zipfile.ZIP_DEFLATED) as zf_out:
                for file in extract_path.rglob("*"):
                    if file.is_file():
                        zf_out.write(file, file.relative_to(extract_path))

            # Generate report
            report = {
                "status": "success",
                "source_version": source_version,
                "target_version": target_version,
                "input_mod": jar_file.name,
                "output_mod": output_jar.name,
                "class_files_total": len(class_files),
                "class_files_patched": patched_count,
                "resource_files_updated": resources_updated,
                "detections": detections,
                "warnings": [
                    "This is an automated port. Please test thoroughly.",
                    "Some mods may require additional manual adjustments.",
                    "Check the log for any patching issues.",
                ],
            }

            report_file = output_path / "porting_report.json"
            report_file.write_text(json.dumps(report, indent=2), encoding="utf-8")

            return {
                "jar_path": str(output_jar),
                "report_path": str(report_file),
                "report": report,
                "success": True,
            }
