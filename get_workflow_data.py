from comfy.comfy_types.node_typing import IO, ComfyNodeABC, InputTypeDict
from typing import Any
import json
import functools
import torch


class WorkFlowData(ComfyNodeABC):
    def get_nested_value(self, data, keys) -> Any:
        """recursively dismantle the data object until the 'dot.formatet.key' is found, or en exception is trown if not"""

        def pass_obj(obj: dict | tuple | list, key: str | int) -> dict | list | tuple:
            if isinstance(obj, dict):
                return obj[key]
            elif isinstance(obj, (list, tuple)):
                try:
                    return obj[int(key)]
                except ValueError:
                    raise ValueError(f"Expected an integer index value for object <{obj}>")

        return functools.reduce(pass_obj, keys.split('.'), data)


    def get_value(self, node: dict, keys: str) -> Any:
        result = self.get_nested_value(data=node, keys=keys)
        if isinstance(result, (list, dict)):
            print(f"Warning: Get Generation Data: geting values from connected inputs is not supported <{keys}>")
            result = None
        return result


class GetWorkflowData(WorkFlowData):
    RETURN_TYPES = IO.STRING, IO.STRING, IO.INT, IO.FLOAT,
    RETURN_NAMES = "workflow_json", "field_value_str", "field_value_int", "field_value_float",
    FUNCTION = "get_data"
    CATEGORY = "Hangover"
    NODE_INPUT_NAME = "node"


    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {"required": {
                    "field_name": (IO.STRING, {"default": "_meta.title"}),
                    },
                "optional": {
                    cls.NODE_INPUT_NAME: (IO.ANY, {}),
                },
                "hidden": {
                    "prompt": "PROMPT", 
                    "extra_pnginfo": "EXTRA_PNGINFO",
                    "unique_id": "UNIQUE_ID",
                    },
                }


    def get_data(self, field_name: str, 
                 prompt: dict, extra_pnginfo: dict, unique_id: str,
                 node: Any | None = None
                 ) -> tuple[str, str, int, float]:
        
        if node is None:
            return json.dumps(obj=extra_pnginfo), "", 0, 0.0,

        this_node_data = prompt[unique_id]
        prev_node_id = this_node_data["inputs"][self.NODE_INPUT_NAME][0]
        prev_node = prompt[prev_node_id]
        print(f"GetWorkflowData: Parent node data = {prev_node}")

        try:
            field_value = self.get_nested_value(data=prev_node, keys=field_name) if field_name else ""
        except KeyError:
            raise KeyError(f"Error: field name <{field_name}> not found in the parent node ({prev_node})")

        try:
            value_float: float = float(field_value)
            value_int: int = int(field_value)
        except (ValueError, TypeError):
            value_int = 0
            value_float = 0.0

        return json.dumps(obj=extra_pnginfo), str(object=field_value), value_int, value_float,


class GetGenerationData(WorkFlowData):
    RETURN_NAMES = "int_seed", "int_steps", "float_cfg", "float_denoise", "int_batch_size", "str_seed", "str_steps", "str_cfg", "str_denoise", "str_batch_size", "sampler", "scheduler",
    RETURN_TYPES = IO.INT, IO.INT, IO.FLOAT, IO.FLOAT, IO.INT, IO.STRING, IO.STRING, IO.STRING, IO.STRING, IO.STRING, IO.STRING, IO.STRING,
    FUNCTION = "get_data"
    CATEGORY = "Hangover"

    @classmethod
    def INPUT_TYPES(cls) -> InputTypeDict:
        return {"required": {"ksampler": (IO.LATENT, {}),},
                "hidden": {
                    "prompt": "PROMPT", 
                    "unique_id": "UNIQUE_ID",
                    },
                }


    def get_data(self, ksampler: dict[str, torch.Tensor], prompt: dict, unique_id: str
                 ) -> tuple[int, int, float, float, int, str, str, str, str, str, str, str]:
        this_node_data = prompt[unique_id]
        prev_node_id = this_node_data["inputs"]["ksampler"][0]
        prev_node = prompt[prev_node_id]

        if (seed := self.get_value(node=prev_node, keys="inputs.seed")) is None:
            seed = 0
        if (steps := self.get_value(node=prev_node, keys="inputs.steps")) is None:
            steps = 0
        if (cfg_scale := self.get_value(node=prev_node, keys="inputs.cfg")) is None:
            cfg_scale = 0.0
        if (denoise := self.get_value(node=prev_node, keys="inputs.denoise")) is None:
            denoise = 0.0
        if (sampler_name := self.get_value(node=prev_node, keys="inputs.sampler_name")) is None:
            sampler_name = ""
        if (scheduler_name := self.get_value(node=prev_node, keys="inputs.scheduler")) is None:
            scheduler_name = ""
        batch_size: int = ksampler["samples"].shape[0]

        return (seed, steps, cfg_scale, denoise, batch_size, 
                str(seed), str(steps), f"{cfg_scale:.2f}", f"{denoise:.2f}", str(batch_size), 
                sampler_name, scheduler_name,)


if __name__ == "__main__":
    GetWorkflowData()
    GetGenerationData()