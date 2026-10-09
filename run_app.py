from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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

from app.porting_engine import PortingEngine


class ModPorterWindow(QMainWindow):
    """Desktop UI for the Minecraft mod porting workflow."""

    VERSION_OPTIONS = [
        "1.7.10",
        "1.12.2",
        "1.16.5",
        "1.20.1",
        "1.21.1",
        "26.4",
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Minecraft Mod Porting Toolkit")
        self.resize(1100, 720)
        self.engine = PortingEngine()

        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        form = QFormLayout()

        self.source_dir_edit = QPlainTextEdit()
        self.source_dir_edit.setFixedHeight(70)
        self.source_dir_edit.setPlaceholderText("Select mod source folder")

        self.output_dir_edit = QPlainTextEdit()
        self.output_dir_edit.setFixedHeight(70)
        self.output_dir_edit.setPlaceholderText("Select output folder")

        self.source_version_combo = QComboBox()
        self.source_version_combo.addItems(self.VERSION_OPTIONS)
        self.source_version_combo.setCurrentText("1.12.2")

        self.target_version_combo = QComboBox()
        self.target_version_combo.addItems(self.VERSION_OPTIONS)
        self.target_version_combo.setCurrentText("1.21.1")

        self.ai_enabled_checkbox = QCheckBox("Enable AI-assisted suggestions")
        self.ai_enabled_checkbox.setChecked(True)

        buttons = QHBoxLayout()
        self.select_source_button = QPushButton("Select source dir")
        self.select_output_button = QPushButton("Select output dir")
        self.port_button = QPushButton("Port mod")
        self.port_button.setStyleSheet("background: #1e88e5; color: white; font-weight: bold;")

        self.select_source_button.clicked.connect(self.select_source_dir)
        self.select_output_button.clicked.connect(self.select_output_dir)
        self.port_button.clicked.connect(self.run_port)

        buttons.addWidget(self.select_source_button)
        buttons.addWidget(self.select_output_button)
        buttons.addWidget(self.port_button)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlainText("Minecraft Mod Porting Toolkit ready.\n")

        form.addRow("Source folder:", self.source_dir_edit)
        form.addRow("Output folder:", self.output_dir_edit)
        form.addRow("Source version:", self.source_version_combo)
        form.addRow("Target version:", self.target_version_combo)
        form.addRow("Options:", self.ai_enabled_checkbox)

        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Porting log:"))
        layout.addWidget(self.log)

    def log_message(self, text: str) -> None:
        self.log.appendPlainText(text)

    def select_source_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select source mod folder")
        if folder:
            self.source_dir_edit.setPlainText(folder)
            self.log_message(f"Selected source directory: {folder}")

    def select_output_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if folder:
            self.output_dir_edit.setPlainText(folder)
            self.log_message(f"Selected output directory: {folder}")

    def run_port(self) -> None:
        source_dir = self.source_dir_edit.toPlainText().strip()
        output_dir = self.output_dir_edit.toPlainText().strip() or str(Path.cwd() / "output")

        if not source_dir:
            QMessageBox.warning(self, "Missing source directory", "Please choose a mod source folder first.")
            return

        source_version = self.source_version_combo.currentText()
        target_version = self.target_version_combo.currentText()
        ai_enabled = self.ai_enabled_checkbox.isChecked()

        self.log_message(f"Starting port from {source_version} to {target_version}...")

        try:
            from os import getenv
            ai_key = getenv("GROQ_API_KEY") if ai_enabled else None

            result = self.engine.port_mod(
                source_dir=source_dir,
                source_version=source_version,
                target_version=target_version,
                output_dir=output_dir,
                ai_enabled=ai_enabled,
                ai_key=ai_key,
            )

            self.log_message(f"Processed Java files: {result['report']['java_files_total']}")
            self.log_message(f"Output folder: {result['output_dir']}")
            self.log_message(f"Artifact: {result['jar_path']}")
            self.log_message("Porting finished successfully.")

            if ai_enabled:
                self.log_message("AI suggestions were appended to patched files when available.")

            QMessageBox.information(
                self,
                "Porting finished",
                f"Porting process completed successfully.\nArtifact: {result['jar_path']}\nOutput directory: {result['output_dir']}",
            )
        except Exception as exc:  # pragma: no cover - GUI path
            self.log_message(f"ERROR: {exc}")
            QMessageBox.critical(self, "Porting failed", str(exc))
