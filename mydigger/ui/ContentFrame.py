from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import TabbedContent, Button, DirectoryTree, ContentSwitcher, Label, TabPane
from .FilesPanel import FilesPanel
from .IAPanel import IAPanel

class ContentFrame(TabbedContent):
    files_panel = FilesPanel(id="files_content")
    ia_panel = IAPanel(id="ia_content")
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Files", id="files_panel"):
                yield self.files_panel
            with TabPane("IA", id="ia_panel"):
                yield self.ia_panel