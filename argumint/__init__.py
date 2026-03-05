"""TBA"""
from warnings import deprecated
from functools import reduce
from operator import or_
import argparse
import warnings
import sys

# Standard typing imports for aps
import typing_extensions as _te
import collections.abc as _a
import typing as _ty

if _ty.TYPE_CHECKING:
    import _typeshed as _tsh
import types as _ts

__version__ = "2.0.1"
__all__ = ["NoDefault", "analyze_function", "Endpoint", "ArgumentParsingError", "Interface"]


class NoDefault:
    def __repr__(self) -> str:
        return "<NoDefault Object>"


def analyze_function(function: _a.Callable) -> dict[str, list[_ty.Any] | str | None]:
    """
    Analyzes a given function's signature and docstring, returning a structured summary of its
    arguments, including default values, types, keyword-only flags, documentation hints, and
    choices for `Literal`-type arguments. Also extracts information on `*args`, `**kwargs`,
    and the return type.

    Args:
        function (types.FunctionType): The function to analyze.

    Returns:
        dict: A dictionary containing the following keys:
            - "name" (str): The name of the function.
            - "doc" (str): The function's docstring.
            - "arguments" (List[Dict[str, Union[str, None]]]): Details of each argument:
                - "name" (str): The argument's name.
                - "default" (Any or None): The default value, if provided.
                - "choices" (List[Any] or []): Options for `Literal` type hints, if applicable.
                - "type" (Any or None): The argument's type hint.
                - "doc_help" (str): The extracted docstring help for the argument.
                - "kwarg_only" (bool): True if the argument is keyword-only.
            - "has_*args" (bool): True if the function accepts variable positional arguments.
            - "has_**kwargs" (bool): True if the function accepts variable keyword arguments.
            - "return_type" (Any or None): The function's return type hint.
            - "return_choices" (List[Any] or []): Options for `Literal` type hints for the return type, if applicable.
            - "return_doc_help" (str): The extracted docstring help for the return type.
    """
    if (not isinstance(function, _ts.FunctionType)
            and hasattr(function, "__call__")
            and isinstance(function.__call__, _ts.FunctionType)):
        function = function.__call__
    if hasattr(function, "__func__"):
        function = function.__func__
    elif not isinstance(function, _ts.FunctionType):
        raise ValueError(f"Only a real function can be analyzed, not '{function}'")

    name = function.__name__
    arg_count = (
        function.__code__.co_argcount
        + function.__code__.co_kwonlyargcount
        + function.__code__.co_posonlyargcount
    )
    argument_names = list(function.__code__.co_varnames[:arg_count] or ())
    has_args = (function.__code__.co_flags & 0b0100) == 4
    has_kwargs = (function.__code__.co_flags & 0b1000) == 8
    defaults: list[_ty.Any | NoDefault | None] = [NoDefault() for _ in range(len(argument_names))]
    defaults.extend(list(function.__defaults__ or ()))
    if function.__kwdefaults__ is not None:
        defaults.extend(list(function.__kwdefaults__.values()))
    defaults = defaults[len(defaults) - len(argument_names) :]
    types = function.__annotations__ or {}
    docstring = function.__doc__ or ""
    type_hints = _ty.get_type_hints(function)

    pos_argcount = function.__code__.co_argcount  # After which i we have kwarg only
    argument_names.append("return")
    defaults.append(None)

    result = {
        "name": name,
        "doc": docstring,
        "arguments": [],
        "has_*args": has_args,
        "has_**kwargs": has_kwargs,
        "return_type": function.__annotations__.get("return"),
        "return_choices": [],
        "return_doc_help": "",
    }
    for i, (argument_name, default) in enumerate(zip(argument_names, defaults)):
        argument_start = docstring.find(argument_name)
        help_str, choices = "", []
        if argument_start != -1:
            help_start = argument_start + len(
                argument_name
            )  # Where argument_name ends in docstring
            next_line = argument_start + docstring[argument_start:].find("\n")
            help_str = docstring[help_start:next_line].strip(": \n\t")
        if argument_name == "return":
            type_hint = result["return_type"]
            if getattr(type_hint, "__origin__", None) is _ty.Literal:
                choices = type_hint.__args__
            result["return_choices"] = choices
            result["return_doc_help"] = help_str
            continue
        type_hint = type_hints.get(argument_name)
        if getattr(type_hint, "__origin__", None) is _ty.Literal:
            choices = type_hint.__args__
            types[argument_name] = reduce(or_, [type(x) for x in type_hint.__args__])
        result["arguments"].append(
            {
                "name": argument_name,
                "default": default,
                "choices": choices,
                "type": types.get(argument_name),
                "doc_help": help_str,
                "kwarg_only": True if i >= pos_argcount else False,
            }
        )
    return result


