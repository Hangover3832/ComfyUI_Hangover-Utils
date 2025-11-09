import re
from comfy.comfy_types.node_typing import InputTypeOptions, IO, InputTypeDict, ComfyNodeABC
from folder_paths import models_dir, get_folder_paths, add_model_folder_path, get_filename_list, get_full_path, filter_files_extensions
from typing import Any, Literal
import pathlib
import random
import pyperclip
import sys


class TextEncodeWildcards(ComfyNodeABC):

    CATEGORY = "Hangover"
    DESCRIPTION = """
        A very simple and basic {wildcard} style replacement text input box.
        Ensure that 'wildcard.txt' files exists in the 'comfyui/models/wildcards' folder or any subfolder.
    """

    RETURN_TYPES = IO.STRING,
    RETURN_NAMES = "string",
    FUNCTION = "encode"

    # preload a list of all .txt files in the wildcards folder
    try:
        Wildcards_Dir = get_folder_paths(folder_name="wildcards")
    except KeyError:
        Wildcards_Dir = f"{models_dir}/wildcards"
        add_model_folder_path(folder_name="wildcards", full_folder_path=Wildcards_Dir)

    Wildcards_Files : list [str] = filter_files_extensions(files=get_filename_list(folder_name="wildcards"),extensions=[".txt"])
    Wildcards_File_Dict: dict[str, list[str]] = {}
    if not Wildcards_Files:
        print(f"Text Encode Wildcards: Warning: No wildcard files were found in '{Wildcards_Dir}'.")

    for file in Wildcards_Files:
        key = object=pathlib.Path(file).stem.lower()
        if (value := get_full_path(folder_name="wildcards", filename=file)): 
            if key in Wildcards_File_Dict.keys():
                Wildcards_File_Dict[key].append(value)
            else:
                Wildcards_File_Dict[key] = [value]


    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {
            "required": {
                    "prompt": (IO.STRING, {"default": "", "multiline": True, "placeholder": "input prompt"}),
                    "seed": (IO.INT, {"control_after_generate": True, "min": 0, "max": sys.maxsize}),
                    "prompt_from_clipboard": (IO.BOOLEAN, {"default": False}),
                    "wildcards": (IO.COMBO, {"options": list(cls.Wildcards_File_Dict.keys()), "default": "wildcards..."})
            }
        }


    @classmethod
    def VALIDATE_INPUTS(cls, prompt_from_clipboard: bool | None = None) -> str | Literal[True]:
        if prompt_from_clipboard and not pyperclip.paste():
            return "Cannot paste from clipboard, clipboard is empty."
        return True


    def replace_placeholder(self, prompt: str, seed: int) -> str:
        random.seed(seed)
        for placeholder in re.findall(pattern=r'{.*?}', string=prompt):
            try:
                file_name = random.choice(seq=self.Wildcards_File_Dict[placeholder[1:-1].lower()])
                with open(file=pathlib.Path(file_name)) as file:
                    wildcard_texts = file.readlines()
                    wildcard_text = random.choice(seq=wildcard_texts).strip()
                prompt = prompt.replace(placeholder, wildcard_text, 1)
            except (KeyError, IndexError):
                print(f"Warning: {placeholder} not found or wildcard file is empty, ignoring.")
                continue 
            except OSError:
                print(f"Error: Unable to open file for {placeholder}, ignoring.")
                continue 
        return prompt


    def encode(self, prompt: str, seed: int, prompt_from_clipboard: bool, wildcards: list[str]) -> tuple[str]:
        if not wildcards:
            print(f"Text Encode Wildcards: Warning: No wildcard files were found.")
            return prompt,

        prompt = clp if (clp := pyperclip.paste()) and prompt_from_clipboard else prompt
        return self.replace_placeholder(prompt=prompt, seed=seed),


def Run_Tests() -> None:
    encoder = TextEncodeWildcards()
    print(f"{TextEncodeWildcards.INPUT_TYPES()}")
    print(f"{encoder.Wildcards_Files=}")
    print(f"{encoder.Wildcards_File_Dict=}")
    if not (prompt := pyperclip.paste()):
        prompt = "{RandomEth} ; {Randomplaces} ; {randomAction}"
    print(encoder.replace_placeholder(prompt=prompt, seed=0))
    print(encoder.replace_placeholder(prompt=prompt, seed=0))
    print(encoder.replace_placeholder(prompt=prompt, seed=1))


if __name__ == "__main__":
    Run_Tests()
