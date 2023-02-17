import sys
import subprocess

from typing import List, Tuple

from rich.console import Console

from tui import Tui


def main_output() -> Tuple[List[str], str]:
    if len(sys.argv) != 2:
        Console().print("pass exactly two argument!!!", style="bold yellow")
        exit()

    application = sys.argv[1]

    result = subprocess.run(
        [application, "--help"],
        capture_output=True,
    )
    return result.stdout.decode().split('\n'), application


def process_commands():
    output, app = main_output()
    start_commands = False
    commands = []
    for index, line in enumerate(output, start=1):

        if "Commands" in line:
            start_commands = True

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
            commands.append(words)

    for command in commands:
        print(commands[0])


def process_data():
    output, app = main_output()
    start_options = False
    data = {}
    for index, line in enumerate(output, start=1):

        if "Options" in line:
            start_options = True
            continue

        if "Commands" in line:
            start_options = False

        if start_options and any(word.isalpha() for word in line.split()):
            items = line.split(" ")
            words = []
            current_word = ""
            for option in items:
                if option and option != '│' and option != '*':
                    current_word += " " + option
                else:
                    words.append(current_word.strip())
                    current_word = ""

            words = list(filter(bool, words))
            if len(words) == 2:
                words.insert(1, "BOOLEAN")
            if words:
                words[0] = words[0].replace('--', '')
                if words[0] == "help":
                    continue
                data[words[0]] = [words[1], words[2]]

    for k, v in data.items():
        print(f"{v[1]}")


if __name__ == "__main__":
   process_commands()
