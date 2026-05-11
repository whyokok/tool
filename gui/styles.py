"""
Modern UI styles for the application.
"""

MAIN_STYLE = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QPushButton {
    background-color: #0078d4;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #106ebe;
}

QPushButton:pressed {
    background-color: #005a9e;
}

QPushButton:disabled {
    background-color: #c8c8c8;
}

QLineEdit {
    padding: 10px 14px;
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
    font-size: 14px;
}

QLineEdit:focus {
    border-color: #0078d4;
}

QComboBox {
    padding: 8px 12px;
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
}

QComboBox:focus {
    border-color: #0078d4;
}

QTableWidget {
    background-color: white;
    border: 1px solid #e1e1e1;
    border-radius: 4px;
    gridline-color: #f0f0f0;
}

QTableWidget::item {
    padding: 8px;
}

QTableWidget::item:selected {
    background-color: #e5f3ff;
    color: black;
}

QHeaderView::section {
    background-color: #fafafa;
    padding: 10px;
    border: none;
    border-bottom: 1px solid #e1e1e1;
    font-weight: 600;
}

QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #e1e1e1;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 4px;
}

QLabel {
    color: #323232;
}

QGroupBox {
    font-weight: 600;
    border: 1px solid #e1e1e1;
    border-radius: 6px;
    margin-top: 12px;
    padding-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
}

QTextEdit {
    border: 1px solid #d1d1d1;
    border-radius: 4px;
    background-color: white;
    padding: 8px;
}

QSplitter::handle {
    background-color: #e1e1e1;
}
"""

FILE_TYPE_ICONS = {
    "pdf": "#e74c3c",
    "word": "#2b579a",
    "ppt": "#d24726",
    "txt": "#95a5a6"
}

FILE_TYPE_NAMES = {
    "pdf": "PDF",
    "word": "Word",
    "ppt": "PowerPoint",
    "txt": "Text"
}
