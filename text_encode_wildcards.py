import re
import random
import sys
import pyperclip
from hashlib import sha256
from _hashlib import HASH
from pathlib import Path

from comfy_api.latest import io
from folder_paths import models_dir, get_folder_paths, add_model_folder_path, get_filename_list, get_full_path, filter_files_extensions


def print_yellow(text: str) -> None:
    print(f"\033[93m{text}\033[0m")


class WildcardFileDict(dict[str, list[Path]]):
    """A dicionary that contains all wildcard files in the current ComfyUI installation"""

    def __init__(self, folder_name:str, extensions:list[str]) -> None:
        super().__init__()
        self.extensions = extensions
        self.root_folders = [Path(path).absolute().resolve() for path in get_folder_paths(folder_name=folder_name)]
        files: list[str] = filter_files_extensions(files=get_filename_list(folder_name=folder_name),extensions=extensions)
        self.num_files = len(files)

        # populate the dictionary with the wildcard files and folder names
        if files:
            entries: dict[str, list[Path]] = {}
            self['*'] = self.root_folders # add the root path(s) as keyword '{*}'
            for file in files:
                file_path = Path(get_full_path(folder_name=folder_name, filename=file)).absolute().resolve() # type: ignore
                folder_path = file_path.parent.absolute().resolve()
                file_folder_name = folder_path.stem.lower() + '*'
                file_name = file_path.stem.lower()

                # add the file to the list in the dict:
                if file_name in self.keys():
                    entries[file_name].append(file_path)
                else:
                    entries[file_name] = [file_path]

                # add the folder to the list in the dict...
                if folder_path not in self.root_folders: # if its not one of the root folders
                    if file_folder_name in entries.keys():
                        if folder_path not in entries[file_folder_name]:
                            entries[file_folder_name].append(folder_path)
                    else:
                        entries[file_folder_name] = [folder_path]

            self.update(sorted(entries.items(), key=lambda item: item[0]))
        else:
            self.print_warning()

    def __repr__(self) -> str:
        """ Return a string representation of the WildcardFileDict, including the number of wildcards, number of wildcard files, and size in bytes."""

        size = sys.getsizeof(self)
        keys = len(self)
        return f"Wildcards: {len(self)}, wildcard files: {self.num_files}, size: {sys.getsizeof(self)} bytes."

    def __str__(self) -> str:
        """ Return a string representation of the WildcardFileDict, including the keys and their corresponding values."""

        result: str = ""
        for key, value in self.items():
            result += f"{key}:\n"
            for value in self[key]:
                result += f"  -{value}\n"
        return result

    def print_warning(self) -> None:
        print_yellow(f"Warning: Text Encode Wildcards: No fildcards files could be found in '{self.root_folders}'")

    def _get_items(self, key_word: str) -> list[Path]:
        """ Return a list of Path objects corresponding to the given key_word. If the key_word is not found, return an empty list."""
        if key_word in self.keys():
            return self[key_word]
        else:
            return []

    def _get_random_file(self, key_word: str, recursive: bool, seed: int = -1) -> Path | None:
        """ Return a random Path object corresponding to the given key_word. If the key_word is not found, return None."""
        if seed >= 0:
            random.seed(seed)
        items = self._get_items(key_word=key_word)
        if not items:
            print_yellow(f"No entries found for key word '{key_word}', skipping.")
            return

        result: Path = random.choice(self._get_items(key_word=key_word))
        _glob = result.rglob if recursive else result.glob
        if result.is_dir():
            if (file_list := [file for ext in self.extensions for file in _glob(pattern=f"*{ext}")]):
                return random.choice(file_list)
            else:
                print_yellow(text=f"No wildcars files found for '{key_word}' in folder '{result}', skipping.")
                return
        elif result.is_file():
            return result
        else:
            raise IOError(f"Error reading '{result}'.")

    def get_random_entry(self, key_word: str, recursive: bool, seed: int = -1) -> str | None:
        """ Return a random line from a wildcard file corresponding to the given key_word. If the key_word is not found, return None."""
        if not self:
            self.print_warning()
            return

        item = self._get_random_file(key_word=key_word, recursive=recursive, seed=seed)
        if item is not None:
            print(f"Getting wildcard entry for '{key_word}' from '{item}'")
            with open(file=item, encoding="utf-8") as file:
                if (lines := [line.strip() for line in file.readlines() if line.strip() and not line.strip().startswith('#')]):
                    return random.choice(seq=lines)
                else:
                    print_yellow(text=f"Warning: '{item}' seem to be empty, skipping.")

    @property
    def get_keys(self) -> list[str]:
        """ Return a list of all keys in the WildcardFileDict."""
        return list(self.keys())


