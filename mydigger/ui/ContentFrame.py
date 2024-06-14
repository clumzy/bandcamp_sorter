from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import TabbedContent, Button, DirectoryTree, ContentSwitcher, Label, TabPane
from .BandcampPanel import BandcampPanel

class ContentFrame(TabbedContent):
    bandcamp_panel = BandcampPanel()
    slsk_panel = Horizontal(
        Label("SLSK"),
        Label("Default"))
    ia_panel = Horizontal(
        Label("IA"),
        Label("Default"))
    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Bandcamp", id="bc_panel"):
                yield self.bandcamp_panel
            with TabPane("SLSK", id="sk_panel"):
                yield self.slsk_panel
            with TabPane("IA", id="ia_panel"):
                yield self.ia_panel