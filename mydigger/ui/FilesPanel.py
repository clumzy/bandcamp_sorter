from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, TabbedContent, Label, Static, DirectoryTree
from textual.reactive import reactive
from textual import log

class FilesPanel(Horizontal):
    
    def compose(self) ->ComposeResult:
        self.files_init = "D:/George"
        self.playlist_init = "D:/George/Documents/Code/clumzy/bandcamp_sorter"
        self.files_loc = ""
        self.playlist_loc = ""
        self.files_pane:Vertical = Vertical(
            Label("Select directory to scan :", id="files_label"),
            DirectoryTree(path=self.files_init, disabled=False, id="files_dir"),
            Button("Select the current directory", id="files_button"))
        self.files_pane.styles.width = "45%"
        self.divider = Static()
        self.divider.styles.width = "5%"
        self.playlist_pane = Vertical(
            Label("Select directory to save playlists :", id="playlist_label"),
            DirectoryTree(path=self.playlist_init, disabled=False, id="playlist_dir"),
            Button("Select the current directory", id="playlist_button"))
        self.playlist_pane.styles.width = "45%"
        yield Horizontal(
            self.files_pane,
            self.divider,
            self.playlist_pane)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "files_button":
            self.files_pane.get_child_by_id("files_dir").disabled = True
        elif event.button.id == "playlist_button":
            self.playlist_pane.get_child_by_id("playlist_dir").disabled = True
        if self.files_pane.get_child_by_id("files_dir").disabled & self.playlist_pane.get_child_by_id("playlist_dir").disabled:
            self.parent.parent.parent.active = "ia_panel"
            self.parent.parent.parent.active_pane.get_child_by_id("ia_content").files_init = self.files_loc
            self.parent.parent.parent.active_pane.get_child_by_id("ia_content").playlist_init = self.playlist_loc
    
    def on_directory_tree_directory_selected(self, message: DirectoryTree.DirectorySelected)  -> None:
        if message.control.id=="files_dir":
            self.files_loc = str(message.path)
        elif message.control.id=="playlist_dir":
            self.playlist_loc = str(message.path)