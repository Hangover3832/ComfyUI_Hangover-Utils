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


class SaveImage_NoWorkflow(SaveImage):
    """
    Inheritance of ComfyUI's SaveImage class.
    This node lets choise if the image itself, and/or the workflow get saved within the image.
    """

    def __init__(self):
        super().__init__()

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict]:
        return {"required": 
                    {"images": ("IMAGE", ), "filename_prefix": ("STRING", {"default": "ComfyUI"}),
                    "save_image": ("BOOLEAN", {"default": True}),
                    "include_workflow": ("BOOLEAN", {"default": True}),
                    },
                    
                "hidden": 
                    {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
                }


    RETURN_TYPES = ()
    FUNCTION = "save_images"
    OUTPUT_NODE = True
    CATEGORY = "Hangover"


    def save_images(self, images: Tensor, filename_prefix: str = "ComfyUI", prompt: dict | None = None, extra_pnginfo: dict | None = None, 
                    save_image: bool = False, include_workflow: bool = False) -> dict[str, dict[str, list]]:
        
        if not include_workflow:
            extra_pnginfo = None
            prompt = None

        if save_image:
            self.__init__()
        else:
            self.output_dir = folder_paths.get_temp_directory()
            self.type = "temp"
            self.prefix_append = "_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for x in range(5))
            self.compress_level = 1

        # Save the images using the parent's class method
        return(super().save_images(images=images, filename_prefix=filename_prefix, prompt=prompt, extra_pnginfo=extra_pnginfo))
