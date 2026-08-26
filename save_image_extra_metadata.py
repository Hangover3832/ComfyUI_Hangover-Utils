"""
@author: AlexL
@title: ComfyUI-Hangover-Save_Image
@nickname: Hangover-Save_Image_Extra_Metadata
@description: Display or not display, save or not save image, with or without extra metadata.
V3 node.
"""
import random
import numpy as np
import torch
from PIL import Image
from torch import Tensor
from comfy_api.latest import io, ui


class SaveImage_NoWorkflow(io.ComfyNode):
    """
    Saves the input images with a choice of whether to embed the workflow and
    whether to write to the output directory (True) or the temp/preview directory (False).
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Save Image w/o Metadata",
            display_name="Save Image w/o Metadata",
            category="Hangover",
            description="Saves the input images, with a choice of whether to embed the workflow "
                        "and whether to save to the output directory or the temp/preview directory.",
            search_aliases=["save", "save image", "output image", "export image"],
            inputs=[
                io.Image.Input("images", tooltip="The images to save."),
                io.String.Input(
                    "filename_prefix",
                    default="ComfyUI",
                    tooltip="The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes.",
                ),
                io.Boolean.Input(
                    "show_image",
                    default=True,
                    tooltip="Wether the image is shown or not.",
                ),
                io.Boolean.Input(
                    "save_image",
                    default=True,
                    tooltip="Save to the ComfyUI output directory (True) or the temp/preview directory (False).",
                ),
                io.Boolean.Input(
                    "include_workflow",
                    default=True,
                    tooltip="Embed the workflow/prompt into the saved image metadata.",
                ),
                io.Boolean.Input(
                    "copy_to_clipboard",
                    default=False,
                    tooltip="Copy the first image to the clipboard.",
                ),
            ],
            is_output_node=True,
            outputs=[io.Image.Output(display_name="images")],
        )

    @classmethod
    def execute(cls, *, images: Tensor, filename_prefix: str = "ComfyUI",
                show_image: bool = True, save_image: bool = True, include_workflow: bool = True,
                copy_to_clipboard: bool = False, **kwargs) -> io.NodeOutput:

        if copy_to_clipboard:
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
            copy(image=Image.fromarray(obj=img))  # type: ignore

        # cls=None makes ImageSaveHelper skip embedding the workflow/prompt metadata.
        cls_arg = None if not include_workflow else cls

        if save_image:
            saved = ui.ImageSaveHelper.get_save_images_ui(
                images, filename_prefix=filename_prefix, cls=cls_arg, compress_level=4,
            )
        else:
            temp_prefix = filename_prefix + "_temp_" + ''.join(
                random.choice("abcdefghijklmnopqrstupvxyz") for _ in range(5)
            )
            saved = ui.SavedImages(
                ui.ImageSaveHelper.save_images(
                    images, filename_prefix=temp_prefix, folder_type=io.FolderType.temp,
                    cls=cls_arg, compress_level=1,
                )
            )

        return io.NodeOutput(images, ui=saved) if show_image else io.NodeOutput(images)
