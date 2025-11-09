from .save_image_extra_metadata import SaveImage_NoWorkflow
from .image_scale_bounding_box import ImageScaleBoundingBox
from .inpaint_model import MakeInpaintModel
from .math_interpreter import Sympy_Interpreter
from .clipboard_paste import PasteImage
from .text_encode_wildcards import TextEncodeWildcards
from .get_workflow_data import GetWorkflowData, GetGenerationData

# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS: dict[str, object] = {
    "Save Image w/o Metadata" : SaveImage_NoWorkflow,
    "Image Scale Bounding Box" : ImageScaleBoundingBox,
    "Make Inpaint Model": MakeInpaintModel,
    "Sympy Math Interpreter": Sympy_Interpreter,
    "Image Clipboard Paster": PasteImage,
    "Text Encode Wildcards": TextEncodeWildcards,
    "Get Workflow Data": GetWorkflowData,
    # "Get Generation Data": GetGenerationData,
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