class ArgumentParsingError(Exception):
    """Exception raised when an error occurs during argument parsing.

    This exception is used to indicate issues when parsing command-line arguments.
    It includes a message and an index to indicate where the error occurred, helping
    users or developers identify the issue in the input command.

    Attributes:
        index (int): The position in the argument list where the error was detected.
    """

    def __init__(self, message: str, index: int) -> None:
        super().__init__(message)
        self.index: int = index


class Endpoint:
    """Represents the endpoint of a trace from an argument structure object.

    The `EndPoint` class serves as a container for functions associated with
    a particular argument path, providing a way to call the function with
    predefined arguments and keyword arguments.

    Attributes:
        analysis (dict): Dictionary containing analysis data of the function's
            arguments, such as names and types, generated by `analyze_function`.
        _arg_index (dict): A mapping of argument names to their indices, allowing
            quick lookup of argument positions by name.
        _function (_ts.FunctionType): The actual function associated with this endpoint,
            which will be called when the endpoint is invoked.
    """

    def __init__(self, function: _a.Callable) -> None:
        self.analysis: dict[str, list[_ty.Any] | str | None] = analyze_function(
            function
        )
        self._arg_index: dict[str, int] = {
            arg["name"]: i for i, arg in enumerate(self.analysis["arguments"])
        }
        self._function: _a.Callable = function

    def call(self, *args, **kwargs) -> None:
        """Executes the internal function using the specified arguments.

        This method forwards all positional and keyword arguments to the stored
        function, allowing flexible invocation from various contexts.

        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        """
        kwargs = {k: v for (k, v) in kwargs.items() if k not in {"cls", "self"}}  # Hotfix
        self._function(*args, **kwargs)

    def __repr__(self) -> str:
        args = [
            f"{key}: {self.analysis['arguments'][index]}"
            for (key, index) in self._arg_index.items()
        ]
        return f"Endpoint(arguments={args})"


_A = _ty.TypeVar("_A")


