import sys
import subprocess

from textual.app import App
from textual.binding import Binding
from textual.widgets import Button, Input
from textual import events
from textual.pilot import Pilot

from rich.console import Console
from typing import Tuple, List

from typer_to_textual.command_options import CommandOptions
from typer_to_textual.homepage import HomePage
from typer_to_textual.show import Show


def maximize() -> None:
    result = subprocess.run(["xdotool", "getactivewindow"], capture_output=True)
    window_id = result.stdout.decode().strip()
    subprocess.run(["xdotool", "windowsize", window_id, "70%", "70%"])

    # Get the screen resolution
    res = subprocess.check_output("xrandr | grep '\*' | awk '{print $1}'", shell=True).decode().strip().split('x')
    screen_width = int(res[0])
    screen_height = int(res[1])

    # Calculate the window position to center it on the screen
    x_pos = int((screen_width - (screen_width * 0.7)) / 2)
    y_pos = int((screen_height - (screen_height * 0.7)) / 2)

    # Move the window to the calculated position
    subprocess.run(["xdotool", "windowmove", window_id, str(x_pos), str(y_pos)])

def homepage_output() -> Tuple[List[str], str]:

    if len(sys.argv) != 2:
        Console().print("[bold][red]Error[/red]: Pass only the name of application")
        sys.exit(1)

    application = sys.argv[1]
    maximize()

    try:
        result = subprocess.run([application, "--help"], capture_output=True)
        return result.stdout.decode().split('\n'), application
    except FileNotFoundError:
        Console().print("[bold][red]Error[/red]: The application is not found")
        sys.exit(1)


