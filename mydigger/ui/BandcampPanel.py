from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import ListView, ListItem, Label, Static
from textual.reactive import reactive

class BandcampPanel(Horizontal):
    mails = []
    bdd = []
    for i in range(1, 100):
        mails.append(ListItem(Label(f"Mail {i}")))
        bdd.append(ListItem(Label(f"BDD {i}")))
    mail_pane = ListView(*mails)
    mail_pane.styles.width = "45%"
    divider = Static()
    divider.styles.width = "10%"
    bdd_pane = ListView(*bdd)
    bdd_pane.styles.width = "45%"

    def compose(self) ->ComposeResult:
        yield Horizontal(
            self.mail_pane,
            self.divider,
            self.bdd_pane)