class Interface:
    """A command-line argument parser that uses structured arguments and endpoints.

    Argumint is designed to parse CLI arguments using a predefined argument structure.
    It allows users to define and manage argument paths, replace the argument structure,
    and execute endpoints based on parsed arguments.

    Attributes:
        _default_endpoint (Endpoint): The default endpoint to call if a path cannot be resolved.
        _arg_struct (dict): The dictionary representing the current argument structure.
        _endpoints (dict): A mapping of argument paths to endpoint functions.
    """

    def __init__(self, name: str, path_seperator: str = ".") -> None:
        self._name: str = name
        self._path_seperator: str = path_seperator
        self._arg_struct: dict[str, dict] = {name: dict()}
        self._endpoints: dict[tuple[str, ...], Endpoint] = dict()

    @staticmethod
    def _error(i: int, command_string: str) -> None:
        """Displays a caret (`^`) pointing to an error in the command string.

        Args:
            i (int): Index in the command string where the error occurred.
            command_string (str): The command string with the error.
        """
        print(f"{command_string}\n{' ' * i + '^'}")

    @staticmethod
    def _lst_error(
        i: int, arg_i: int, command_lst: list[str], do_exit: bool = False
    ) -> None:
        """Displays an error caret in a list of command arguments.

        This method calculates the error position in a CLI argument list, displaying
        a caret to indicate where the error was found. Optionally, it can exit
        the program.

        Args:
            i (int): Index of the problematic argument in the list.
            arg_i (int): Position within the argument string to place the caret.
            command_lst (list[str]): List of command-line arguments.
            do_exit (bool, optional): If True, exits the program. Defaults to False.
        """
        length = sum(len(item) for item in command_lst[:i]) + i
        print(" ".join(command_lst) + "\n" + " " * (length + arg_i) + "^")
        if do_exit:
            sys.exit(1)

    def _check_path(self, path: str, overwrite_pre_args: dict | None = None) -> bool:
        """Verifies if a specified path exists within the argument structure.

        This method traverses the structure to confirm whether each segment of the
        path is valid and points to an existing command or subcommand.

        Args:
            path (str): The dot-separated path to check within the argument structure.
            overwrite_pre_args (Optional[dict], optional): An optional argument structure
                to check against instead of the default `_arg_struct`.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        overwrite_pre_args = overwrite_pre_args or self._arg_struct
        current_level: str | dict[str, str | dict] = overwrite_pre_args
        for point in path.split("."):
            if point not in current_level or not isinstance(current_level[point], dict):
                return False
            current_level = current_level[point]
        return True

    def path(self, path: str, endpoint: Endpoint | _a.Callable | None = None, /, create_path: bool = True,
             replace_endpoint: bool = True) -> None:
        if endpoint is not None and not isinstance(endpoint, Endpoint):
            endpoint = Endpoint(endpoint)
        split_path: tuple[str, ...] = tuple(path.split(self._path_seperator))
        if split_path in self._endpoints and not replace_endpoint:
            raise ValueError(f"Path {path} already has an endpoint and replace_endpoint was turned off.")
        current_level: dict[str, dict] = self._arg_struct[self._name]
        for piece in split_path:
            if piece not in current_level:
                if not create_path:
                    raise ValueError(f"{piece} was not in the level {current_level} and create_path was turned off.")
                current_level[piece] = dict()
            current_level = current_level[piece]
        self._endpoints[split_path] = endpoint

    def _parse_pre_args(self, arguments: list[str]) -> tuple[tuple[str, ...], list[str], dict[str, dict]]:
        """Parses and validates preliminary arguments from the CLI.

        This method traverses the argument structure and verifies that the provided
        arguments match a valid command path. It returns a structured list of the
        parsed arguments.

        Args:
            arguments (list[str]): List of preliminary command arguments from the CLI.

        Returns:
            list[str]: A list of parsed arguments that form a valid command path.

        Raises:
            IndexError: If an argument does not match any expected value in the structure.
            KeyError: If a required argument is missing from the structure.
        """
        struct_lst = []

        current_struct = self._arg_struct
        i = 0
        call = None
        try:
            for i, call in enumerate(arguments + [None]):  # Need to add empty element as i signifies the "pre_arg area"
                # so when the last arg is from the pre args it gives it as a parameter. To get around that we could
                # start at i=1 to declare the current argument as "pre_arg" without checking, but we would need to
                # reverse that decision if we only have 1 passed arg, so I decided it would be best to just have one
                # empty arg appended at the end that increases i by one in the event we do not have any passed args.
                if call in current_struct:
                    struct_lst.append(call)
                    if not i == len(arguments):
                        current_struct = current_struct[call]
                else:#elif len(current_struct) == 0:  # At endpoint
                    break
                #else:
                #    raise IndexError
        except TypeError:
            print("Too many pre arguments.")
            self._lst_error(i, 0, arguments, True)
        except (IndexError, KeyError):
            print(
                f"The argument '{call}' doesn't exist in current_struct ({current_struct})."
            )
            self._lst_error(i, 0, arguments, True)
        return tuple(struct_lst), arguments[i:], current_struct

    @staticmethod
    def _to_type(to_type: str, type_: _ty.Type[_A] | None) -> _A | None:
        """Converts a string to a specified type.

        This method attempts to convert a string into a specified type. It supports
        basic types, collections, and literals. For collections, it splits the input
        string by whitespace. If a type cannot be determined, it returns None.

        Args:
            to_type (str): The string to be converted.
            type_ (_ty.Type[_A] | None): The target type for conversion.

        Returns:
            _A | None: The converted value, or None if the type is invalid.
        """
        if not type_:
            return None
        if type_ in [list, tuple, set]:
            tmp = to_type.split()
            return type_(tmp)
        elif _ty.get_origin(type_) is _ty.Literal:
            choices = type_.__args__
            choice_types = set(type(choice) for choice in choices)
            if len(choice_types) == 1:
                type_ = choice_types.pop()  # All choices have the same type
            else:  # Choices have different types
                for type_ in choice_types:
                    try:
                        result = type_(to_type)
                    except Exception:
                        continue
                    else:
                        return result
        return type_(to_type)

    @classmethod
    @deprecated("The mode 'native_light' is deprecated. Please use 'argparse' instead.")
    def _parse_args_native_light(
        cls, args: list[str], endpoint: Endpoint, smart_typing: bool = True
    ) -> dict[str, _ty.Any]:
        """Parses command-line arguments in a lightweight manner.

        This method parses arguments for an endpoint function, supporting positional
        arguments, keyword arguments (preceded by '--'), and flags (preceded by '-').
        It also assigns default values if not all arguments are provided.

        Args:
            args (list[str]): The list of arguments from the CLI.
            endpoint (Endpoint): The endpoint for which arguments are parsed.
            smart_typing (bool, optional): If True, attempts to match argument types
                intelligently based on their default values.

        Returns:
            dict[str, _ty.Any]: A dictionary of parsed argument names and values.

        Raises:
            ArgumentParsingError: If an unknown argument is encountered.
        """
        parsed_args = {}
        remaining_args = list(endpoint.analysis["arguments"])

        for i, arg in enumerate(args):
            # Check for keyword argument
            if arg.startswith("--"):
                key, _, value = arg[2:].partition("=")
                if not any(a["name"] == key for a in endpoint.analysis["arguments"]):
                    raise ArgumentParsingError(f"Unknown argument: {key}", i)
                elif not value:
                    raise ArgumentParsingError(
                        f"No value: {key}, pleae use the format {key}=[value]", i
                    )
                arg_obj = next(
                    a for a in endpoint.analysis["arguments"] if a["name"] == key
                )
                parsed_args[key] = (
                    cls._to_type(value, arg_obj["type"]) if arg_obj["type"] else value
                )
                remaining_args.remove(arg_obj)

            # Check for flag argument
            elif arg.startswith("-"):
                key = arg[1:]
                if not any(
                    a["name"] == key and a["type"] is bool
                    for a in endpoint.analysis["arguments"]
                ):
                    raise ArgumentParsingError(f"Unknown flag argument: {key}", i)
                parsed_args[key] = True
                remaining_arg = next(
                    a for a in endpoint.analysis["arguments"] if a["name"] == key
                )
                remaining_args.remove(remaining_arg)

            # Handle positional argument
            else:
                if smart_typing:
                    # Find the first argument with a matching type
                    for pos_arg in remaining_args:
                        if (
                            isinstance(pos_arg["default"], type(arg))
                            or pos_arg["default"] is None
                        ):
                            parsed_args[pos_arg["name"]] = cls._to_type(
                                arg, pos_arg["type"]
                            )
                            remaining_args.remove(pos_arg)
                            break
                    else:
                        raise ArgumentParsingError("No matching argument type found", i)
                else:
                    # Assign to the next available argument
                    if remaining_args:
                        pos_arg = remaining_args.pop(0)
                        parsed_args[pos_arg["name"]] = cls._to_type(
                            arg, pos_arg["type"]
                        )

        # Assign default values for missing optional arguments
        for remaining_arg in remaining_args:
            if remaining_arg["default"] is not None:
                parsed_args[remaining_arg["name"]] = remaining_arg["default"]

        return parsed_args

    @staticmethod
    def _parse_args_argparse(
        args: list[str], endpoint: Endpoint
    ) -> dict[str, _ty.Any]:
        """Parses command-line arguments using the argparse library.

        Sets up argparse to support keyword arguments (prefixed with '--') and flag
        arguments (prefixed with '-'), along with custom help texts.

        Args:
            args (list[str]): The list of command-line arguments to parse.
            endpoint (Endpoint): The endpoint that defines the argument structure.

        Returns:
            dict[str, _ty.Any]: A dictionary of parsed argument names and values.
        """
        parser = argparse.ArgumentParser()

        # Set up argparse for keyword and flag arguments
        for arg in endpoint.analysis["arguments"]:
            if arg["type"] is bool:  # For boolean flags
                parser.add_argument(
                    f"-{arg['name'][0]}",
                    f"--{arg['name']}",
                    action="store_true",
                    help=arg.get("help", "No help available"),
                )
            else:
                parser.add_argument(  # Positional
                    arg['name'],
                    type=arg["type"],
                    default=argparse.SUPPRESS,
                    choices=arg["choices"] if arg["choices"] else None,
                    help=arg.get("help", "No help available"),
                    nargs="?"
                )
                parser.add_argument(
                    f"--{arg['name']}", dest=arg['name'],
                    type=arg["type"],
                    default=argparse.SUPPRESS,
                    choices=arg["choices"] if arg["choices"] else None,
                    help=arg.get("help", "No help available"),
                )

        # Parse arguments with argparse
        parsed_args: argparse.Namespace = parser.parse_args(args)
        for arg in endpoint.analysis["arguments"]:
            if not hasattr(parsed_args, arg["name"]):
                setattr(parsed_args, arg["name"], arg["default"])
        return vars(parsed_args)

    def parse_cli(self, arguments: list[str] | None = None,
                  mode: _ty.Literal["argparse", "native_light"] = "argparse") -> None:
        """Parses CLI arguments and calls the endpoint based on the parsed path.

        This method processes command-line input, navigates the argument structure,
        and calls the relevant endpoint function. If the path is unmatched, it calls
        the `default_endpoint`.

        Args:
            arguments (list, optional): Arguments to parse, if None, use sys.argv instead.
            mode (Literal["arg_parse", "native_light"], optional): Mode to parse
                arguments. Defaults to `"arg_parse"`, but `"native_light"` can be used
                for lightweight parsing.
        """
        if mode == "native_light":
            warnings.warn("The mode 'native_light' is deprecated. Please use 'argparse' instead.", stacklevel=2)
        arguments = (arguments or sys.argv)
        arguments[0] = self._name  # Implant correct root node
        pre_args, val_args, curr_struct = self._parse_pre_args(arguments)

        endpoint = self._endpoints.get(pre_args[1:])  # Skip root node
        if endpoint is None:
            def _explore_path(curr_path: tuple[str, ...], path: dict[str, dict]) -> list[str]:
                if not path:
                    return [self._path_seperator.join(curr_path)]
                shard: list[str] = [self._path_seperator.join(curr_path)] if curr_path in self._endpoints else []
                return shard + reduce(lambda x, y: x+y, [_explore_path((*curr_path, name), rest) for name, rest in path.items()], [])

            print("commands:")  # Provide structure help
            possible_paths: list[str] = _explore_path(pre_args, curr_struct)
            if self._path_seperator.join(pre_args) in possible_paths:
                possible_paths.remove(self._path_seperator.join(pre_args))
            for possible_path in possible_paths or ["(no commands registered)"]:
                print(f" - {possible_path}")
            return  # sys.exit(0)  # We can just return here
        parsed_arguments: dict[str, _ty.Any] = {
            "native_light": self._parse_args_native_light,
            "argparse": self._parse_args_argparse
        }[mode](val_args, endpoint)
        endpoint.call(**parsed_arguments)