class Tui(App):

    def __init__(self) -> None:
        self.output, self.application = homepage_output()
        super().__init__()

    CSS_PATH = "style.css"

    BINDINGS = [
        Binding(key="escape", action="key_escape", description="exit"),
    ]

    def on_mount(self) -> None:
        self.install_screen(HomePage(self.output), name="homepage")
        self.push_screen("homepage")

    async def on_key(self, event: events.Key):
        if event.key == "up":
            pilot = Pilot(self)
            await pilot.press("shift+tab")
        if event.key == "down":
            pilot = Pilot(self)
            await pilot.press("tab")

    def action_key_escape(self) -> None:
        self.exit()

    def call_command(self, command: str) -> List[str]:

        maximize()
        result = subprocess.run([self.application, command, "--help"], capture_output=True)

        return result.stdout.decode().split('\n')

    def command_buttons(self):
        start_commands = False
        buttons = {}
        for index, line in enumerate(self.output, start=1):

            if "Commands" in line:
                start_commands = True
                continue

            if start_commands and any(word.isalpha() for word in line.split()):
                command = line.split(" ")
                words = []
                current_word = ""
                for item in command:
                    if item and item != '│':
                        current_word += " " + item
                    else:
                        words.append(current_word.strip())
                        current_word = ""

                words = list(filter(bool, words))
                buttons[words[0]] = words[1]

        return buttons

    """def check(self, screen: str, elements: str):
        
        for element in self.query(f"{screen}").last().query(f".{elements}"):
            key = element.query_one(".name").id
            input_type = ''
            tuple_types = []

            # Iterate over the static elements and extract the type information
            for index, static_element in enumerate(element.query("Static"), start=1):
                if index == 2 and static_element.name != "BOOLEAN":
                    tuple_types = static_element.name.split(" ")
                    if len(tuple_types) == 1:
                        if tuple_types[0] == "INTEGER":
                            input_type = "INTEGER"
                        elif tuple_types[0] == "FLOAT":
                            input_type = "FLOAT"
                        else:
                            input_type = "TEXT"
                    else:
                        input_type = "TUPLE"

            # Validate input values based on the input type
            if input_type == "INTEGER" or input_type == "FLOAT":
                for input_element in element.query(".input"):
                    try:
                        if input_element.value != "":
                            if input_type == "INTEGER":
                                int(input_element.value)
                            else:
                                float(input_element.value)
                        input_element.styles.border = ("blank", "red")
                    except ValueError:
                        almeno_uno = True
                        input_element.styles.border = ("tall", "red")

            elif input_type == "TUPLE":
                for index, input_element in enumerate(element.query(".input")):
                    expected_type = {
                        "INTEGER": int,
                        "TEXT": str,
                        "FLOAT": float
                    }.get(tuple_types[index], None)

                    try:
                        if input_element.value != "":
                            expected_type(input_element.value)
                        input_element.styles.border = ("blank", "red")
                    except ValueError:
                        almeno_uno = True
                        input_element.styles.border = ("tall", "red")

            if len(element.query(".input")) > 0:
                diversi = len(set(i.placeholder for i in element.query(".input"))) > 1
                if diversi:
                    for index, i in enumerate(element.query(".input"), start=1):
                        if i.value != '':
                            if index == 1:
                                command_data[key] = [i.value]
                            else:
                                command_data[key].append(i.value)
                else:
                    for index, i in enumerate(element.query(".input"), start=1):
                        if "--argument--" in key and i.value != '':
                            lista.append(i.value)
                        elif i.value != '':
                            lista.append(key)
                            lista.append(i.value)
            else:
                if str(element.query_one("Checkbox").value) == "True":
                    command_data[key] = "BOOL"
    """

    def on_button_pressed(self, event: Button.Pressed):

        values = self.command_buttons()
        buttons = values.keys()

        if event.button.id in buttons:

            description = values[event.button.id]
            if not self.is_screen_installed(event.button.id):
                result = self.call_command(event.button.id)
                self.install_screen(CommandOptions(result, event.button.id, description), name=event.button.id)
            self.push_screen(event.button.id)

        elif event.button.id.startswith("show-"):

            homepage_data = {}

            for element in self.query_one(HomePage).query():
                if element.name == "checkbox":
                    if str(element.value) == "True":
                        homepage_data[element.id] = "BOOL"
                elif element.name == "input":
                    if element.value != '':
                        homepage_data[element.id] = element.value

            command_data = {}
            lista = []
            almeno_uno = False

            for element in self.query(CommandOptions).last().query(".booklet-horizontal"):
                key = element.query_one(".name").id
                input_type = ''
                tuple_types = []

                # Iterate over the static elements and extract the type information
                for index, static_element in enumerate(element.query("Static"), start=1):
                    if index == 2 and static_element.name != "BOOLEAN":
                        tuple_types = static_element.name.split(" ")
                        if len(tuple_types) == 1:
                            if tuple_types[0] == "INTEGER":
                                input_type = "INTEGER"
                            elif tuple_types[0] == "FLOAT":
                                input_type = "FLOAT"
                            else:
                                input_type = "TEXT"
                        else:
                            input_type = "TUPLE"

                # Validate input values based on the input type
                if input_type == "INTEGER" or input_type == "FLOAT":
                    for input_element in element.query(".input"):
                        try:
                            if input_element.value != "":
                                if input_type == "INTEGER":
                                    int(input_element.value)
                                else:
                                    float(input_element.value)
                            input_element.styles.border = ("blank", "red")
                        except ValueError:
                            almeno_uno = True
                            input_element.styles.border = ("tall", "red")

                elif input_type == "TUPLE":
                    for index, input_element in enumerate(element.query(".input")):
                        expected_type = {
                            "INTEGER": int,
                            "TEXT": str,
                            "FLOAT": float
                        }.get(tuple_types[index], None)

                        try:
                            if input_element.value != "":
                                expected_type(input_element.value)
                            input_element.styles.border = ("blank", "red")
                        except ValueError:
                            almeno_uno = True
                            input_element.styles.border = ("tall", "red")

                if len(element.query(".input")) > 0:
                    diversi = len(set(i.placeholder for i in element.query(".input"))) > 1
                    if diversi:
                        for index, i in enumerate(element.query(".input"), start=1):
                            if i.value != '':
                                if index == 1:
                                    command_data[key] = [i.value]
                                else:
                                    command_data[key].append(i.value)
                    else:
                        for index, i in enumerate(element.query(".input"), start=1):
                            if "--argument--" in key and i.value != '':
                                lista.append(i.value)
                            elif i.value != '':
                                lista.append(key)
                                lista.append(i.value)
                else:
                    if str(element.query_one("Checkbox").value) == "True":
                        command_data[key] = "BOOL"

            command = event.button.id.replace("show-", "")

            if almeno_uno:
                return

            if not self.is_screen_installed(event.button.id):
                self.install_screen(Show(self.application, command, homepage_data, command_data, lista), name=event.button.id)
            self.push_screen(event.button.id)

        if event.button.id.startswith("one_more-"):
            index = event.button.id.split("-")[1]
            placeholder = self.query(CommandOptions).last().query_one(f"#container-{index} .name").id
            placeholder = placeholder.replace("--argument--", "").replace("--", "")
            input_element = Input(placeholder=f"{placeholder}....", classes="input")
            self.query(CommandOptions).last().query_one(f"#container-{index}").mount(input_element, before=3)

    async def action_pop_screen_n(self, screen):

        input_has_focus = any(i.has_focus for i in self.query("Input"))

        if input_has_focus:
            for i in self.query("Input"):
                if i.has_focus:
                    i.value = i.value + 'r'
                    pilot = Pilot(self)
                    await pilot.press("right")
                    break
        else:
            if screen == "show":
                self.uninstall_screen(self.pop_screen())
            else:
                self.pop_screen()


if __name__ == "__main__":
    Tui().run()
