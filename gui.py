import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QTabWidget, QCheckBox, QRadioButton, QButtonGroup, QGroupBox
)
from PyQt5.Qsci import QsciScintilla, QsciLexerPython, QsciLexerJavaScript, QsciLexerJava
from PyQt5.QtCore import Qt, QTimer, QSettings
from PyQt5.QtGui import QFont, QColor
from api_client import APIClient
from config import Config
from logger import logger
import asyncio

class DuoQEditor(QsciScintilla):
    def __init__(self, language="Python", inline_suggestions=True):
        super().__init__()
        self.inline_suggestions = inline_suggestions
        self.set_language(language)
        self.setup_editor()
        self.setup_indicator()

    def setup_editor(self):
        self.setUtf8(True)
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionSource(QsciScintilla.AcsAll if self.inline_suggestions else QsciScintilla.AcsNone)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setIndentationWidth(4)
        
        margin_font = QFont("Courier", 10)
        self.setMarginsFont(margin_font)

    def setup_indicator(self):
        self.suggestion_indicator = self.indicatorDefine(QsciScintilla.SquiggleIndicator, -1)
        self.setIndicatorForegroundColor(QColor("gray"), self.suggestion_indicator)

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
    
    def toggle_inline_suggestions(self, enabled):
        self.inline_suggestions = enabled
        self.setAutoCompletionSource(QsciScintilla.AcsAll if self.inline_suggestions else QsciScintilla.AcsNone)

    def display_inline_suggestion(self, suggestion, position, length=0):
        """
        Display the suggestion as ethereal text using indicators.
        """
        # Remove any existing indicators in the range
        self.clearIndicatorRange(0, 0, self.lines(), self.lineLength(self.lines() - 1), self.suggestion_indicator)
        
        # Insert the suggestion at the current cursor position
        self.insertAt(suggestion, position // self.lineLength(position), position % self.lineLength(position))
        
        # Highlight the inserted suggestion with the indicator
        self.fillIndicatorRange(position // self.lineLength(position), position % self.lineLength(position),
                                (position + len(suggestion)) // self.lineLength(position + len(suggestion)),
                                (position + len(suggestion)) % self.lineLength(position + len(suggestion)),
                                self.suggestion_indicator)
        
        # Store the suggestion details for acceptance
        self.suggestion_position = position
        self.suggestion_length = len(suggestion)
        self.current_suggestion = suggestion
    
    def accept_inline_suggestion(self):
        """
        Accept the currently displayed inline suggestion.
        """
        if hasattr(self, 'suggestion_position') and hasattr(self, 'suggestion_length'):
            # Remove the indicator
            end_line = (self.suggestion_position + self.suggestion_length) // self.lineLength(self.suggestion_position + self.suggestion_length - 1)
            end_col = (self.suggestion_position + self.suggestion_length) % self.lineLength(self.suggestion_position + self.suggestion_length - 1)
            self.clearIndicatorRange(self.suggestion_position // self.lineLength(self.suggestion_position),
                                     self.suggestion_position % self.lineLength(self.suggestion_position),
                                     end_line, end_col, self.suggestion_indicator)
            
            # Move cursor to the end of the suggestion
            self.setCursorPosition(end_line, end_col)
            
            # Reset suggestion attributes
            del self.suggestion_position
            del self.suggestion_length
            del self.current_suggestion

class SuggestionsPanel(QsciScintilla):
    def __init__(self):
        super().__init__()
        self.setup_panel()

    def setup_panel(self):
        self.setReadOnly(True)
        self.setUtf8(True)
        self.setMarginLineNumbers(0, False)
        self.setMarginsBackgroundColor(Qt.lightGray)
        self.setPaper(Qt.white)
        self.setCaretLineVisible(False)
        self.setFoldMarginColors(Qt.lightGray, Qt.lightGray)
        self.setMarginWidth(0, 0)
        
        suggestion_font = QFont("Courier", 10)
        self.setFont(suggestion_font)

    def display_suggestion(self, suggestion):
        self.setText(suggestion)

class DuoQGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DuoQ - Advanced AI-Powered Code Assistant")
        self.resize(1000, 700)
        self.api_client = APIClient()
        self.settings = QSettings("YourOrganization", "DuoQ")
        self.init_ui()
        self.load_settings()
        self.setup_logic()

    def init_ui(self):
        main_layout = QVBoxLayout()

        self.tabs = QTabWidget()
        self.home_tab = QWidget()
        self.settings_tab = QWidget()
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.settings_tab, "Settings")

        self.init_home_tab()
        self.init_settings_tab()

        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def init_home_tab(self):
        home_layout = QVBoxLayout()

        lang_layout = QHBoxLayout()
        lang_label = QLabel("Select Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(Config.SUPPORTED_LANGUAGES)
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()

        self.code_editor = DuoQEditor(language=self.lang_combo.currentText(), inline_suggestions=True)
        self.suggestions_panel = SuggestionsPanel()

        self.fetch_button_main = QPushButton("Fetch Suggestion")
        self.fetch_button_main.clicked.connect(self.manual_fetch_suggestion)
        self.fetch_button_main.setVisible(False)

        self.status_label = QLabel("Ready")

        home_layout.addLayout(lang_layout)
        home_layout.addWidget(QLabel("Your Code:"))
        home_layout.addWidget(self.code_editor, 3)
        home_layout.addWidget(QLabel("Suggestions:"))
        home_layout.addWidget(self.suggestions_panel, 2)
        home_layout.addWidget(self.fetch_button_main)
        home_layout.addWidget(self.status_label)

        self.home_tab.setLayout(home_layout)

    def init_settings_tab(self):
        settings_layout = QVBoxLayout()

        self.inline_suggestions_checkbox = QCheckBox("Enable Inline Code Suggestions")
        self.inline_suggestions_checkbox.setChecked(True)
        self.inline_suggestions_checkbox.stateChanged.connect(self.toggle_inline_suggestions)

        suggestion_mode_group = QGroupBox("Suggestion Mode")
        suggestion_mode_layout = QHBoxLayout()

        self.auto_radio = QRadioButton("Automatic")
        self.auto_radio.setChecked(True)
        self.manual_radio = QRadioButton("Manual")

        self.suggestion_mode_button_group = QButtonGroup()
        self.suggestion_mode_button_group.addButton(self.auto_radio)
        self.suggestion_mode_button_group.addButton(self.manual_radio)
        self.suggestion_mode_button_group.buttonClicked.connect(self.toggle_suggestion_mode)

        suggestion_mode_layout.addWidget(self.auto_radio)
        suggestion_mode_layout.addWidget(self.manual_radio)
        suggestion_mode_group.setLayout(suggestion_mode_layout)

        settings_layout.addWidget(self.inline_suggestions_checkbox)
        settings_layout.addWidget(suggestion_mode_group)
        settings_layout.addStretch()

        self.settings_tab.setLayout(settings_layout)

    def load_settings(self):
        inline = self.settings.value("inline_suggestions", True, type=bool)
        mode = self.settings.value("suggestion_mode", "Automatic", type=str)
        
        self.inline_suggestions_checkbox.setChecked(inline)
        self.code_editor.toggle_inline_suggestions(inline)

        if mode == "Automatic":
            self.auto_radio.setChecked(True)
            self.fetch_button_main.setVisible(False)
        else:
            self.manual_radio.setChecked(True)
            self.fetch_button_main.setVisible(True)

    def save_settings(self):
        self.settings.setValue("inline_suggestions", self.inline_suggestions)
        self.settings.setValue("suggestion_mode", self.suggestion_mode)

    def toggle_inline_suggestions(self, state):
        enabled = state == Qt.Checked
        self.inline_suggestions = enabled
        self.code_editor.toggle_inline_suggestions(enabled)
        logger.info(f"Inline Code Suggestions {'Enabled' if enabled else 'Disabled'}.")
        self.save_settings()

    def toggle_suggestion_mode(self, button):
        mode = button.text()
        self.suggestion_mode = mode
        logger.info(f"Suggestion Mode set to {mode}.")

        if mode == "Automatic":
            self.debounce_timer.start()
            self.fetch_button_main.setVisible(False)
            try:
                self.code_editor.textChanged.connect(self.on_text_changed)
            except TypeError:
                pass  # Already connected
        else:
            self.debounce_timer.stop()
            self.fetch_button_main.setVisible(True)
            try:
                self.code_editor.textChanged.disconnect(self.on_text_changed)
            except TypeError:
                pass  # Already disconnected
        self.save_settings()

    def setup_logic(self):
        self.lang_combo.currentTextChanged.connect(self.on_language_change)
        self.code_editor.textChanged.connect(self.on_text_changed)
        self.debounce_timer = QTimer()
        self.debounce_timer.setInterval(1000)  # 1 second debounce
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.request_suggestion)

        self.inline_suggestions = True
        self.suggestion_mode = "Automatic"

    def on_language_change(self, language):
        logger.info(f"Language changed to {language}")
        self.code_editor.set_language(language)
        self.suggestions_panel.display_suggestion("")  # Clear suggestions

    def on_text_changed(self):
        if self.suggestion_mode == "Automatic":
            self.debounce_timer.start()

    def request_suggestion(self):
        code = self.code_editor.text()
        language = self.lang_combo.currentText()
        prompt = self.construct_prompt(code, language)
        logger.debug("Requesting suggestion from API.")
        asyncio.create_task(self.fetch_and_display(prompt))

    def manual_fetch_suggestion(self):
        code = self.code_editor.text()
        language = self.lang_combo.currentText()
        prompt = self.construct_prompt(code, language)
        logger.debug("Manually requesting suggestion from API.")
        asyncio.create_task(self.fetch_and_display(prompt))

    def construct_prompt(self, code, language):
        prompt = (
            f"Provide a continuation of the following {language} code, adhering to best practices and standard conventions:\n\n{code}"
        )
        return prompt

    async def fetch_and_display(self, prompt):
        self.status_label.setText("Fetching suggestions...")
        suggestion = await self.api_client.fetch_suggestion(prompt)
        if self.inline_suggestions:
            cursor = self.code_editor.getCursorPosition()
            line, index = cursor
            position = self.code_editor.positionFromLineIndex(line, index)
            self.code_editor.display_inline_suggestion(suggestion, position)
        else:
            self.suggestions_panel.display_suggestion(suggestion)
        self.status_label.setText("Suggestion updated.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Tab:
            if hasattr(self.code_editor, 'current_suggestion'):
                self.code_editor.accept_inline_suggestion()
                event.accept()
                return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

def run_app():
    app = QApplication(sys.argv)
    gui = DuoQGUI()
    gui.show()
    # The event loop is managed by qasync in main.py