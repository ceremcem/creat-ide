import sys
import json
import os
import subprocess # To launch applications
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QSplitter, QLabel, QFrame, QMenuBar,
                             QAction, QInputDialog, QFileDialog, QMessageBox,
                             QDialog, QLineEdit, QDialogButtonBox, QCompleter,
                             QListView, QPushButton)
from PyQt5.QtGui import QPainter, QColor, QCursor, QPolygon
from PyQt5.QtCore import Qt, QRect, QPoint, QDir, QTimer, QStringListModel

# --- Configuration ---
# Directory to save workspaces relative to the script location
WORKSPACE_DIR = "workspaces"
# Minimum drag distance to trigger a split
SPLIT_THRESHOLD = 10 # pixels
# List of directories to search for executables for autocompletion
EXEC_PATHS = ['/usr/bin', '/bin', '/usr/local/bin', '/usr/sbin', '/sbin']

# --- Helper Functions ---
def clear_layout(layout):
    """Recursively remove and delete all items and widgets from a layout."""
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            else:
                clear_layout(item.layout()) # Clear nested layouts

def get_executable_list():
    """Generates a list of executable files from common system paths."""
    executables = set()
    for path in EXEC_PATHS:
        if os.path.isdir(path):
            try:
                for filename in os.listdir(path):
                    full_path = os.path.join(path, filename)
                    # Check if it's a file and is executable
                    if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                        executables.add(filename)
            except OSError:
                # Ignore directories we don't have permission to read
                continue
    # Add some common GUI apps explicitly in case they are not in standard paths or for aliases
    common_gui_apps = ["firefox", "gimp", "inkscape", "libreoffice", "vlc",
                       "xterm", "gnome-terminal", "konsole", "nautilus",
                       "dolphin", "gedit", "kate", "code", "subl", "chromium-browser"]
    executables.update(common_gui_apps)
    return sorted(list(executables))

# --- Application Launcher Dialog ---
class AppLauncherDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Launch Application")
        self.setGeometry(200, 200, 400, 150) # x, y, width, height

        layout = QVBoxLayout(self)

        self.app_name_input = QLineEdit(self)
        self.app_name_input.setPlaceholderText("Enter application name...")
        layout.addWidget(self.app_name_input)

        # Setup autocompletion
        self.executable_list = get_executable_list()
        self.completer_model = QStringListModel(self.executable_list)
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains) # Match anywhere in the name
        self.app_name_input.setCompleter(self.completer)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def get_app_name(self):
        """Returns the entered application name."""
        return self.app_name_input.text().strip()

# --- Pane Options Dialog ---
class PaneOptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pane Options")
        self.setGeometry(300, 300, 200, 100) # x, y, width, height

        layout = QVBoxLayout(self)

        self.launch_button = QPushButton("Launch Application", self)
        self.close_button = QPushButton("Close Pane", self)
        self.cancel_button = QPushButton("Cancel", self)

        layout.addWidget(self.launch_button)
        layout.addWidget(self.close_button)
        layout.addWidget(self.cancel_button)

        self.launch_button.clicked.connect(self.on_launch_clicked)
        self.close_button.clicked.connect(self.on_close_clicked)
        self.cancel_button.clicked.connect(self.reject) # Reject the dialog on Cancel

        self.setLayout(layout)

        self._result = None # To store the chosen action and data

    def on_launch_clicked(self):
        """Handles the 'Launch Application' button click."""
        # Open the AppLauncherDialog
        app_dialog = AppLauncherDialog(self)
        if app_dialog.exec_() == QDialog.Accepted:
            app_name = app_dialog.get_app_name()
            if app_name:
                self._result = {"action": "launch", "app_name": app_name}
                self.accept() # Accept this dialog after getting app name
        # If AppLauncherDialog is rejected, this dialog remains open

    def on_close_clicked(self):
        """Handles the 'Close Pane' button click."""
        self._result = {"action": "close"}
        self.accept() # Accept this dialog

    def get_result(self):
        """Returns the chosen action and associated data."""
        return self._result


