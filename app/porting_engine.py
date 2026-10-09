import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from app.ai_client import AIClient


class PortingRules:
    """API replacement rules for different version migrations."""

    RULES = {
        ("1.7.10", "1.12.2"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "GameRegistry.registerItem": "ForgeRegistries.ITEMS.register",
            "GameRegistry.registerBlock": "ForgeRegistries.BLOCKS.register",
            "Minecraft.getMinecraft()": "Minecraft.getInstance()",
        },
        ("1.7.10", "1.16.5"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "GameRegistry.registerItem": "ForgeRegistries.ITEMS.register",
            "GameRegistry.registerBlock": "ForgeRegistries.BLOCKS.register",
            "Minecraft.getMinecraft()": "Minecraft.getInstance()",
            "EntityPlayer": "PlayerEntity",
            "Entity": "Entity",
        },
        ("1.7.10", "1.20.1"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "EntityPlayer": "Player",
            "EntityPlayerMP": "ServerPlayer",
            "WorldServer": "ServerLevel",
            "Minecraft.getMinecraft()": "Minecraft.getInstance()",
        },
        ("1.12.2", "1.16.5"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "EntityPlayer": "PlayerEntity",
            "EntityPlayerMP": "ServerPlayerEntity",
            "WorldServer": "ServerWorld",
        },
        ("1.12.2", "1.20.1"): {
            "EntityPlayer": "Player",
            "EntityPlayerMP": "ServerPlayer",
            "WorldServer": "ServerLevel",
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
        },
        ("1.16.5", "1.20.1"): {
            "net/minecraftforge/fml/common/registry/ForgeRegistries": "net/minecraftforge/registries/ForgeRegistries",
            "ServerPlayerEntity": "ServerPlayer",
            "PlayerEntity": "Player",
            "ServerWorld": "ServerLevel",
        },
        ("1.20.1", "1.21.1"): {
            "net/minecraft/world/level/block/entity/BlockEntity": "net/minecraft/world/level/block/entity/BlockEntity",
            "GuiScreen": "Screen",
        },
        ("1.21.1", "26.4"): {
            "@Mod.EventBusSubscriber": "@Mod.EventBusSubscriber",
            "GuiContainer": "AbstractContainerScreen",
        },
    }

    @classmethod
    def get_rules(cls, source: str, target: str) -> Dict[str, str]:
        return cls.RULES.get((source, target), {})


class JarPorter:
    """Port compiled JAR mods between Minecraft/Forge versions."""

    def __init__(self) -> None:
        self.ai_client: Optional[AIClient] = None
        self.porting_rules = PortingRules()

    def enable_ai(self, api_key: Optional[str] = None) -> None:
        self.ai_client = AIClient(api_key=api_key)

    def port_jar(
        self,
        jar_path: str,
        source_version: str,
        target_version: str,
        output_dir: str,
    ) -> Dict[str, object]:
        """Port a JAR file from source to target Forge version."""
        jar_file = Path(jar_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not jar_file.exists():
            raise FileNotFoundError(f"JAR not found: {jar_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            extract_path = tmp_path / "extracted"
            extract_path.mkdir()

            with zipfile.ZipFile(jar_file, "r") as zf:
                zf.extractall(extract_path)

            # Apply rules
            rules = self.porting_rules.get_rules(source_version, target_version)
            detections = []
            ai_results = []

            # Process class files
            class_files = list(extract_path.rglob("*.class"))
            patched_count = 0

            for class_file in class_files:
                try:
                    content = class_file.read_bytes()
                    original_content = content

                    # Apply string replacements in bytecode
                    for old, new in rules.items():
                        content = content.replace(old.encode(), new.encode())

                    if content != original_content:
                        class_file.write_bytes(content)
                        patched_count += 1
                        rel_path = class_file.relative_to(extract_path).as_posix()
                        detections.append(f"Patched: {rel_path}")
                except Exception as e:
                    detections.append(f"Warning: Could not patch {class_file.name}: {str(e)[:100]}")

            # Create output JAR
            output_jar = output_path / f"ported_mod_v{target_version}.jar"
            with zipfile.ZipFile(output_jar, "w", zipfile.ZIP_DEFLATED) as zf_out:
                for file in extract_path.rglob("*"):
                    if file.is_file():
                        zf_out.write(file, file.relative_to(extract_path))

            # Create report
            report = {
                "source_version": source_version,
                "target_version": target_version,
                "input_jar": str(jar_file),
                "output_jar": str(output_jar),
                "class_files_processed": len(class_files),
                "class_files_patched": patched_count,
                "detections": detections,
                "ai_results": ai_results,
                "status": "completed",
            }

            report_path = output_path / "porting_report.json"
            report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        return {
            "jar_path": str(output_jar),
            "report": report,
            "output_dir": str(output_path),
        }
