from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ListView, Static, ListItem, Label, ProgressBar
from textual import log
import vlc
import threading
from ..ai.tagmytechno import *
from typing import List, Dict, Any
from os import startfile

class IAPanel(Vertical):
    """
    A panel for interacting with the AI analysis features.
    
    This class provides a UI component for analyzing audio files,
    displaying playlists, and playing tunes based on AI predictions.
    """

    def compose(self) -> ComposeResult:
        """
        Composes the layout of the IAPanel.
        
        Initializes the panel's components including buttons, progress bars,
        and lists for displaying playlists and sound files.
        
        Returns:
            ComposeResult: The composed layout of the IAPanel.
        """
        self.vlc_player = None
        self.vlc_thread = None
        self.playing:bool = False
        self.files_init = ""
        self.playlist_init = ""
        self.sorted_results = {}
        self.activate_zone:Horizontal = Horizontal(
            Button(label="Analyze", id="analyze_button"),
            ProgressBar(id="analyze_progress"))
        self.divider = Static()
        self.ia_pane = Horizontal(
            ListView(id="playlist_list"),
            ListView(id="sound_list"))
        self.ia_pane.styles.height = "90%"
        yield Vertical(
            self.activate_zone,
            self.divider,
            self.ia_pane)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handles button press events.
        
        When the analyze button is pressed, initiates the process of analyzing
        audio files and updates the UI accordingly.
        """
        if event.button.id == "analyze_button":
            files = get_files_list(location = self.files_init)
            self.activate_zone.get_child_by_id("analyze_progress").update(total = len(files), progress = 0)
            self.sorted_results = self._get_predictions(files)
            self.add_playlists(self.sorted_results.keys())

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        """
        Handles selection events from the playlist and sound list views.
        
        Adds selected tunes to the sound list or plays a sound file when a
        tune is selected from the sound list using VLC.
        """
        if message.list_view.id == "playlist_list":
            self.add_tunes(str(message.item.get_child_by_type(Label).renderable))
        elif message.list_view.id == "sound_list":
            # Get the file location of the selected tune

            file_path = str(message.item.get_child_by_type(TuneItem).file_loc).replace("\\", "/")
            # Define a function to play the audio in the background using VLC
            startfile(file_path)

    def add_tunes(self, genre: str) -> None:
        """
        Adds tunes to the sound list view based on the selected genre.
        
        Args:
            genre (str): The genre of tunes to display.
        """
        self.ia_pane.get_child_by_id("sound_list").clear()
        for t in self.sorted_results[genre]:
            tune_name = str(t).split('\\')[-1]
            self.ia_pane.get_child_by_id("sound_list").append(ListItem(TuneItem(tune_name, str(t))))
            self.ia_pane.get_child_by_id("sound_list").refresh()

    def add_playlists(self, playlists: List[str]) -> None:
        """
        Populates the playlist list view with the given playlists.
        
        Args:
            playlists (List[str]): A list of playlist names to display.
        """
        for p in playlists:
            self.ia_pane.get_child_by_id("playlist_list").append(ListItem(Label(p)))
            self.ia_pane.get_child_by_id("playlist_list").refresh()

    def _get_predictions(self, files: List[str]) -> Dict[str, Any]:
        """
        Retrieves AI predictions for the given audio files.
        
        Args:
            files (List[str]): A list of file paths to analyze.
            
        Returns:
            Dict[str, Any]: A dictionary mapping genres to their corresponding
                            tunes based on AI predictions.
        """
        model = create_model("D:/George/Documents/Code/clumzy/bandcamp_sorter/mydigger/ai/tagmytechno/mdl.keras")
        images = []
        for image in get_images(files_list=files):
            self.activate_zone.get_child_by_id("analyze_progress").update(advance=1)
            images.append(image)
        results = get_predictions(model=model, images=images, threshold=0.98)
        return sort_results(files_list=files, results=results)

class TuneItem(Label):
    """
    Represents a tune item in the UI.
    
    A custom widget for displaying a tune in the sound list view, including
    the tune's name and file location.
    """

    def __init__(self, label: str, file_loc: str) -> None:
        """
        Initializes a new instance of the TuneItem class.
        
        Args:
            label (str): The name of the tune.
            file_loc (str): The file location of the tune.
        """
        super().__init__()
        self.label = label
        self.file_loc = file_loc

    def compose(self) -> ComposeResult:
        yield Label(self.label)
