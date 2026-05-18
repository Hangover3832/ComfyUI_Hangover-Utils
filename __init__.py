from .save_image_extra_metadata import SaveImage_NoWorkflow
from .image_scale_bounding_box import ImageScaleBoundingBox
from .inpaint_model import MakeInpaintModel
from .clipboard_paste import PasteImage
from .text_encode_wildcards import TextEncodeWildcards
from .get_workflow_data import GetWorkflowData, GetGenerationData

from .math_interpreter import MathExtension, SympyInterpreter

# V3 entrypoint – must be here in __init__.py so that ComfyUI can find it.
# ComfyUI only loads __init__.py of each custom_nodes/ folder as a module and
# searches for NODE_CLASS_MAPPINGS or comfy_entrypoint there.
async def comfy_entrypoint() -> MathExtension:
    return MathExtension()


# V1 nodes are registered via NODE_CLASS_MAPPINGS.
# V3 nodes (SympyInterpreter) are also added here because ComfyUI's V3 loader
# (elif branch) only activates when NODE_CLASS_MAPPINGS is absent.
# Therefore we register the V3 node manually in NODE_CLASS_MAPPINGS.
NODE_CLASS_MAPPINGS: dict[str, object] = {
    "Save Image w/o Metadata" : SaveImage_NoWorkflow,
    "Image Scale Bounding Box" : ImageScaleBoundingBox,
    "Make Inpaint Model": MakeInpaintModel,
    "Image Clipboard Paster": PasteImage,
    "Text Encode Wildcards": TextEncodeWildcards,
    "Get Workflow Data": GetWorkflowData,
    "SympyInterpreter": SympyInterpreter,
}


# Try to import pyperclipimg, it might need some dependencies depending on the OS,
# so we catch the exception and pyperclipimg will throw an appropriate message.
# The node becomes unavailable in this case.
try:
    from pyperclipimg import copy
    from .clipboard_copy import CopyImage
    NODE_CLASS_MAPPINGS["Image Clipboard Copy"] = CopyImage
except NotImplementedError as e:
    print("Save Image w/o Metadata: Error importing 'pyperclipimg' module. Copy to clipboard is not abailable.")
    print(e)
