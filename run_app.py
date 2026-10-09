import sys
import traceback
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.porting_engine import BytecodeReplacer


class ModPorterUI(QMainWindow):
    """Minecraft Mod Porter - Simple UI for JAR porting."""

    VERSIONS = ["1.12.2", "1.16.5", "1.20.1", "1.21.1", "26.4"]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Minecraft Mod Porter - Fixed")
        self.resize(1000, 700)
        self.jar_path = ""
        self.source_version = ""
        self.output_dir = str(Path.cwd() / "output")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        form = QFormLayout()

        # JAR selection
        self.jar_display = QPlainTextEdit()
        self.jar_display.setReadOnly(True)
        self.jar_display.setFixedHeight(50)
        self.jar_display.setPlaceholderText("No JAR selected")

        # Source version
        self.source_version_label = QLabel("Auto-detect or select")
        self.source_version_label.setStyleSheet("color: #666; font-style: italic;")

        # Target version
        self.target_version = QComboBox()
        self.target_version.addItems(self.VERSIONS)
        self.target_version.setCurrentText("1.20.1")

        # Output directory
        self.output_dir_display = QPlainTextEdit()
        self.output_dir_display.setReadOnly(True)
        self.output_dir_display.setFixedHeight(50)
        self.output_dir_display.setPlainText(self.output_dir)

        form.addRow("Mod JAR:", self.jar_display)
        form.addRow("Source version:", self.source_version_label)
        form.addRow("Target version:", self.target_version)
        form.addRow("Output folder:", self.output_dir_display)

        # Buttons
        btn_layout = QHBoxLayout()
        self.select_jar_btn = QPushButton("📁 Select JAR")
        self.select_output_btn = QPushButton("📁 Change output")
        self.port_btn = QPushButton("🚀 PORT MOD")
        self.port_btn.setStyleSheet(
            "background: #28a745; color: white; font-weight: bold; padding: 12px; font-size: 14px; border-radius: 4px;"
        )

        self.select_jar_btn.clicked.connect(self.select_jar)
        self.select_output_btn.clicked.connect(self.select_output)
        self.port_btn.clicked.connect(self.run_port)

        btn_layout.addWidget(self.select_jar_btn)
        btn_layout.addWidget(self.select_output_btn)
        btn_layout.addWidget(self.port_btn)

        # Log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText(
            "Ready.\n\n"
            "Step 1: Click 'Select JAR' to load your mod\n"
            "Step 2: Select target Minecraft version\n"
            "Step 3: Click 'PORT MOD'\n\n"
            "Supported migrations:\n"
            "  1.12.2 → 1.20.1\n"
            "  1.16.5 → 1.20.1\n"
            "  1.20.1 → 1.21.1\n\n"
        )
        self.log.setStyleSheet("background: #f5f5f5; font-family: monospace; font-size: 10px;")

        main_layout.addLayout(form)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("Processing log:"))
        main_layout.addWidget(self.log)

    def log_msg(self, text: str) -> None:
        self.log.appendPlainText(text)

    def select_jar(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Mod JAR", filter="JAR files (*.jar);;All files (*)")
        if file_path:
            self.jar_path = file_path
            jar_name = Path(file_path).name
            self.jar_display.setPlainText(jar_name)
            self.log_msg(f"✓ Loaded: {jar_name}")

            # Try to detect version
            detected = self.detect_version_from_name(jar_name)
            if detected:
                self.source_version = detected
                self.source_version_label.setText(detected)
                self.log_msg(f"✓ Detected version: {detected}")

    def select_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_dir = folder
            self.output_dir_display.setPlainText(folder)
            self.log_msg(f"✓ Output: {folder}")

    def detect_version_from_name(self, jar_name: str) -> str:
        """Try to detect Minecraft version from filename."""
        for version in self.VERSIONS:
            if version.replace(".", "") in jar_name.replace(".", "").lower():
                return version
            if version in jar_name:
                return version
        return ""

    def run_port(self) -> None:
        if not self.jar_path:
            QMessageBox.warning(self, "Error", "Please select a JAR file first.")
            return

        # Get source version
        source_version = self.source_version
        if not source_version:
            dlg = QInputDialog(self)
            dlg.setWindowTitle("Select Source Version")
            dlg.setLabelText("Source Minecraft/Forge version:")
            dlg.setComboBoxItems(self.VERSIONS)
            if dlg.exec() == QInputDialog.Accepted:
                source_version = dlg.textValue()
            else:
                return

        target_version = self.target_version.currentText()

        if source_version == target_version:
            QMessageBox.warning(self, "Error", "Source and target versions are the same.")
            return

        # Check if migration is supported
        if (source_version, target_version) not in BytecodeReplacer.MIGRATION_RULES:
            QMessageBox.warning(
                self,
                "Unsupported",
                f"Migration {source_version} → {target_version} is not yet supported.\n\n"
                f"Supported routes:\n"
                f"  1.12.2 → 1.20.1\n"
                f"  1.16.5 → 1.20.1\n"
                f"  1.20.1 → 1.21.1",
            )
            return

        self.log_msg(f"\n{'='*70}")
        self.log_msg(f"Starting port: {source_version} → {target_version}")
        self.log_msg(f"Input: {Path(self.jar_path).name}")
        self.log_msg(f"{'='*70}\n")

        try:
            result = BytecodeReplacer.apply_rules(
                jar_path=self.jar_path,
                source_version=source_version,
                target_version=target_version,
                output_dir=self.output_dir,
            )

            report = result["report"]
            self.log_msg(f"✓ PORTING COMPLETED")
            self.log_msg(f"  Output: {Path(result['jar_path']).name}")
            self.log_msg(f"  Classes processed: {report['class_files_total']}")
            self.log_msg(f"  Classes patched: {report['class_files_patched']}")
            self.log_msg(f"  Resources updated: {report['resource_files_updated']}")
            self.log_msg(f"\n  Report: {Path(result['report_path']).name}")
            self.log_msg(f"{'='*70}\n")

            QMessageBox.information(
                self,
                "✓ Success",
                f"Mod ported successfully!\n\n"
                f"Output JAR: {Path(result['jar_path']).name}\n\n"
                f"Please test the mod in-game before distribution.",
            )
        except ValueError as ve:
            self.log_msg(f"✗ ERROR: {str(ve)}")
            self.log_msg(f"{'='*70}\n")
            QMessageBox.critical(self, "✗ Error", str(ve))
        except Exception as e:
            error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
            self.log_msg(f"✗ ERROR: {error_msg[:200]}")
            self.log_msg(f"{'='*70}\n")
            QMessageBox.critical(self, "✗ Critical Error", f"Porting failed:\n{str(e)}")  


def main() -> int:
    app = QApplication(sys.argv)
    window = ModPorterUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