class TextEncodeWildcards(io.ComfyNode):
    """ A very simple and basic {wildcard} style replacement text input box."""
    WILDCARD_EXTENSIONS: list[str] = [".txt"]

    # preload a list of all .txt files in the wildcards folder
    try:
        Wildcards_Folders: list[Path] = [Path(path).absolute().resolve() for path in get_folder_paths(folder_name="wildcards")]
    except:
        Wildcards_Folders = [Path(f"{models_dir}/wildcards").absolute().resolve()]
        add_model_folder_path(folder_name="wildcards", full_folder_path=str(Wildcards_Folders[0]))

    Wildcards_File_Dict: WildcardFileDict = WildcardFileDict(folder_name="wildcards", extensions=WILDCARD_EXTENSIONS)

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Text Encode Wildcards",
            display_name="Text Encode Wildcards",
            category="Hangover",
            description=(
                "A very simple and basic {wildcard} style replacement text input box.\n"
                "Ensure that wildcard files are stored in the 'comfyui/models/wildcards' folder\n"
                "or any of its subfolder. The wildrard can also be a folder name, in which case\n"
                "a random file will be choosen."
            ),
            inputs=[
                io.String.Input("prompt", default="", multiline=True, placeholder="input prompt"),
                io.Int.Input("seed", min=0, max=sys.maxsize, control_after_generate=True),
                io.Boolean.Input("prompt_from_clipboard", default=False),
                io.Boolean.Input("recurive_search", default=False),
                io.Combo.Input("wildcards", options=list(cls.Wildcards_File_Dict.keys()), default="wildcards..."),
            ],
            outputs=[
                io.String.Output("string"),
            ],
        )

    @classmethod
    def validate_inputs(cls, *, prompt_from_clipboard: bool | None = None, **kwargs) -> bool | str:
        """ Validate the inputs for the TextEncodeWildcards node. If prompt_from_clipboard is True, 
        check if the clipboard is empty and return an error message if it is. Otherwise, return True."""
        if prompt_from_clipboard and not pyperclip.paste():
            return "Cannot paste, clipboard is empty."
        return True

    @classmethod
    def fingerprint_inputs(cls, *, prompt_from_clipboard: bool | None = None, **kwargs) -> str:
        """ Generate a fingerprint for the inputs of the TextEncodeWildcards node. If prompt_from_clipboard is True,"""
        sha: HASH = sha256()
        if prompt_from_clipboard:
            sha.update(pyperclip.paste().encode())
        return sha.digest().hex()

    def replace_placeholder(self, prompt: str, recursive: bool, seed: int = -1) -> str:
        """ Replace all placeholders in the prompt with random entries from the wildcard files. 
        If recursive is True, search for wildcards in subfolders as well. 
        If seed is provided, use it to seed the random number generator for reproducibility.
        """
        if seed >= 0:
            random.seed(a=seed)

        for s, placeholder in enumerate(iterable=re.findall(pattern=r'{.*?}', string=prompt)):
            text = self.Wildcards_File_Dict.get_random_entry(key_word=placeholder[1:-1].lower(), recursive=recursive, seed=seed+s)
            if text:
                prompt = prompt.replace(placeholder, text, 1)
        return prompt

    @classmethod
    def execute(cls, *, prompt: str = "", seed: int = 0, prompt_from_clipboard: bool = False, recurive_search: bool = False, wildcards: str = "", **kwargs) -> io.NodeOutput:
        """ Execute the TextEncodeWildcards node. If prompt_from_clipboard is True, use the text from the clipboard as the prompt."""
        if not wildcards:
            print(f"Text Encode Wildcards: Warning: No wildcard files were found.")
            return io.NodeOutput(prompt)

        prompt = clp if (clp := pyperclip.paste()) and prompt_from_clipboard else prompt
        return io.NodeOutput(cls().replace_placeholder(prompt=prompt, recursive=recurive_search, seed=seed))


def test_dict():
    """ Test the WildcardFileDict class and print the results."""
    f = TextEncodeWildcards.Wildcards_File_Dict
    print(repr(f))
    print(f)


def run_tests() -> None:
    """ Run a series of tests on the TextEncodeWildcards node."""
    encoder = TextEncodeWildcards()

    print(f"{models_dir=}")
    print(f"{get_folder_paths(folder_name="wildcards")=}")

    prompt = pyperclip.paste() or "{*}"

    for _ in range(10):
        print(encoder.replace_placeholder(prompt=prompt, recursive=True, seed=-1))


if __name__ == "__main__":
    test_dict()
    run_tests()
