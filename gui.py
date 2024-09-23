# gui.py

import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QMessageBox
)
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerJavaScript, QsciLexerJava
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont  # Imported QFont
from api_client import APIClient
from config import Config
from logger import logger
import asyncio

class CodeEditor(QsciScintilla):
    def __init__(self, language="Python"):
        super().__init__()
        self.set_language(language)
        self.setup_editor()

    def setup_editor(self):
        self.setUtf8(True)
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        
        # Create a QFont object for the margins
        margin_font = QFont("Courier", 10)
        self.setMarginsFont(margin_font)
        
        # Optionally set the margin font point size
        # self.setMarginsFontPointSize(10)  # Can be removed if using QFont with size

    def set_language(self, language):
        if language == "Python":
            lexer = QsciLexerPython()
        elif language == "JavaScript":
            lexer = QsciLexerJavaScript()
        elif language == "Java":
            lexer = QsciLexerJava()
        else:
            lexer = QsciLexerPython()  # Default to Python
        lexer.setDefaultFont(self.font())
        self.setLexer(lexer)

class SuggestionsPanel(QsciScintilla):
    def __init__(self):
        super().__init__()
        self.setup_panel()

    def setup_panel(self):
        self.setReadOnly(True)
        self.setUtf8(True)
        # Corrected: Specify margin index (e.g., 0) and the boolean value
        self.setMarginLineNumbers(0, False)
        self.setMarginsBackgroundColor(Qt.lightGray)
        self.setPaper(Qt.white)  # Corrected method
        self.setCaretLineVisible(False)
        self.setFoldMarginColors(Qt.lightGray, Qt.lightGray)
        # Removed invalid attribute 'NoMargin'
        # self.setMarginType(0, QsciScintilla.NoMargin)
        self.setMarginWidth(0, 0)  # Set margin 0 width to 0 to hide it
        
        # Optionally, set a default font for the suggestions panel
        suggestion_font = QFont("Courier", 10)
        self.setFont(suggestion_font)

    def display_suggestion(self, suggestion):
        self.setText(suggestion)

class CodeAssistGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeAssist - Advanced AI-Powered Code Assistant")
        self.resize(1000, 700)
        self.api_client = APIClient()
        self.init_ui()
        self.setup_logic()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Language Selection
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Select Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(Config.SUPPORTED_LANGUAGES)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()

        # Code Editor
        self.code_editor = CodeEditor(language=self.lang_combo.currentText())

        # Suggestions Panel
        self.suggestions_panel = SuggestionsPanel()

        # Status Bar
        self.status_label = QLabel("Ready")

        main_layout.addLayout(lang_layout)
        main_layout.addWidget(QLabel("Your Code:"))
        main_layout.addWidget(self.code_editor, 3)
        main_layout.addWidget(QLabel("Suggestions:"))
        main_layout.addWidget(self.suggestions_panel, 2)
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def setup_logic(self):
        self.lang_combo.currentTextChanged.connect(self.on_language_change)
        self.code_editor.textChanged.connect(self.on_text_changed)
        self.debounce_timer = QTimer()
        self.debounce_timer.setInterval(1000)  # 1 second debounce
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.request_suggestion)

    def on_language_change(self, language):
        logger.info(f"Language changed to {language}")
        self.code_editor.set_language(language)
        self.suggestions_panel.display_suggestion("")  # Clear suggestions

    def on_text_changed(self):
        self.debounce_timer.start()

    def request_suggestion(self):
        code = self.code_editor.text()
        language = self.lang_combo.currentText()
        prompt = self.construct_prompt(code, language)
        logger.debug("Requesting suggestion from API.")
        asyncio.create_task(self.fetch_and_display(prompt))

    def construct_prompt(self, code, language):
        prompt = (
            f"Provide a continuation of the following {language} code, adhering to best practices and standard conventions:\n\n{code}"
        )
        return prompt

    async def fetch_and_display(self, prompt):
        self.status_label.setText("Fetching suggestions...")
        suggestion = await self.api_client.fetch_suggestion(prompt)
        self.suggestions_panel.display_suggestion(suggestion)
        self.status_label.setText("Suggestion updated.")

def run_app():
    app = QApplication(sys.argv)
    gui = CodeAssistGUI()
    gui.show()
    # Note: The event loop is now managed by qasync in main.py
