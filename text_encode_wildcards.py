from ctypes import sizeof
import re
from comfy.comfy_types.node_typing import IO, InputTypeDict, ComfyNodeABC
from folder_paths import models_dir, get_folder_paths, add_model_folder_path, get_filename_list, get_full_path, filter_files_extensions
from typing import Literal
from pathlib import Path
import random
import pyperclip
import sys
from hashlib import sha256


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

        if files:
            self['*'] = self.root_folders # add the root path(s) as keyword '{*}'
            for file in files:
                file_path = Path(get_full_path(folder_name=folder_name, filename=file)).absolute().resolve() # type: ignore
                folder_path = file_path.parent.absolute().resolve()
                file_folder_name = folder_path.stem.lower()
                file_name = file_path.stem.lower()

                # add the file to the list in the dict:
                if file_name in self.keys():
                    self[file_name].append(file_path)
                else:
                    self[file_name] = [file_path]

                # add the folder to the list in the dict...
                if folder_path not in self.root_folders: # if its not one of the root folders
                    if file_folder_name not in self.keys():
                        self[file_folder_name] = [folder_path]
        else:
            self.print_warning()

    def __repr__(self) -> str:
        size = sys.getsizeof(self)
        keys = len(self)
        return f"Wildcards: {len(self)}, wildcard files: {self.num_files}, size: {sys.getsizeof(self)} bytes."

    def __str__(self) -> str:
        result: str = ""
        for key, value in self.items():
            result += f"{key}:\n"
            for value in self[key]:
                result += f"  -{value}\n"
        return result

    def print_warning(self) -> None: 
        print_yellow(f"Warning: Text Encode Wildcards: No fildcards files could be found in '{self.root_folders}'")

    def _get_items(self, key_word: str) -> list[Path]:
        if key_word in self.keys():
            return self[key_word]
        else:
            return []

    def _get_random_file(self, key_word: str, recursive: bool, seed: int = -1) -> Path | None:
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
        return list(self.keys())


class TextEncodeWildcards(ComfyNodeABC):

    CATEGORY = "Hangover"
    DESCRIPTION = """
        A very simple and basic {wildcard} style replacement text input box.
        Ensure that wildcard files are stored in the 'comfyui/models/wildcards' folder
        or any of its subfolder. The wildrard can also be a folder name, in which case
        a random file will be choosen.
    """

    RETURN_TYPES: tuple[IO] = IO.STRING,
    RETURN_NAMES: tuple[str] = "string",
    FUNCTION = "encode"
    WILDCARD_EXTENSIONS: list[str] = [".txt"]

    # preload a list of all .txt files in the wildcards folder
    try:
        Wildcards_Folders: list[Path] = [Path(path).absolute().resolve() for path in get_folder_paths(folder_name="wildcards")]
    except:
        Wildcards_Folders = [Path(f"{models_dir}/wildcards").absolute().resolve()]
        add_model_folder_path(folder_name="wildcards", full_folder_path=str(Wildcards_Folders[0]))

    Wildcards_File_Dict: WildcardFileDict = WildcardFileDict(folder_name="wildcards", extensions=WILDCARD_EXTENSIONS)

    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                    "prompt": (IO.STRING, {"default": "", "multiline": True, "placeholder": "input prompt"}),
                    "seed": (IO.INT, {"control_after_generate": True, "min": 0, "max": sys.maxsize}),
                    "prompt_from_clipboard": (IO.BOOLEAN, {"default": False}),
                    "recurive_search": (IO.BOOLEAN, {"default": False}),
                    "wildcards": (IO.COMBO, {"options": list(cls.Wildcards_File_Dict.keys()), "default": "wildcards..."})
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, prompt_from_clipboard: bool | None = None) -> str | Literal[True]:
        if prompt_from_clipboard and not pyperclip.paste():
            return "Cannot paste, clipboard is empty."
        return True

    @classmethod
    def IS_CHANGED(cls, prompt: str, seed: int, prompt_from_clipboard: bool, recurive_search: bool, wildcards: list[str]) -> str:
        sha = sha256()
        if prompt_from_clipboard:
            sha.update(pyperclip.paste().encode())
        return sha.digest().hex()

    def replace_placeholder(self, prompt: str, recursive: bool, seed: int = -1) -> str:
        if seed >= 0:
            random.seed(a=seed)

        for s, placeholder in enumerate(iterable=re.findall(pattern=r'{.*?}', string=prompt)):
            text = self.Wildcards_File_Dict.get_random_entry(key_word=placeholder[1:-1].lower(), recursive=recursive, seed=seed+s)
            if text:
                prompt = prompt.replace(placeholder, text, 1)
        return prompt


    def encode(self, prompt: str, seed: int, prompt_from_clipboard: bool, recurive_search: bool, wildcards: list[str]) -> tuple[str]:
        if not wildcards:
            print(f"Text Encode Wildcards: Warning: No wildcard files were found.")
            return prompt,

        prompt = clp if (clp := pyperclip.paste()) and prompt_from_clipboard else prompt
        return self.replace_placeholder(prompt=prompt, recursive=recurive_search, seed=seed),


def test_dict():
    f = WildcardFileDict(folder_name="wildcards", extensions=[".txt"])
    print(repr(f))
    print(f)


def run_tests() -> None:
    encoder = TextEncodeWildcards()

    print(f"{models_dir=}")
    print(f"{get_folder_paths(folder_name="wildcards")=}")

    if not (prompt := pyperclip.paste()):
        prompt = "{*}"

    for _ in range(10):
        print(encoder.replace_placeholder(prompt=prompt, recursive=True, seed=-1))

if __name__ == "__main__":
    test_dict()
    run_tests()
