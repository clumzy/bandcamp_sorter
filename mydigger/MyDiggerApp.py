from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Header, Footer, Button

from .ui import ContentFrame

class MyDiggerApp(App):
    """DJing, made easy."""
    _content_frame = ContentFrame(id="content_frame")
    def compose(self) -> ComposeResult:
        """Create Child Widgets for the app."""
        yield Header()
        yield Footer()
        yield self._content_frame