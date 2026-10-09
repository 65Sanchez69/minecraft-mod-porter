import sys
import traceback
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.porting_engine import AppPortingEngine


class IndustrialCraftPorterUI(QMainWindow):
    """Focused UI for Industrial Craft / Forge porting."""

    VERSIONS = ["1.12.2", "1.16.5", "1.20.1", "1.21.1", "26.4"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("IndustrialCraft Forge Porting Tool")
        self.resize(1000, 700)
        self.jar_path = ""
        self.output_dir = str(Path.cwd() / "output")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        form = QFormLayout()

        self.jar_display = QPlainTextEdit()
        self.jar_display.setReadOnly(True)
        self.jar_display.setFixedHeight(60)

        self.source_version_combo = QComboBox()
        self.source_version_combo.addItems(self.VERSIONS)
        self.source_version_combo.setCurrentText("1.12.2")

        self.target_version_combo = QComboBox()
        self.target_version_combo.addItems(self.VERSIONS)
        self.target_version_combo.setCurrentText("1.20.1")

        self.output_display = QPlainTextEdit()
        self.output_display.setReadOnly(True)
        self.output_display.setFixedHeight(60)
        self.output_display.setPlainText(self.output_dir)

        form.addRow("JAR mod:", self.jar_display)
        form.addRow("Source version:", self.source_version_combo)
        form.addRow("Target version:", self.target_version_combo)
        form.addRow("Output folder:", self.output_display)

        btns = QHBoxLayout()
        self.select_jar_btn = QPushButton("Select JAR")
        self.output_btn = QPushButton("Select output")
        self.port_btn = QPushButton("PORT MOD")
        self.port_btn.setStyleSheet("background: #28a745; color: white; font-weight: bold; padding: 10px;")

        self.select_jar_btn.clicked.connect(self.select_jar)
        self.output_btn.clicked.connect(self.select_output)
        self.port_btn.clicked.connect(self.run_port)

        btns.addWidget(self.select_jar_btn)
        btns.addWidget(self.output_btn)
        btns.addWidget(self.port_btn)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText(
            "IndustrialCraft Forge Port Tool\n\n"
            "1. Load a JAR mod\n"
            "2. Choose source and target Forge versions\n"
            "3. Click PORT MOD\n\n"
            "This is a best-effort porting tool for Industrial Craft-like Forge mods.\n"
        )

        layout.addLayout(form)
        layout.addLayout(btns)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log)

    def log_msg(self, text: str) -> None:
        self.log.appendPlainText(text)

    def select_jar(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select mod JAR", filter="JAR files (*.jar)")
        if file_path:
            self.jar_path = file_path
            self.jar_display.setPlainText(Path(file_path).name)
            self.log_msg(f"\n✓ JAR selected: {Path(file_path).name}")

    def select_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir = folder
            self.output_display.setPlainText(folder)
            self.log_msg(f"✓ Output directory: {folder}")

    def run_port(self) -> None:
        if not self.jar_path:
            QMessageBox.warning(self, "Error", "Select a JAR first.")
            return

        source_version = self.source_version_combo.currentText()
        target_version = self.target_version_combo.currentText()

        if source_version == target_version:
            QMessageBox.warning(self, "Error", "Source and target versions are the same.")
            return

        self.log_msg(f"\n{'='*70}\n")
        self.log_msg(f"Starting Industrial Craft port: {source_version} -> {target_version}\n")

        try:
            result = AppPortingEngine.port_jar(
                jar_path=self.jar_path,
                source_version=source_version,
                target_version=target_version,
                output_dir=self.output_dir,
            )

            self.log_msg(f"✓ Output JAR: {result['jar_path']}\n")
            self.log_msg(f"✓ Report: {result['report_path']}\n")
            self.log_msg(f"Patched classes: {result['report']['patched_classes']}\n")
            self.log_msg(f"Resource updates: {result['report']['resource_updates']}\n")
            self.log_msg(f"Metadata fixes: {len(result['report'].get('metadata_fixes', []))}\n")
            self.log_msg("\nNOTE: This is best-effort, and complex mods still need manual validation.\n")
            self.log_msg(f"{'='*70}\n")

            QMessageBox.information(
                self,
                "Success",
                f"Porting complete!\n\nOutput: {result['jar_path']}\nReport: {result['report_path']}",
            )
        except Exception as e:
            self.log_msg(f"\n✗ ERROR: {str(e)}\n")
            self.log_msg(traceback.format_exc()[:500])
            QMessageBox.critical(self, "Port failed", str(e))


def main():
    app = QApplication(sys.argv)
    window = IndustrialCraftPorterUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
