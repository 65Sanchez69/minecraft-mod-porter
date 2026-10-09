import json
import os
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from app.ai_client import AIClient


class PortingRules:
    """API replacement rules for Forge version migrations."""

    RULES = {
        ("1.7.10", "1.12.2"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "GameRegistry": "ForgeRegistries",
            "Minecraft/getMinecraft": "Minecraft/getInstance",
        },
        ("1.7.10", "1.16.5"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "EntityPlayer": "PlayerEntity",
            "EntityPlayerMP": "ServerPlayerEntity",
            "WorldServer": "ServerWorld",
        },
        ("1.7.10", "1.20.1"): {
            "net/minecraftforge/fml/common/registry/GameRegistry": "net/minecraftforge/registries/ForgeRegistries",
            "EntityPlayer": "Player",
            "EntityPlayerMP": "ServerPlayer",
            "WorldServer": "ServerLevel",
        },
        ("1.7.10", "1.21.1"): {
            "EntityPlayer": "Player",
            "EntityPlayerMP": "ServerPlayer",
            "WorldServer": "ServerLevel",
            "World": "Level",
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
        },
        ("1.12.2", "1.21.1"): {
            "EntityPlayer": "Player",
            "EntityPlayerMP": "ServerPlayer",
            "World": "Level",
            "WorldServer": "ServerLevel",
        },
        ("1.16.5", "1.20.1"): {
            "ServerPlayerEntity": "ServerPlayer",
            "PlayerEntity": "Player",
            "ServerWorld": "ServerLevel",
        },
        ("1.16.5", "1.21.1"): {
            "ServerPlayerEntity": "ServerPlayer",
            "PlayerEntity": "Player",
            "World": "Level",
            "ServerWorld": "ServerLevel",
        },
        ("1.20.1", "1.21.1"): {
            "GuiScreen": "Screen",
            "Container": "AbstractContainerMenu",
        },
        ("1.21.1", "26.4"): {
            "Screen": "Screen",
            "AbstractContainerMenu": "AbstractContainerMenu",
        },
    }

    @classmethod
    def get_rules(cls, source: str, target: str) -> Dict[str, str]:
        return cls.RULES.get((source, target), {})


class JarPorter:
    """Port compiled JAR mods between Minecraft/Forge versions."""

    def __init__(self) -> None:
        self.porting_rules = PortingRules()
        self.ai_client: Optional[AIClient] = None

    def port_jar(
        self,
        jar_path: str,
        source_version: str,
        target_version: str,
        output_dir: str,
        ai_enabled: bool = False,
    ) -> Dict[str, object]:
        """Port a JAR file from source to target Forge version."""
        jar_file = Path(jar_path)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not jar_file.exists():
            raise FileNotFoundError(f"JAR not found: {jar_path}")

        if not jar_file.suffix.lower() == ".jar":
            raise ValueError(f"File is not a JAR: {jar_path}")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            extract_path = tmp_path / "extracted"
            extract_path.mkdir()

            try:
                with zipfile.ZipFile(jar_file, "r") as zf:
                    zf.extractall(extract_path)
            except zipfile.BadZipFile:
                raise ValueError(f"Invalid JAR file: {jar_path}")

            rules = self.porting_rules.get_rules(source_version, target_version)
            detections: List[str] = []
            ai_results: List[Dict[str, str]] = []
            patched_count = 0

            class_files = list(extract_path.rglob("*.class"))

            for class_file in class_files:
                try:
                    content = class_file.read_bytes()
                    original_size = len(content)

                    for old, new in rules.items():
                        content = content.replace(old.encode("utf-8", errors="ignore"), new.encode("utf-8", errors="ignore"))

                    if len(content) != original_size or content != class_file.read_bytes():
                        class_file.write_bytes(content)
                        patched_count += 1
                        rel_path = class_file.relative_to(extract_path).as_posix()
                        detections.append(f"Patched: {rel_path}")
                except Exception as e:
                    detections.append(f"Warning: {class_file.name}: {str(e)[:80]}")

            resource_files = list(extract_path.rglob("*.properties")) + list(extract_path.rglob("*.json")) + list(
                extract_path.rglob("*.xml")
            )
            for res_file in resource_files:
                try:
                    content = res_file.read_text(encoding="utf-8", errors="ignore")
                    original = content

                    for old, new in rules.items():
                        content = content.replace(old, new)

                    if content != original:
                        res_file.write_text(content, encoding="utf-8")
                        rel_path = res_file.relative_to(extract_path).as_posix()
                        detections.append(f"Updated resource: {rel_path}")
                except Exception as e:
                    detections.append(f"Warning (resource): {res_file.name}: {str(e)[:80]}")

            output_jar = output_path / f"ported_{Path(jar_file.name).stem}_v{target_version}.jar"
            with zipfile.ZipFile(output_jar, "w", zipfile.ZIP_DEFLATED) as zf_out:
                for file in extract_path.rglob("*"):
                    if file.is_file():
                        zf_out.write(file, file.relative_to(extract_path))

            report = {
                "source_version": source_version,
                "target_version": target_version,
                "input_jar": jar_file.name,
                "output_jar": output_jar.name,
                "class_files_processed": len(class_files),
                "class_files_patched": patched_count,
                "resource_files_checked": len(resource_files),
                "detections": detections[:50],
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