# A simple widget to put inside the panes
class ContentWidget(QWidget):
    def __init__(self, content_type="default", app_name=None, color=Qt.blue, parent=None):
        super().__init__(parent)
        self.content_type = content_type # "default" or "app"
        self.app_name = app_name
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), color)
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.update_label()

    def update_label(self):
        """Updates the label text based on content type."""
        if self.content_type == "app" and self.app_name:
            self.label.setText(f"Launching: {self.app_name}")
        else:
            self.label.setText("Content Pane") # Default text

    def launch_app(self):
        """Launches the application specified by app_name."""
        if self.content_type == "app" and self.app_name:
            print(f"Attempting to launch: {self.app_name}")
            try:
                # Launch the application in the background
                # Use subprocess.Popen for non-blocking launch
                # shell=True can be risky, but simplifies launching apps with args/paths
                # Consider using a more robust method for production
                subprocess.Popen(self.app_name, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.label.setText(f"Running: {self.app_name}") # Update label on successful launch attempt
            except FileNotFoundError:
                self.label.setText(f"Error: App '{self.app_name}' not found!")
                print(f"Error: Application '{self.app_name}' not found.")
            except Exception as e:
                self.label.setText(f"Error launching: {self.app_name}\n{e}")
                print(f"Error launching application '{self.app_name}': {e}")


# Custom widget that represents a pane and handles splitting
class SplitPaneWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Use a frame to give it a visible border
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setLineWidth(1)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # Remove margins for cleaner splitting
        self.layout.setSpacing(0) # Remove spacing between widgets

        # Initially, this pane contains a default ContentWidget
        self.content_widget = ContentWidget(content_type="default", color=Qt.blue)
        self.layout.addWidget(self.content_widget)

        self.is_split = False
        self.split_orientation = None # Qt.Horizontal or Qt.Vertical
        self.split_handle_size = 15 # Size of the corner handle area
        self.dragging_handle = False
        self.drag_start_pos = QPoint()
        self.current_drag_pos = QPoint() # Store current drag position for visual feedback
        self.split_threshold = SPLIT_THRESHOLD # Minimum drag distance to trigger a split

        # Set mouse tracking to detect hover over the handle
        self.setMouseTracking(True)

    # Override paintEvent to draw the split handle and potentially the drag line
    def paintEvent(self, event):
        super().paintEvent(event) # Draw the frame and background first

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.is_split:
            # Draw the filled red triangle handle
            painter.setBrush(QColor(255, 0, 0)) # Red color for the handle
            painter.setPen(Qt.NoPen) # No border for the filled triangle
            points = [
                QPoint(self.width(), self.height() - self.split_handle_size),
                QPoint(self.width(), self.height()),
                QPoint(self.width() - self.split_handle_size, self.height())
            ]
            painter.drawPolygon(QPolygon(points)) # Use QPolygon

        # Draw a line indicating the potential split location while dragging
        if self.dragging_handle and not self.is_split:
            painter.setPen(QColor(0, 0, 255)) # Blue color for the drag line
            delta = self.current_drag_pos - self.drag_start_pos
            # Determine potential split orientation based on current drag
            if abs(delta.x()) > abs(delta.y()):
                # Horizontal split preview
                split_x = self.width() - (self.drag_start_pos.x() - self.current_drag_pos.x())
                split_x = max(0, min(split_x, self.width())) # Clamp within bounds
                painter.drawLine(split_x, 0, split_x, self.height())
            else:
                # Vertical split preview
                split_y = self.height() - (self.drag_start_pos.y() - self.current_drag_pos.y())
                split_y = max(0, min(split_y, self.height())) # Clamp within bounds
                painter.drawLine(0, split_y, self.width(), split_y)


    # Helper to get the rectangle of the split handle area
    def get_handle_rect(self):
        return QRect(self.width() - self.split_handle_size,
                     self.height() - self.split_handle_size,
                     self.split_handle_size,
                     self.split_handle_size)

    # Override mousePressEvent to start dragging if on the handle
    def mousePressEvent(self, event):
        if not self.is_split and self.get_handle_rect().contains(event.pos()):
            if event.button() == Qt.LeftButton:
                self.dragging_handle = True
                self.drag_start_pos = event.pos()
                self.current_drag_pos = event.pos() # Initialize current drag pos
                self.setCursor(Qt.CrossCursor) # Change cursor while dragging
                # Grab mouse to ensure we receive move events even if cursor leaves widget
                self.grabMouse()
                self.update() # Request repaint to draw drag line
        else:
            super().mousePressEvent(event) # Pass event up if not on handle

    # Override mouseMoveEvent to update drag position and trigger split
    def mouseMoveEvent(self, event):
        if self.dragging_handle:
            self.current_drag_pos = event.pos()
            delta = self.current_drag_pos - self.drag_start_pos

            # Check if drag exceeds the threshold to trigger a split
            if not self.is_split and (abs(delta.x()) > self.split_threshold or abs(delta.y()) > self.split_threshold):
                 if abs(delta.x()) > abs(delta.y()):
                    # Horizontal split
                    self.split(Qt.Horizontal)
                 else:
                    # Vertical split
                    self.split(Qt.Vertical)

                 # After splitting, stop the drag operation
                 self.dragging_handle = False
                 self.releaseMouse()
                 self.unsetCursor()
                 self.update() # Repaint to remove the drag line preview

            # Change cursor based on dominant drag direction while still dragging
            if self.dragging_handle: # Check again in case split just happened
                if abs(delta.x()) > abs(delta.y()):
                    self.setCursor(Qt.SplitHCursor) # Horizontal resize cursor
                else:
                    self.setCursor(Qt.SplitVCursor) # Vertical resize cursor

            self.update() # Request repaint to update drag line position

        elif not self.is_split and self.get_handle_rect().contains(event.pos()):
             self.setCursor(Qt.CrossCursor) # Show cross cursor on hover
        else:
            self.unsetCursor() # Revert to default cursor
            super().mouseMoveEvent(event) # Pass event up if not dragging or hovering handle

    # Override mouseReleaseEvent to stop dragging or trigger click action
    def mouseReleaseEvent(self, event):
        if self.dragging_handle:
            self.dragging_handle = False
            self.releaseMouse()
            self.unsetCursor()
            self.update() # Repaint to remove the drag line preview

            # Check if it was a click (drag distance below threshold)
            total_delta = event.pos() - self.drag_start_pos
            if not self.is_split and abs(total_delta.x()) < self.split_threshold and abs(total_delta.y()) < self.split_threshold:
                # It was a click on the handle, open the pane options dialog
                self.open_pane_options()

        super().mouseReleaseEvent(event) # Pass event up

    # Method to perform the actual split
    def split(self, orientation):
        if self.is_split:
            return # Already split

        # Remove the current content widget
        self.layout.removeWidget(self.content_widget)
        self.content_widget.deleteLater() # Delete the old widget

        # Create a new splitter
        splitter = QSplitter(orientation)
        self.split_orientation = orientation

        # Create two new SplitPaneWidgets and add them to the splitter
        pane1 = SplitPaneWidget()
        pane2 = SplitPaneWidget()

        splitter.addWidget(pane1)
        splitter.addWidget(pane2)

        # Add the splitter to this widget's layout
        self.layout.addWidget(splitter)

        self.is_split = True

        # Optional: Set initial sizes for the splitter children
        # This helps distribute space evenly on split
        if orientation == Qt.Horizontal:
             splitter.setSizes([self.width() // 2, self.width() // 2])
        else: # Vertical
             splitter.setSizes([self.height() // 2, self.height() // 2])

    def open_pane_options(self):
        """Opens the pane options dialog for this pane."""
        dialog = PaneOptionsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_result()
            if result and result["action"] == "launch":
                app_name = result.get("app_name")
                if app_name:
                    self.set_pane_content(content_type="app", app_name=app_name)
            elif result and result["action"] == "close":
                self.close_pane()


    def set_pane_content(self, content_type="default", app_name=None):
        """Sets the content of this pane."""
        if self.is_split:
             print("Cannot set content on a split pane.")
             return

        # Clear existing content
        if self.content_widget:
            self.layout.removeWidget(self.content_widget)
            self.content_widget.deleteLater()
            self.content_widget = None

        # Create and add new content widget
        if content_type == "app" and app_name:
            self.content_widget = ContentWidget(content_type="app", app_name=app_name, color=Qt.lightGray) # Different color for app pane
            self.layout.addWidget(self.content_widget)
            self.content_widget.launch_app() # Attempt to launch the app
        else: # Default content
            self.content_widget = ContentWidget(content_type="default", color=Qt.blue)
            self.layout.addWidget(self.content_widget)

        self.update() # Repaint the widget

    def close_pane(self):
        """Closes this pane by removing it from its parent layout/splitter."""
        parent_widget = self.parentWidget()
        if isinstance(parent_widget, QSplitter):
            # If the parent is a splitter, remove self from it
            print(f"Closing pane: {self}")
            # Simply delete the widget. The QSplitter will handle the rest.
            self.deleteLater()
        elif isinstance(parent_widget, QWidget) and parent_widget.layout() == self.layout().parentWidget():
             # This is likely the root pane within the main window's layout
             print("Cannot close the root pane directly.")
             QMessageBox.warning(self, "Cannot Close", "Cannot close the main root pane.")
        else:
             print(f"Cannot close pane with parent type: {type(parent_widget)}")
             # Handle other parent types if necessary


    # --- Workspace Saving/Loading Methods ---

    def get_state(self):
        """Recursively gets the state of this pane and its children."""
        if not self.is_split:
            # This is a content pane
            state = {
                "type": "pane",
                "content": self.content_widget.content_type if self.content_widget else "default",
                "app_name": self.content_widget.app_name if self.content_widget and self.content_widget.content_type == "app" else None
            }
            return state
        else:
            # This is a split pane
            state = {
                "type": "split",
                "orientation": "horizontal" if self.split_orientation == Qt.Horizontal else "vertical",
                # Get sizes from the QSplitter if it exists
                "sizes": self.layout.itemAt(0).widget().sizes() if self.layout.count() > 0 and isinstance(self.layout.itemAt(0).widget(), QSplitter) else [],
                "children": []
            }
            # Ensure the item is a QSplitter before iterating
            if self.layout.count() > 0 and isinstance(self.layout.itemAt(0).widget(), QSplitter):
                splitter = self.layout.itemAt(0).widget()
                for i in range(splitter.count()):
                    child_widget = splitter.widget(i)
                    if isinstance(child_widget, SplitPaneWidget):
                         state["children"].append(child_widget.get_state())
                    # Add handling for other widget types if needed in the future
            return state

    @staticmethod
    def create_from_state(state):
        """Recursively creates a SplitPaneWidget (or splitter) from a state dictionary."""
        if state["type"] == "pane":
            # Create a simple pane with content
            new_pane = SplitPaneWidget()
            content_type = state.get("content", "default")
            app_name = state.get("app_name")
            new_pane.set_pane_content(content_type=content_type, app_name=app_name)
            return new_pane
        elif state["type"] == "split":
            # Create a split pane with a splitter and children
            orientation = Qt.Horizontal if state["orientation"] == "horizontal" else Qt.Vertical
            splitter = QSplitter(orientation)

            children_states = state.get("children", [])
            for child_state in children_states:
                child_widget = SplitPaneWidget.create_from_state(child_state)
                if child_widget: # Ensure child widget was created successfully
                     splitter.addWidget(child_widget)

            # Set sizes after adding all children
            sizes = state.get("sizes", [])
            if sizes and len(sizes) == splitter.count():
                 splitter.setSizes(sizes)
            else:
                 # Fallback to distributing space evenly if sizes are missing or don't match
                 # Only set sizes if there are children in the splitter
                 if splitter.count() > 0:
                     splitter.setSizes([1] * splitter.count())


            # Create a parent SplitPaneWidget to hold the splitter
            parent_pane = SplitPaneWidget()
            clear_layout(parent_pane.layout) # Clear the initial content
            parent_pane.layout.addWidget(splitter)
            parent_pane.is_split = True
            parent_pane.split_orientation = orientation

            return parent_pane
        return None # Should not happen with valid state

# Main application window
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PyQt Split Pane Example (Blender Style) with Workspaces and App Launcher")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Remove margins
        self.main_layout.setSpacing(0) # Remove spacing

        # Start with a single SplitPaneWidget
        self.root_pane = SplitPaneWidget()
        self.main_layout.addWidget(self.root_pane)

        self.create_menus()
        self.ensure_workspace_dir_exists()
        self.update_load_menu()

    def create_menus(self):
        """Creates the menu bar and workspace menu."""
        menu_bar = self.menuBar()
        workspaces_menu = menu_bar.addMenu("&Workspaces")

        # Save action
        save_action = QAction("&Save Current Workspace...", self)
        save_action.triggered.connect(self.save_workspace)
        workspaces_menu.addAction(save_action)

        # Load submenu
        self.load_menu = workspaces_menu.addMenu("&Load Workspace")

        # Add a separator
        workspaces_menu.addSeparator()

        # Exit action
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        workspaces_menu.addAction(exit_action)


    def ensure_workspace_dir_exists(self):
        """Ensures the directory for saving workspaces exists."""
        # Get the directory of the currently running script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.workspace_path = os.path.join(script_dir, WORKSPACE_DIR)
        if not os.path.exists(self.workspace_path):
            try:
                os.makedirs(self.workspace_path)
                print(f"Created workspace directory: {self.workspace_path}")
            except OSError as e:
                print(f"Error creating workspace directory {self.workspace_path}: {e}")
                # Handle error appropriately, maybe disable save/load

    def get_workspace_file_path(self, workspace_name):
        """Gets the full path for a workspace file."""
        # Sanitize the name to be filesystem-friendly
        safe_name = "".join(c for c in workspace_name if c.isalnum() or c in (' ', '.', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        if not safe_name:
             safe_name = "untitled_workspace"
        return os.path.join(self.workspace_path, f"{safe_name}.json")


    def save_workspace(self):
        """Saves the current pane arrangement as a workspace."""
        workspace_name, ok = QInputDialog.getText(self, "Save Workspace", "Enter workspace name:")
        if ok and workspace_name:
            file_path = self.get_workspace_file_path(workspace_name)

            try:
                # Get the state of the root pane
                current_state = self.root_pane.get_state()

                # Save the state to a JSON file
                with open(file_path, 'w') as f:
                    json.dump(current_state, f, indent=4)

                print(f"Workspace '{workspace_name}' saved to {file_path}")
                QMessageBox.information(self, "Success", f"Workspace '{workspace_name}' saved successfully!")
                self.update_load_menu() # Update the load menu after saving
            except Exception as e:
                print(f"Error saving workspace: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save workspace '{workspace_name}': {e}")


    def load_workspace(self, file_path):
        """Loads a workspace arrangement from a file."""
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "Warning", f"Workspace file not found: {file_path}")
            self.update_load_menu() # Refresh menu in case file was deleted
            return

        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)

            # Clear the current layout
            clear_layout(self.main_layout)
            # Ensure the old root pane is properly deleted
            if self.main_layout.count() == 0:
                 self.root_pane = None # Dereference the old root pane

            # Create the new pane structure from the loaded state
            self.root_pane = SplitPaneWidget.create_from_state(state_data)
            if self.root_pane:
                self.main_layout.addWidget(self.root_pane)
                print(f"Workspace loaded from {file_path}")
                # QMessageBox.information(self, "Success", f"Workspace loaded successfully!")
            else:
                raise ValueError("Failed to create pane from state data.")

        except json.JSONDecodeError:
            print(f"Error loading workspace: Invalid JSON in {file_path}")
            QMessageBox.critical(self, "Error", f"Failed to load workspace: Invalid file format for {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error loading workspace: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load workspace from {os.path.basename(file_path)}: {e}")


    def update_load_menu(self):
        """Clears and repopulates the Load Workspace submenu."""
        self.load_menu.clear() # Remove existing actions

        if not os.path.exists(self.workspace_path):
             # Directory doesn't exist, cannot load
             no_workspaces_action = QAction("No workspaces found", self)
             no_workspaces_action.setEnabled(False)
             self.load_menu.addAction(no_workspaces_action)
             return

        workspaces = []
        try:
            for filename in os.listdir(self.workspace_path):
                if filename.endswith(".json"):
                    workspace_name = os.path.splitext(filename)[0].replace('_', ' ') # Convert filename back to display name
                    file_path = os.path.join(self.workspace_path, filename)
                    workspaces.append((workspace_name, file_path))
        except OSError as e:
            print(f"Error listing workspaces: {e}")
            no_workspaces_action = QAction(f"Error listing workspaces: {e}", self)
            no_workspaces_action.setEnabled(False)
            self.load_menu.addAction(no_workspaces_action)
            return


        if not workspaces:
            no_workspaces_action = QAction("No workspaces found", self)
            no_workspaces_action.setEnabled(False)
            self.load_menu.addAction(no_workspaces_action)
        else:
            # Sort workspaces alphabetically
            workspaces.sort()
            for name, file_path in workspaces:
                action = QAction(name, self)
                # Use a lambda to pass the file_path to the load_workspace method
                action.triggered.connect(lambda checked, fp=file_path: self.load_workspace(fp))
                self.load_menu.addAction(action)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
