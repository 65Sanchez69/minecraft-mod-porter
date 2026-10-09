import json
import os
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple

from app.ai_client import AIClient


class VersionMapping:
    """Simple version-translation table for known Forge compatibility edits."""

    def __init__(self) -> None:
        self.rules = {
            ("1.7.10", "1.20.1"): {
                "net.minecraftforge.fml.common.registry.GameRegistry": "net.minecraftforge.registries.ForgeRegistries",
                "GameRegistry.register": "Registry.register",
                "Minecraft.getMinecraft()": "Minecraft.getInstance()",
                "IRecipe": "RecipeHolder",
                "EntityPlayer": "Player",
            },
            ("1.12.2", "1.21.1"): {
                "net.minecraftforge.fml.common.registry.GameRegistry": "net.minecraftforge.registries.ForgeRegistries",
                "GameRegistry.register": "Registry.register",
                "Minecraft.getMinecraft()": "Minecraft.getInstance()",
                "EntityPlayerMP": "ServerPlayer",
                "WorldServer": "ServerLevel",
                "BlockPos": "BlockPos",
            },
            ("1.21.1", "26.4"): {
                "net.minecraftforge.fml.common.registry.GameRegistry": "net.minecraftforge.registries.ForgeRegistries",
                "@Mod.EventBusSubscriber": "@Mod.EventBusSubscriber(bus = Mod.EventBusSubscriber.Bus.MOD)",
                "KeyBinding": "KeyMapping",
                "GuiContainer": "AbstractContainerScreen",
            },
        }

    def get_rules(self, source_version: str, target_version: str) -> Dict[str, str]:
        return self.rules.get((source_version, target_version), {})


def apply_known_replacements(content: str, rules: Dict[str, str]) -> str:
    updated = content
    for old, new in rules.items():
        updated = updated.replace(old, new)
    return updated


def find_java_files(root_dir: str) -> List[Path]:
    base = Path(root_dir)
    if not base.exists():
        return []
    return sorted(base.rglob("*.java"))


def create_gradle_files(output_dir: Path, target_version: str) -> None:
    settings = """\
pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
        maven { url = uri(\"https://maven.minecraftforge.net/\") }
    }
}

rootProject.name = \"ported_mod\"
"""

    build_gradle = f"""\
plugins {{
    id 'java'
    id 'net.minecraftforge.gradle' version '6.0.+' 
}}

version = '1.0.0'
group = 'com.example.portedmod'

java {{
    toolchain {{
        languageVersion = JavaLanguageVersion.of(17)
    }}
}}

minecraft {{
    mappings channel = 'official', version = '{target_version}'
}}

repositories {{
    mavenCentral()
    maven { url = uri('https://maven.minecraftforge.net/') }
}}

dependencies {{
    minecraft 'net.minecraftforge:forge:{target_version}-forge'
}}

tasks.withType(JavaCompile).configureEach {{
    options.encoding = 'UTF-8'
}}
"""

    (output_dir / "settings.gradle").write_text(settings, encoding="utf-8")
    (output_dir / "build.gradle").write_text(build_gradle, encoding="utf-8")


class PortingEngine:
    """A practical MVP engine for source code porting and output packaging."""

    def __init__(self) -> None:
        self.mapping = VersionMapping()

    def port_mod(self, source_dir: str, source_version: str, target_version: str, output_dir: str, ai_enabled: bool = False, ai_key: str = None) -> Dict[str, object]:
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if not source_path.exists():
            raise FileNotFoundError(f"Source directory not found: {source_dir}")

        java_files = find_java_files(source_dir)
        if not java_files:
            raise FileNotFoundError("No .java files were found in the selected source directory.")

        result_files: List[Dict[str, str]] = []
        detections: List[str] = []
        ai_results: List[Dict[str, str]] = []

        rules = self.mapping.get_rules(source_version, target_version)
        if not rules:
            detections.append(f"No direct mapping table found for {source_version} -> {target_version}. The app will still copy files and run a generic analysis.")

        for java_file in java_files:
            relative = java_file.relative_to(source_path)
            patched_path = output_path / "ported_mod" / "src" / relative
            patched_path.parent.mkdir(parents=True, exist_ok=True)

            content = java_file.read_text(encoding="utf-8", errors="ignore")
            patched_content = apply_known_replacements(content, rules)

            if patched_content != content:
                detections.append(f"Applied replacement rules to {relative.as_posix()}")

            if ai_enabled:
                ai_client = AIClient(api_key=ai_key)
                suggestion = ai_client.generate_patch(java_file.name, patched_content, source_version, target_version)
                patched_content += "\n\n/*\nAI porting suggestion:\n" + suggestion + "\n*/\n"
                ai_results.append({"file": relative.as_posix(), "summary": suggestion[:160]})

            patched_path.write_text(patched_content, encoding="utf-8")
            result_files.append({"source": str(java_file), "output": str(patched_path)})

        create_gradle_files(output_path, target_version)

        report = {
            "source_version": source_version,
            "target_version": target_version,
            "source_dir": source_dir,
            "output_dir": str(output_path),
            "java_files_total": len(java_files),
            "detections": detections,
            "ai_results": ai_results,
            "completed": True,
        }

        report_path = output_path / "porting_report.json"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        jar_path = output_path / "ported_mod.jar"
        with zipfile.ZipFile(jar_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file in output_path.rglob("*"):
                if file.is_file() and file.name != jar_path.name:
                    archive.write(file, file.relative_to(output_path))

        return {
            "report": report,
            "jar_path": str(jar_path),
            "output_dir": str(output_path),
            "result_files": result_files,
        }
