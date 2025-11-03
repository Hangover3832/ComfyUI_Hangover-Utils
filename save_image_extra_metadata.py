"""
@author: AlexL
@title: ComfyUI-Hangover-Save_Image
@nickname: Hangover-Save_Image_Extra_Metadata
@description: Display, save or not save image, with or without extra metadata.
"""

from nodes import SaveImage
import folder_paths
import random
from torch import Tensor
from PIL import Image
import numpy as np


class SaveImage_NoWorkflow(SaveImage):
    """
    Inheritance of ComfyUI's SaveImage class.
    This node lets choise if the image itself, and/or the workflow get saved within the image.
    """

    def __init__(self):
        super().__init__()

    input_types = {"required": 
                    {"images": ("IMAGE", ), 
                    "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                    "save_image": ("BOOLEAN", {"default": True}),
                    "include_workflow": ("BOOLEAN", {"default": True}),
                    },
                }
    
    # if pyperclipimg_available:
    input_types["required"]["copy_to_clipboard"] = ("BOOLEAN", {"default": False})

    input_types["hidden"] = {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}


    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict]:
        return cls.input_types


    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Hangover"


    def save_images(self, images: Tensor, filename_prefix: str = "ComfyUI", 
                    prompt: dict | None = None, extra_pnginfo: dict | None = None, 
                    save_image: bool = True, include_workflow: bool = True, copy_to_clipboard: bool = False
                    ) -> dict[str, dict[str, list]]:
        
        if not include_workflow:
            extra_pnginfo = None
            prompt = None

        if copy_to_clipboard: # and pyperclipimg_available:
            try:
                from pyperclipimg import copy
            except NotImplementedError as e:
                raise NotImplementedError("""
                      copy_to_clipboard is not available\n
                      Cannot import 'pyperclipimg' module, it might need some dependencies:\n
                      Windows: The pywin32 Python package. Install with pip install pywin32\n
                      macOS: The pyobjc-framework-quartz Python package. Install with pip install pyobjc-framework-quartz\n
                      Linux: Either the xclip or wl-copy commands. Install these with sudo apt install xclip or sudo apt install wl-clipboard
                """)

            if images.shape[0] > 1:
                print(f"Note: copy batched images to the clipboard is not supported, picking the first one")

            img = np.clip(images[0].cpu().numpy() * 255., a_min=0, a_max=255).astype(dtype=np.uint8)
            copy(image=Image.fromarray(obj=img)) # type: ignore


        if save_image:
            self.__init__()
        else:
            self.output_dir = folder_paths.get_temp_directory()
            self.type = "temp"
            self.prefix_append = "_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
            self.compress_level = 1

        # Save the images using the parent's class method
        return(super().save_images(images=images, filename_prefix=filename_prefix, prompt=prompt, extra_pnginfo=extra_pnginfo))
