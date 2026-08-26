from .save_image_extra_metadata import SaveImage_NoWorkflow
from .image_scale_bounding_box import ImageScaleBoundingBox
from .inpaint_model import MakeInpaintModel
from .clipboard_paste import PasteImage
from .text_encode_wildcards import TextEncodeWildcards
from .get_workflow_data import GetWorkflowData
from .math_interpreter import SympyInterpreter
from comfy_api.latest import ComfyExtension, io
from typing_extensions import override

WEB_DIRECTORY = "./web"

class HangoverUtils(ComfyExtension):
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        result = [
            SaveImage_NoWorkflow,
            ImageScaleBoundingBox,
            MakeInpaintModel,
            PasteImage,
            SympyInterpreter,
            TextEncodeWildcards,
            GetWorkflowData,
        ]

        try:
            from pyperclipimg import copy
            from .clipboard_copy import CopyImage
            result.append(CopyImage)
        except NotImplementedError as e:
            print("Save Image w/o Metadata: Error importing 'pyperclipimg' module. Copy to clipboard is not available.")
            print(e)
            
        return result

async def comfy_entrypoint() -> HangoverUtils:
    return HangoverUtils()
