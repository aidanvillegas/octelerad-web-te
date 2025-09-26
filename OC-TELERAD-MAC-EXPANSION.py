# OC-TELERAD-MAC-EXPANSION.py
import os
import sys
import pandas as pd
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QLineEdit, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QHeaderView, QSplitter, QStyledItemDelegate, QLineEdit, QDialog, QSizePolicy, QTextEdit, QMenu, QAction, QMessageBox, QLabel, QFileDialog, QListWidget, QApplication, QMainWindow, QTableView, QLineEdit, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QMessageBox
from PyQt5.QtGui import QPixmap, QFont, QKeyEvent
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from pandas_model import PandasModel
from database_manager import DatabaseManager
import keyboard
from PyQt5.QtCore import QThread, QTimer
import pyperclip
import pyautogui
import time

# Utility function to get the path of a resource. Used for bundling with PyInstaller.
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Main window class for the application
class MainWindow(QMainWindow):
    """
    The main window class for the OC TELERAD Text Expander application.
    This class handles the initialization of the UI components, database management,
    and user interactions.
    """

    def __init__(self):
        super().__init__()
        # Window setup
        self.setWindowTitle("Orange Coast Teleradiology Corp - Research Division - Text Expander")
        self.setGeometry(200, 200, 1200, 800)

        # Application styling
        self.setStyleSheet("""
            QMainWindow {background-color: black;}
            QLabel {color: white;}
            QPushButton {background-color: #333; color: white; border: 1px solid #555;}
            QLineEdit {background-color: white; color: black;}
        """)
        # Initialize an empty DataFrame for the application to use
        self.original_df = pd.DataFrame(columns=['Label', 'Expansion', 'Diagnosis'])

        # Initialize the UI components
        self.initUI()

        # Initialize DatabaseManager without a specific path
        self.db_manager = DatabaseManager()

        # Prompt the user for database selection
        self.prompt_for_database()

        # After the user makes a selection, appropriate database actions are taken
        # Now it's safe to initialize listeners as the database context is established
        self.keyboardListener = KeyboardListener(self.db_manager)
        self.clipboardMonitor = ClipboardMonitor(self.db_manager)
        self.clipboardMonitor.ExpansionCopied.connect(self.onExpansionCopied)
        self.keyboardListener.escapePressed.connect(self.handleEscapePress)

    # Method to prompt user for database action on startup
    def prompt_for_database(self):
        while True:
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Start Menu")
            msg_box.setText("WELCOME TO OC TELERAD OPERATONS: Do you want to load the last database, start with a new one, or import a new one?")
            
            # Add buttons in reverse order
            new_btn = msg_box.addButton("New Database", QMessageBox.AcceptRole)
            import_btn = msg_box.addButton("Import Database", QMessageBox.AcceptRole)
            exit_btn = msg_box.addButton("Exit", QMessageBox.DestructiveRole)
            load_btn = msg_box.addButton("Load Last", QMessageBox.AcceptRole)

            msg_box.exec_()  # This line should display the prompt
            if msg_box.clickedButton() == load_btn:
                # Logic to load the last database
                self.load_last_database()
                break
            elif msg_box.clickedButton() == new_btn:
                # Logic to handle a new database
                self.new_database()
                break
            elif msg_box.clickedButton() == import_btn:
                # Logic to import a new database
                self.import_csv()
                break
            elif msg_box.clickedButton() == cancel_btn or msg_box.clickedButton() is None:
                # Exit the application if the user selects 'Exit' or closes the dialog.
                sys.exit()
        
    def initUI(self):
        """
        Method to initialize UI components and start the main event loop.
        """
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Load and display the logo
        logoLabel = QLabel(self)
        # Get the directory of the current script
        script_dir = os.path.dirname(sys.argv[0])

        # Construct the path to the octelerad_logo.png file
        logo_file_path = resource_path("octelerad_logo.png")
        # Use logo_file_path to set the logo in your code
        logoPixmap = QPixmap(logo_file_path)
        
        logoLabel.setPixmap(logoPixmap)
        logoLabel.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logoLabel)

        self.menuButton = QPushButton("Menu")
        self.menuButton.clicked.connect(self.showMenu)
        self.menuButton.setStyleSheet("""
            QPushButton {
                height: 40px;
                font-size: 16px;
            }
        """)
        main_layout.addWidget(self.menuButton)

        if hasattr(self, 'db_manager'):
            self.clipboardMonitor = ClipboardMonitor(self.db_manager)
            self.clipboardMonitor.ExpansionCopied.connect(self.onExpansionCopied)
        

        # Search bar setup
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.on_search)
        self.search_bar.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 6px;
                border: 1px solid gray;
                border-radius: 4px;
            }
        """)
        main_layout.addWidget(self.search_bar)
        self.statusBar().showMessage("Ready")

        # Table view setup
        self.table_view = QTableView(self.central_widget)
        self.update_table_view(self.original_df)
        self.table_view.setEditTriggers(QTableView.DoubleClicked | QTableView.SelectedClicked)
        self.table_view.clicked.connect(self.openCustomEditor)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.MultiSelection)
        self.table_view.setAlternatingRowColors(True)
        self.delegate = LineEditDelegate(self.table_view)
        self.table_view.setItemDelegate(self.delegate)

        # Customizing the appearance of table headers and data
        self.table_view.setStyleSheet("""
            QHeaderView::section {
                background-color: #646464;
                color: white;
                border: 1px solid #525252;
                font-size: 14px;
                font-weight: bold;
                padding: 4px;
            }
            QTableView {
                selection-background-color: #4a6984;
                selection-color: white;
                font-size: 12px;
                color: black;
                gridline-color: #c0c0c0;
            }
            QTableView QTableCornerButton::section {
                background-color: #646464;
            }
        """)

        main_layout.addWidget(self.table_view)
        self.central_widget.setLayout(main_layout)
        pass
    
    def load_last_database(self):
        """
        Method to handle loading the last used database.
        """
        print("Loading the last database...")
        with open('last_db_path.txt', 'r') as f:
            last_db_path = f.read().strip()

        if last_db_path and os.path.exists(last_db_path):
            try:
                df_loaded = pd.read_csv(last_db_path)
                self.original_df = self.standardize_column_names(df_loaded)
                self.db_manager.df = self.original_df
                self.db_manager.db_path = last_db_path  # Ensure db_manager path is updated
                self.update_table_view(self.original_df)
                self.save_last_db_path(last_db_path)  # Confirm path saving
                self.statusBar().showMessage(f"Loaded database from {last_db_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Unable to load the database from {last_db_path}: {e}")
                self.new_database()
        else:
            QMessageBox.warning(self, "Error", "Last database path is invalid or does not exist.")
            self.new_database()
    def save_last_db_path(self, path):
        """
        Method to save the path of the last database used.
        """
        with open('last_db_path.txt', 'w') as f:
            f.write(path)


    def new_database(self):
        """
        Method to create a new database.
        """
        # Define the structure of the new, empty DataFrame 
        self.original_df = pd.DataFrame(columns=['Label', 'Expansion', 'Diagnosis'])
        self.db_manager.df = self.original_df

        # Prompt the user to choose where to save the new database
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save New Database", "new_database.csv", "CSV Files (*.csv)", options=options)
        if fileName:
            if not fileName.endswith('.csv'):
                fileName += '.csv'
            self.original_df.to_csv(fileName, index=False)
            self.db_manager.df = self.original_df
            self.db_manager.db_path = fileName  # Ensure db_manager path is updated
            self.save_last_db_path(fileName)  # Confirm path saving
            self.update_table_view(self.original_df)
            self.statusBar().showMessage("New database created and saved.")
        else:
            # If the user cancels, go back without creating a file.
            self.statusBar().showMessage("New database creation canceled.") 

    # Method to update the view of the table to reflect data     
    def update_table_view(self, data):
        if not hasattr(self, 'table_view'):
            return  # Guard against being called before table_view is ready
        self.table_view.setModel(PandasModel(data))

     # Method for search functionality in the tableView
    def on_search(self, text):
        """Filter the table based on the search query."""
        try:
            if text:
                # Filter the DataFrame and reset the index to align with the view
                self.filtered_df = self.original_df[self.original_df.apply(lambda row: row.astype(str).str.contains(text, case=False, regex=False).any(), axis=1)].reset_index(drop=True)
            else:
                self.filtered_df = self.original_df.copy()
            self.update_table_view(self.filtered_df)
            matchCount = len(self.filtered_df.index)
            self.statusBar().showMessage(f"{matchCount} matches found")
        except re.error as e:
            QMessageBox.warning(self, "Search Error", f"An error occurred during the search: {e}")

    # Method to handle row selection and display the corresponding Expansion
    def onItemClicked(self, item):
        Label = item.text()
        if hasattr(self, 'filtered_df') and not self.filtered_df.empty:
            # Use the filtered dataframe to get the Expansion
            Expansion = self.filtered_df[self.filtered_df['Label'].str.lower() == Label.lower()]['Expansion'].iloc[0]
        else:
            # Fallback to the original dataframe if filtered_df is not set
            Expansion = self.original_df[self.original_df['Label'].str.lower() == Label.lower()]['Expansion'].iloc[0]
        self.ExpansionLabel.setText(f"Expansion: {Expansion}")

    # Method to add a new entry to the data
    def add_entry(self):
        """Add a new entry to the DataFrame."""
        # Ensure the DataFrame is initialized
        if self.original_df is None:
            self.new_database()  # Initialize the DataFrame if it hasn't been already
        new_row = {'Label': '', 'Expansion': '', 'Diagnosis': ''}
        self.original_df = pd.concat([self.original_df, pd.DataFrame([new_row])], ignore_index=True)
        self.update_table_view(self.original_df)
        self.statusBar().showMessage("Entry added. Ready to edit.")
 
    # Method to delete the selected entry/entries from the data
    def delete_entry(self):
        selectedRows = self.table_view.selectionModel().selectedRows()
        if not selectedRows:
            QMessageBox.information(self, "No Row Is Selected For Deletion", "No row selected for deletion.")
            return
        for index in sorted(selectedRows, reverse=True):
            self.original_df = self.original_df.drop(self.original_df.index[index.row()])
        self.original_df.reset_index(drop=True, inplace=True)
        self.update_table_view(self.original_df)

    # Method to save changes made to the data back to the file
    def save_changes(self):
        """Save the changes made to the DataFrame back to the CSV file."""
        
        try:
            self.original_df.to_csv(self.db_manager.db_path, index=False)
            
            QMessageBox.information(self, "Save Successful", "Changes were saved.")
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"An error occurred while saving the changes: {e}")

     # Method to open a custom editor for the selected cell
    def openCustomEditor(self, index):
        # Get the current value from the DataFrame
        if hasattr(self, 'filtered_df') and not self.filtered_df.empty:
            df = self.filtered_df
        else:
            df = self.original_df
        # Get the current value from the filtered/original DataFrame
        current_value = str(df.iloc[index.row(), index.column()])
        editor = CustomEditor(current_value, self)
        # Execute the dialog and check if the user pressed save
        if editor.exec_() == QDialog.Accepted:
            new_value = editor.getValue()
            # Update the DataFrame with the new value
            self.original_df.iloc[index.row(), index.column()] = new_value
            # Reflect changes in the view
            self.update_table_view(self.original_df)
    
    # Method to show the menu bar
    def showMenu(self):
        menu = QMenu()
        
        # Add actions to the menu

        # Add 'Add Entry' action to the menu
        addAction = QAction("Add Entry", self)
        addAction.triggered.connect(self.add_entry)
        menu.addAction(addAction)

        # Add 'Delete Entry' action to the menu
        deleteAction = QAction("Delete Entry", self)
        deleteAction.triggered.connect(self.delete_entry)
        menu.addAction(deleteAction)

        # Add 'Import CSV' action to the menu
        importAction = QAction("Import CSV", self)
        importAction.triggered.connect(self.import_csv)
        menu.addAction(importAction)

        # 'Export CSV' action to the menu
        exportAction = QAction("Export CSV", self)
        exportAction.triggered.connect(self.export_csv)
        menu.addAction(exportAction)

        # 'Save Changes' action to the menu
        saveAction = QAction("Save Changes", self)
        saveAction.triggered.connect(self.save_changes)
        menu.addAction(saveAction)

        searchAction = QAction("Search Label", self)
        searchAction.triggered.connect(self.showSearchPopup)
        menu.addAction(searchAction)

        # Add 'Text Expander Mode' action to the menu
        self.toggleAction = QAction("Text Expander Mode(Press 'esc' to Quit))", self)
        self.toggleAction.setCheckable(True)
        self.toggleAction.triggered.connect(self.toggleMonitoring)
        menu.addAction(self.toggleAction)
        

        #  Add 'Quit and Save' action to the menu
        quitSaveAction = QAction("Save and Quit", self)
        quitSaveAction.triggered.connect(self.quit_and_save)
        menu.addAction(quitSaveAction)

        # Show the menu below the menu button
        menuPos = self.menuButton.mapToGlobal(QPoint(0, self.menuButton.height()))
        menu.exec_(menuPos)
    
    # Method to import a CSV file into the dictionary list widget
    def import_csv(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            try:
                # Load the CSV file
                imported_df = pd.read_csv(fileName)
                self.original_df = self.standardize_column_names(imported_df)
                # Standardize column names
                if len(imported_df.columns) == 3:
                    imported_df.columns = ['Label', 'Expansion', 'Diagnosis']
                else:
                    QMessageBox.warning(self, "Error", "The imported file does not have the correct number of columns.")
                    return

                # Update the DataFrame and the view
                self.db_manager.df = self.original_df
                self.db_manager.db_path = fileName  # Ensure db_manager path is updated
                self.save_last_db_path(fileName)  # Confirm path saving
                self.update_table_view(self.original_df)

                self.statusBar().showMessage(f"Imported {fileName}")
            except Exception as e:
                QMessageBox.warning(self, "Import Error", f"An error occurred: {e}")

    # Method to export the dictionary list widget to a CSV file
    def export_csv(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            if not fileName.endswith('.csv'):
                fileName += '.csv'
            self.original_df.to_csv(fileName, index=False)
            self.statusBar().showMessage(f"Exported to {fileName}")

    # Method to standardize the column names of the DataFrame
    def quit_and_save(self):
        """Saves the changes and quits the application."""
        self.save_changes()  # Save changes to the DataFrame
        QMessageBox.information(self, "Quitting", "Closing your program now!")
        self.close()  # Close the application window
   

    def showSearchPopup(self):
        print("showSearchPopup called")
        if not hasattr(self, 'searchPopup'):
            self.searchPopup = SearchPopup(self.db_manager, self)  # Make sure this matches the name used in MainWindow
        self.searchPopup.show()
#NEW
    
    def toggleMonitoring(self):
        if self.toggleAction.isChecked():
            # Start or restart the keyboard listener
            if not self.keyboardListener.isRunning():
                self.keyboardListener.start()
            else:
                self.keyboardListener.terminate()  # Restart if already running
                self.keyboardListener.start()

            # Start or restart the clipboard monitor
            if not self.clipboardMonitor.isRunning():
                self.clipboardMonitor.start()
            else:
                self.clipboardMonitor.terminate()  # Restart if already running
                self.clipboardMonitor.start()

            # Display popup message
            QMessageBox.information(self, "Text Replacement is Enabled", "Text Replacement Is Running, press 'esc' to turn off toggle")
            
        else:
            # Stop both monitors
            if self.keyboardListener.isRunning():
                self.keyboardListener.terminate()

            if self.clipboardMonitor.isRunning():
                self.clipboardMonitor.terminate()

            
    def onExpansionCopied(self, Expansion):
        #  React to the Expansion being copied, e.g., display a notification
        print(f"Expansion copied to clipboard: {Expansion}")

    # Method to close Text Expander mode when the application is closed
    def closeEvent(self, event):
        # Ensure both monitors are stopped when the application closes
        if self.keyboardListener.isRunning():
            self.keyboardListener.terminate()
        if self.clipboardMonitor.isRunning():
            self.clipboardMonitor.terminate()
        super().closeEvent(event)

    # Method to handle key press events
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.toggleAction.isChecked():
            self.toggleAction.setChecked(False)
            self.toggleMonitoring()
        if event.key() == Qt.Key_Escape:  # Check if the 'esc' key was pressed
            self.handleEscapePress()

    # Method to handle escape key press
    def handleEscapePress(self):
        # Logic to disable monitoring when escape is pressed
        if self.toggleAction.isChecked():
            self.toggleAction.setChecked(False)
            self.toggleMonitoring()
            QMessageBox.information(self, "Text Replacement is Disabled", "Text Replacement Monitoring is now turned off.")
    
    # Method to standardize the column names of the DataFrame
    def standardize_column_names(self, df):
        standardized_columns = ['Label', 'Expansion', 'Diagnosis']
        # Check if the DataFrame has the same number of columns expected, otherwise raise an error
        if len(df.columns) == len(standardized_columns):
            df.columns = standardized_columns
        else:
            raise ValueError(f"The DataFrame does not have the expected number of columns. Found {len(df.columns)}, expected {len(standardized_columns)}.")
        return df

# `LineEditDelegate` class for handling editing of cells in the table view
class LineEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        # This method creates the editor widget. We'll use QLineEdit.
        editor = QLineEdit(parent)
        # Optional: Customize the QLineEdit editor if needed (e.g., set validators)
        return editor

    def setEditorData(self, editor, index):
        # This method sets the initial data inside the editor widget.
        value = index.model().data(index, Qt.EditRole)
        editor.setText(value)

    def setModelData(self, editor, model, index):
        # This method updates the model once editing is finished.
        value = editor.text()
        model.setData(index, value, Qt.EditRole)

# CustomEditor class for editing the cell data
class CustomEditor(QDialog):
    def __init__(self, value, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Edit')
        self.layout = QVBoxLayout(self)

        # Use QTextEdit for multi-line text editing
        self.textEdit = QTextEdit(self)
        self.textEdit.setText(value)
        self.textEdit.setMinimumSize(400, 100)  # Adjust size as needed
        # Increase the font size in QTextEdit
        self.textEdit.setStyleSheet("""
            QTextEdit {
                font-size: 18px; /* Adjust the size as needed */
                padding: 6px; /* Optional: for better text alignment */
            }
        """)
        self.layout.addWidget(self.textEdit)

        # Create a save button
        self.saveButton = QPushButton('Save', self)
        # Increase the font size in QPushButton
        self.saveButton.setStyleSheet("""
            QPushButton {
                font-size: 18px; /* Adjust the size as needed */
                padding: 6px; /* Optional: for better button alignment */
            }
        """)
        self.saveButton.clicked.connect(self.accept)
        self.layout.addWidget(self.saveButton)

        # Resize the dialog to accommodate the QTextEdit
        self.resize(1000, 400)  # Adjust size as needed

    def getValue(self):
        # Return the edited text from the QTextEdit
        return self.textEdit.toPlainText()

# SearchPopup class for the search popup

class SearchPopup(QDialog):
    
    # Constructor method for SearchPopup
    def __init__(self, db_manager, parent=None):
        super(SearchPopup, self).__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Search Label")
        self.setGeometry(100, 100, 700, 700)  # Make the window larger
        self.initUI()

    # Method to initialize the UI components of the SearchPopup
    def initUI(self):
        layout = QVBoxLayout(self)

        # Customize QLineEdit
        self.lineEdit = QLineEdit(self)
        self.lineEdit.setPlaceholderText("Type a Label...")
        self.lineEdit.setStyleSheet("""
            QLineEdit {
                font-size: 18px;
                padding: 6px;
                border: 1px solid gray;
                border-radius: 4px;
            }
        """)
        self.lineEdit.textChanged.connect(self.onTextChanged)
        layout.addWidget(self.lineEdit)

        # Customize QListWidget
        self.listWidget = QListWidget(self)
        self.listWidget.hide()  # Initially hide
        self.listWidget.setStyleSheet("""
            QListWidget {
                font-size: 15px;
            }
        """)
        self.listWidget.itemClicked.connect(self.onItemClicked)
        layout.addWidget(self.listWidget)

        # Add "Copy" button after the ExpansionLabel
        self.copyButton = QPushButton("Copy", self)
        self.copyButton.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                padding: 5px 10px;
                border: 2px solid gray;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.copyButton.clicked.connect(self.copyToClipboard)
        layout.addWidget(self.copyButton)

        # Customize QLabel for showing the Expansion
        self.ExpansionLabel = QLabel(self)
        self.ExpansionLabel.setText("Expansion will appear here...")
        self.ExpansionLabel.setWordWrap(True)  # Allow multi-line text
        self.ExpansionLabel.setStyleSheet("""
            QLabel {
                color: black; /* Change font color */
                font-size: 16px; /* Adjust font size as needed */
                padding: 10px; /* Add some padding for better readability */
            }
        """)
        layout.addWidget(self.ExpansionLabel)

         

        # Adjust layout spacing and margins for better UX
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

    # Method to handle text changed in the QLineEdit widget
    def onTextChanged(self, text):
        self.listWidget.clear()
        if text:
            self.listWidget.show()
            suggestions = self.db_manager.get_suggestions(text)
            self.listWidget.addItems(suggestions)
        else:
            self.listWidget.hide()
    
    # Method to handle item clicked in the QListWidget widget
    def onItemClicked(self, item):
        Label = item.text()
        # If filtered_df exists and is not empty, use it for accurate data retrieval
        if hasattr(self, 'filtered_df') and not self.filtered_df.empty:
            Expansion = self.filtered_df[self.filtered_df['Label'].str.lower() == Label.lower()]['Expansion'].iloc[0]
        else:
            # If no filtered_df exists, fall back to original dataframe
            Expansion = self.db_manager.get_Expansion(Label.lower())
        self.ExpansionLabel.setText(f"Expansion: {Expansion}")

        self.ExpansionLabel.setText(f"Expansion: {Expansion}")

    # Method to copy the Expansion to the clipboard
    def copyToClipboard(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.ExpansionLabel.text())
        QMessageBox.information(self, "Copied", "Expansion copied to clipboard!")

    # Method to show the search popup window
    def showSearchPopup(self):
        # Assuming 'self.databaseManager' can return the database or data structure you're using
        database = self.databaseManager.get_database()  # Ensure this method returns the data structure needed
        self.popup = SearchPopup(database)
        self.popup.show()

# Define a class ClipboardMonitor that inherits from QThread
class ClipboardMonitor(QThread):
    # Define a signal that will be emitted when a Expansion is copied
    ExpansionCopied = pyqtSignal(str)

    # The constructor for the class
    def __init__(self, db_manager):
        # Call the constructor of the parent class
        super().__init__()
        # Store the database manager that will be used to get Expansions
        self.db_manager = db_manager
        # A flag to indicate whether the thread should keep running
        self._running = True
        # Store the last content of the clipboard
        self._last_clipboard_content = ""

    # The main loop of the thread
    def run(self):
        # Keep running as long as the _running flag is True
        while self._running:
            # Get the current content of the clipboard
            current_clipboard_content = pyperclip.paste()
            # If the content of the clipboard has changed since the last check
            if current_clipboard_content != self._last_clipboard_content:
                # Update the stored last content of the clipboard
                self._last_clipboard_content = current_clipboard_content
                # Check if the new content is an Label that has a Expansion
                self.check_for_Label(current_clipboard_content)
            # Wait for half a second before the next check
            time.sleep(0.5)

    # Check if the given text is an Label that has a Expansion
    def check_for_Label(self, text):
        # Get the Expansion of the text from the database manager
        Expansion = self.db_manager.get_Expansion(text)
        # If a Expansion was found and it's not the placeholder for a missing Expansion
        if Expansion and Expansion != "Expansion not found":
            # Copy the Expansion to the clipboard
            pyperclip.copy(Expansion)
            # Emit a signal to indicate that a Expansion was copied
            self.ExpansionCopied.emit(Expansion)

    # Stop the thread
    def stop(self):
        # Set the _running flag to False, which will stop the main loop
        self._running = False

# Define a class KeyboardListener that inherits from QThread
class KeyboardListener(QThread):
    escapePressed = pyqtSignal()

    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        self._running = True
        self.current_word = ""  # Initialize current_word

    def on_key_pressed(self, e):
        if e.event_type == 'down':  # Act only on 'key down' events
            if e.name == 'esc':
                self._running = False
                self.escapePressed.emit()
                self.stop()  # Assuming you have a stop method to terminate the thread safely

            if e.name in ['shift', 'ctrl', 'alt', 'left shift', 'right shift', 'left ctrl', 'right ctrl', 'left alt', 'right alt', 'enter', 'tab', 'caps lock', 'up', 'down', 'left', 'right', 'home', 'end', 'page up', 'page down', 'insert', 'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f20', 'f21', 'f22', 'f23', 'f24', 'num lock', 'print screen', 'scroll lock', 'pause', 'menu', 'windows', 'command']:
                return  # Ignore modifier and special keys

            if e.name == 'space':
                if self.current_word:
                    self.on_space_pressed(e)
                self.current_word = ""
            elif e.name == 'backspace':
                # Remove the last character from current_word
                self.current_word = self.current_word[:-1]
            elif e.name.isalnum() or e.name in ['.', '-']:
                # Append character to current_word, considering case sensitivity based on your requirements
                self.current_word += e.name
            else:
                self.current_word = ""  # Reset current_word for non-valid characters
            print(f"Current word: {self.current_word}")  # Debugging line to monitor current_word

    def on_space_pressed(self, e):
        original_clipboard_content = pyperclip.paste()  # Save original clipboard content
        Expansion = self.db_manager.get_Expansion(self.current_word)
        
        if Expansion and Expansion != "Expansion not found":
            # Clear the Label
            backspaces_needed = len(self.current_word) + 1  # +1 for the space
            keyboard.write('\b' * backspaces_needed, delay=0.005)  # Adjust delay as needed
            
            # Type out the Expansion ensuring the entire string is processed
            for char in Expansion:
                keyboard.write(char, delay=0.005)  # Adjust delay to ensure reliability
            
            # Introduce a slight delay to ensure text is fully typed out before proceeding
            time.sleep(0.1)  # Adjust this delay as needed based on performance
            
        else:
            print("Expansion not found for:", self.current_word)

        # Restore the original clipboard content after a slight delay
        time.sleep(0.1)  # Additional delay to ensure clipboard restoration occurs after typing
        pyperclip.copy(original_clipboard_content)

        self.current_word = ""  # Reset current word for the next Label

    def run(self):
        print("KeyboardListener started")  # Confirm this message appears in your console
        self._running = True
        keyboard.on_press(self.on_key_pressed)
        while self._running:
            # This loop keeps the thread alive waiting for the 'esc' press event.
            time.sleep(0.1)
        keyboard.unhook(self.on_key_pressed)

    def stop(self):
        self._running = False
        keyboard.unhook_all()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())


#First Column name: Label
#Second column: Expansion
#Third column: Diagnosis