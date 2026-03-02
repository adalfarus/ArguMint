# ArguMint
 A fresh new way to handle cli. 
 
This package is just maintained (EOL) as I have rewritten large parts of the package (2k new LOC) and plan to release them under the new name autocli. This could take a 1-2 months though as the old owner of the name seems unresponsive.

I have also updated it with the latest code from aplustools.package.autocli and applied a few patches and quality of life enhancements.

## How to use it
```python
from argumint import Argumint, ArgumentParsingError
from typing import Literal


def sorry(*args, **kwargs):
    print("This path does not have an endpoint, please use aps help to get help.")

def help_text():
    print("Build -> dir/file or help.")

def build_file(path: Literal["./main.py", "./file.py"] = "./main.py", num: int = 0):
    """
    build_file
    :param path: The path to the file that should be built.
    :param num:
    :return None:
    """
    print(f"Building file {path} ..., {num}")

from chronix import FlexTimer

timer = FlexTimer()

# Initialization
parser = Argumint(default_endpoint=sorry, arg_struct={
    'aps': {
        'build': {
            'file': {},
            'dir': {
                'main': {},
                'all': {}
            }
        },
        'help': {}
    }
})

# Add endpoints
parser.add_endpoint("aps.help", help_text)
parser.add_endpoint("aps.build.file", build_file)

# Testing
try:
    print("---- 1 ----")
    parser.parse_cli(["main.py", "help"], "native_light")
    print(timer.lap().to_readable())
    print("---- 2 ----")
    parser.parse_cli(["main.py", "build", "file", "./file.py", "--num=19"], "native_light")
    print(timer.lap().to_readable())
    print("---- 3 ----")
    parser.parse_cli(mode="native_light")
    print(timer.lap().to_readable())
    print("---- 4 ----")
    parser.parse_cli(["main.py", "build", "file", "./file.py", "--num", "=", "19"], "native_light")  # Error
    print(timer.lap().to_readable())
except ArgumentParsingError as e:
    print(f"There was an error while parsing '{e}'.")
timer.end()
```
