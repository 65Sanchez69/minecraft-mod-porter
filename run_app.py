import sys
import zipfile
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

from app.porting_engine import JarPorter


class ModPorterUI(QMainWindow):
    """Simple mod porting UI - Load JAR -> Select version -> Port."""

    VERSIONS = ["1.7.10", "1.12.2", "1.16.5", "1.20.1", "1.21.1", "26.4"]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Minecraft Mod Porter")
        self.resize(950, 650)
        self.porter = JarPorter()
        self.jar_path = ""
        self.source_version = ""
        self.output_dir = str(Path.cwd() / "output")

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        form = QFormLayout()

        self.jar_display = QPlainTextEdit()
        self.jar_display.setReadOnly(True)
        self.jar_display.setFixedHeight(50)
        self.jar_display.setPlaceholderText("No JAR selected")

        self.source_version_label = QLabel("Auto-detected")
        self.source_version_label.setStyleSheet("color: #666; font-style: italic;")

        self.target_version = QComboBox()
        self.target_version.addItems(self.VERSIONS)
        self.target_version.setCurrentText("1.21.1")

        self.output_dir_display = QPlainTextEdit()
        self.output_dir_display.setReadOnly(True)
        self.output_dir_display.setFixedHeight(50)
        self.output_dir_display.setPlaceholderText("Output folder")
        self.output_dir_display.setPlainText(self.output_dir)

        self.ai_checkbox = QCheckBox("Enable AI suggestions (requires GROQ_API_KEY)")
        self.ai_checkbox.setChecked(False)

        form.addRow("Mod JAR file:", self.jar_display)
        form.addRow("Source version:", self.source_version_label)
        form.addRow("Target version:", self.target_version)
        form.addRow("Output folder:", self.output_dir_display)
        form.addRow("Options:", self.ai_checkbox)

        btn_layout = QHBoxLayout()
        self.select_jar_btn = QPushButton("📁 Select JAR")
        self.select_output_btn = QPushButton("📁 Change output")
        self.port_btn = QPushButton("🚀 Port mod")
        self.port_btn.setStyleSheet(
            "background: #28a745; color: white; font-weight: bold; padding: 10px; font-size: 14px; border-radius: 4px;"
        )

        self.select_jar_btn.clicked.connect(self.select_jar)
        self.select_output_btn.clicked.connect(self.select_output)
        self.port_btn.clicked.connect(self.run_port)

        btn_layout.addWidget(self.select_jar_btn)
        btn_layout.addWidget(self.select_output_btn)
        btn_layout.addWidget(self.port_btn)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText("Ready.\n\n1. Click 'Select JAR' to load a mod\n2. Pick target Minecraft version\n3. Click 'Port mod'\n")
        self.log.setStyleSheet("background: #f5f5f5; font-family: monospace; font-size: 10px;")

        main_layout.addLayout(form)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log)

    def log_msg(self, text: str) -> None:
        self.log.appendPlainText(text)

    def select_jar(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select mod JAR", filter="JAR files (*.jar);;All files (*)")
        if file_path:
            self.jar_path = file_path
            self.jar_display.setPlainText(file_path)
            self.log_msg(f"✓ JAR selected: {Path(file_path).name}")

            detected = self.detect_version_from_jar(file_path)
            if detected:
                self.source_version = detected
                self.source_version_label.setText(detected)
                self.log_msg(f"✓ Detected version: {detected}")
            else:
                self.log_msg("? Could not auto-detect version, you can still proceed")

    def select_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir = folder
            self.output_dir_display.setPlainText(folder)
            self.log_msg(f"✓ Output folder: {folder}")

    def detect_version_from_jar(self, jar_path: str) -> str:
        """Try to detect Minecraft version from JAR."""
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                file_list = zf.namelist()

                for version in self.VERSIONS:
                    for file_name in file_list:
                        if version.replace(".", "") in file_name.lower():
                            return version
        except Exception:
            pass
        return ""

    def run_port(self) -> None:
        if not self.jar_path:
            QMessageBox.warning(self, "Error", "Please select a JAR file first.")
            return

        if not self.source_version:
            dlg = QInputDialog(self)
            dlg.setWindowTitle("Select source version")
            dlg.setLabelText("Could not detect version. Select source version:")
            dlg.setComboBoxItems(self.VERSIONS)
            dlg.setComboBoxEditable(False)
            if dlg.exec() == QInputDialog.Accepted:
                self.source_version = dlg.textValue()
                self.source_version_label.setText(self.source_version)
            else:
                return

        target_version = self.target_version.currentText()

        if self.source_version == target_version:
            QMessageBox.warning(self, "Error", "Source and target versions are the same.")
            return

        self.log_msg("\n" + "="*60)
        self.log_msg(f"Starting port: {self.source_version} → {target_version}")
        self.log_msg("="*60)

        try:
            result = self.porter.port_jar(
                jar_path=self.jar_path,
                source_version=self.source_version,
                target_version=target_version,
                output_dir=self.output_dir,
                ai_enabled=self.ai_checkbox.isChecked(),
            )

            self.log_msg("\n✓ PORTING COMPLETED SUCCESSFULLY")
            self.log_msg(f"  Output JAR: {result['jar_path']}")
            self.log_msg(
                f"  Classes processed: {result['report']['class_files_processed']}, "
                f"Patched: {result['report']['class_files_patched']}"
            )
            self.log_msg(f"  Report: {self.output_dir}/porting_report.json")
            self.log_msg("="*60 + "\n")

            QMessageBox.information(
                self,
                "✓ Success",
                f"Mod ported successfully!\n\n{Path(result['jar_path']).name}",
            )
        except Exception as e:
            self.log_msg(f"\n✗ ERROR: {str(e)}")
            self.log_msg("="*60 + "\n")
            QMessageBox.critical(self, "✗ Error", f"Porting failed:\n{str(e)}")


def main() -> int:
    app = QApplication(sys.argv)
    window = ModPorterUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
