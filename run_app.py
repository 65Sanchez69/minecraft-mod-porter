import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
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

from app.porting_engine import JarPorter


class ModPorterUI(QMainWindow):
    """Simple mod porting UI."""

    VERSIONS = ["1.7.10", "1.12.2", "1.16.5", "1.20.1", "1.21.1", "26.4"]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Minecraft Mod Porter")
        self.resize(900, 600)
        self.porter = JarPorter()
        self.jar_path = ""

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Form
        form = QFormLayout()

        self.jar_display = QPlainTextEdit()
        self.jar_display.setReadOnly(True)
        self.jar_display.setFixedHeight(60)
        self.jar_display.setPlaceholderText("No JAR selected")

        self.target_version = QComboBox()
        self.target_version.addItems(self.VERSIONS)
        self.target_version.setCurrentText("1.21.1")

        self.output_dir_display = QPlainTextEdit()
        self.output_dir_display.setReadOnly(True)
        self.output_dir_display.setFixedHeight(60)
        self.output_dir_display.setPlaceholderText("Output folder (auto-generated if not set)")

        self.ai_checkbox = QCheckBox("Enable AI patches (if GROQ_API_KEY set)")
        self.ai_checkbox.setChecked(True)

        form.addRow("Mod JAR:", self.jar_display)
        form.addRow("Target version:", self.target_version)
        form.addRow("Output folder:", self.output_dir_display)
        form.addRow("Options:", self.ai_checkbox)

        # Buttons
        btn_layout = QHBoxLayout()
        self.select_jar_btn = QPushButton("Select JAR")
        self.select_output_btn = QPushButton("Select output")
        self.port_btn = QPushButton("Port mod")
        self.port_btn.setStyleSheet("background: #28a745; color: white; font-weight: bold; padding: 8px;")

        self.select_jar_btn.clicked.connect(self.select_jar)
        self.select_output_btn.clicked.connect(self.select_output)
        self.port_btn.clicked.connect(self.run_port)

        btn_layout.addWidget(self.select_jar_btn)
        btn_layout.addWidget(self.select_output_btn)
        btn_layout.addWidget(self.port_btn)

        # Log
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText("Ready to port a mod JAR.\n")

        main_layout.addLayout(form)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(QLabel("Log:"))
        main_layout.addWidget(self.log)

    def log_msg(self, text: str) -> None:
        self.log.appendPlainText(text)

    def select_jar(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(self, "Select mod JAR", filter="JAR files (*.jar)")
        if file_path:
            self.jar_path = file_path
            self.jar_display.setPlainText(file_path)
            self.log_msg(f"Selected JAR: {file_path}")

    def select_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir_display.setPlainText(folder)
            self.log_msg(f"Output folder: {folder}")

    def run_port(self) -> None:
        if not self.jar_path:
            QMessageBox.warning(self, "Error", "Please select a JAR file first.")
            return

        output_dir = self.output_dir_display.toPlainText().strip() or str(Path.cwd() / "output")
        target_version = self.target_version.currentText()

        # Detect source version from JAR
        source_version = self.detect_version(self.jar_path)
        if not source_version:
            QMessageBox.warning(self, "Error", "Could not detect source Minecraft version from JAR.")
            return

        if source_version == target_version:
            QMessageBox.warning(self, "Error", "Source and target versions are the same.")
            return

        self.log_msg(f"Porting {self.jar_path} from {source_version} to {target_version}...")

        try:
            result = self.porter.port_jar(
                jar_path=self.jar_path,
                source_version=source_version,
                target_version=target_version,
                output_dir=output_dir,
            )

            self.log_msg(f"✓ Porting complete!")
            self.log_msg(f"Output JAR: {result['jar_path']}")
            self.log_msg(f"Classes patched: {result['report']['class_files_patched']}/{result['report']['class_files_processed']}")
            self.log_msg(f"Report: {output_dir}/porting_report.json")

            QMessageBox.information(
                self,
                "Success",
                f"Mod ported successfully!\n\nOutput: {result['jar_path']}",
            )
        except Exception as e:
            self.log_msg(f"✗ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Porting failed: {str(e)}")

    def detect_version(self, jar_path: str) -> str:
        """Detect Minecraft version from JAR metadata."""
        try:
            with zipfile.ZipFile(jar_path, "r") as zf:
                # Check mcmod.info or similar metadata
                file_list = zf.namelist()
                for name in file_list:
                    if "mcmod" in name.lower() or "META-INF" in name:
                        return None  # Could implement version detection here
        except Exception:
            pass

        # Ask user to select version
        from PySide6.QtWidgets import QInputDialog

        version, ok = QInputDialog.getItem(
            self,
            "Detect version",
            "Could not auto-detect source version. Select it:",
            self.VERSIONS,
        )
        return version if ok else None


def main() -> int:
    app = QApplication(sys.argv)
    window = ModPorterUI()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
