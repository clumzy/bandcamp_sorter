from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ListView, Static, ListItem, Label, ProgressBar
from textual.reactive import reactive
from textual import log
import threading
from ..ai.tagmytechno import *

class IAPanel(Vertical):
    files_init = ""
    playlist_init = ""
    sorted_results = {}
    activate_zone:Horizontal = Horizontal(
        Button(label="Analyze", id="analyze_button"),
        ProgressBar(id="analyze_progress"))
    divider = Static()
    ia_pane = Horizontal(
        ListView(id="playlist_list"),
        ListView(id="sound_list"))
    ia_pane.styles.height = "90%"

    def compose(self) ->ComposeResult:
        yield Vertical(
            self.activate_zone,
            self.divider,
            self.ia_pane)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "analyze_button":
            images = []
            files = get_files_list(location = self.files_init)
            self.activate_zone.get_child_by_id("analyze_progress").update(total = len(files), progress = 0)
            self.sorted_results = self._get_predictions(files)
            self.add_playlists(self.sorted_results.keys())

    def on_list_view_selected(self, message: ListView.Selected):
        if message.list_view.id == "playlist_list":
            self.add_tunes(str(message.item.get_child_by_type(Label).renderable))

    def add_tunes(self, genre):
        self.ia_pane.get_child_by_id("sound_list").clear()
        for t in self.sorted_results[genre]:
            tune_name = str(t).split('\\')[-1]
            self.ia_pane.get_child_by_id("sound_list").append(ListItem(Label(tune_name)))
            self.ia_pane.get_child_by_id("sound_list").refresh()

    def add_playlists(self, playlists:list):
        for p in playlists:
            self.ia_pane.get_child_by_id("playlist_list").append(ListItem(Label(p)))
            self.ia_pane.get_child_by_id("playlist_list").refresh()

    def _get_predictions(self, files):
        model = create_model("D:/George/Documents/Code/clumzy/bandcamp_sorter/mydigger/ai/tagmytechno/mdl.keras")
        images = []
        for image in get_images(files_list=files):
            self.activate_zone.get_child_by_id("analyze_progress").update(advance=1)
            images.append(image)
        results = get_predictions(model=model, images=images)
        return sort_results(files_list=files, results=results)
