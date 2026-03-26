import sys
import os
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow

def load_stylesheet(app):
    style_path = os.path.join(os.path.dirname(__file__), 'src', 'styles', 'dark_theme.qss')
    try:
        with open(style_path, 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Failed to load stylesheet: {e}")

def main():
    app = QApplication(sys.argv)
    
    # Load and apply QSS theme
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
