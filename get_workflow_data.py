"""
@author: AlexL
@title: ComfyUI-Hangover-Workflow_Data
@nickname: Hangover-Workflow_Data
@description: Extracts data from the node connected to this node's 'node' input.

V3 node.
"""
import functools
import json
from typing import Any
from comfy_api.latest import io


class GetWorkflowData(io.ComfyNode):
    """ Extracts data from the node connected to this node's 'node' input."""
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="Get Workflow Data",
            display_name="Get Workflow Data",
            category="Hangover",
            description=(
                "This node extracts data from the node connected to the 'node' input.\n"
                "field_value_str is built from value_prefix + field_value + value_suffix."
            ),
            inputs=[
                io.String.Input("value_prefix", default=""),
                io.String.Input("field_name", default=""),
                io.String.Input("value_suffix", default=""),
                io.AnyType.Input("node", optional=True),
            ],
            hidden=[
                io.Hidden.prompt,
                io.Hidden.extra_pnginfo,
                io.Hidden.unique_id,
            ],
            outputs=[
                io.String.Output("workflow_json"),
                io.String.Output("field_value_str"),
                io.Int.Output("field_value_int"),
                io.Float.Output("field_value_float"),
                io.String.Output("node_data"),
            ],
        )

    @staticmethod
    def get_nested_value(data, keys) -> Any | None:
        """Navigate `data` along a dotted key path ('inputs.text'), raising KeyError if a key is missing."""

        def pass_obj(obj, key):
            if isinstance(obj, dict):
                return obj[key]
            if isinstance(obj, (list, tuple)):
                try:
                    return obj[int(key)]
                except ValueError:
                    raise ValueError(f"Expected an integer index value for object <{obj}>")
            return None

        return functools.reduce(pass_obj, keys.split("."), data)


    @classmethod
    def execute(cls, *, value_prefix="", field_name="", value_suffix="", node=None, **kwargs) -> io.NodeOutput:
        this_node_data = cls.hidden.prompt[cls.hidden.unique_id]
        try:
            prev_node_id = this_node_data["inputs"]["node"][0]
            prev_node_data = cls.hidden.prompt[prev_node_id]
            node_data = json.dumps(prev_node_data)
        except (KeyError, TypeError):
            return io.NodeOutput(json.dumps(cls.hidden.extra_pnginfo), "", 0, 0.0, "")

        try:
            field_value = cls.get_nested_value(prev_node_data, field_name) if field_name else node_data
        except KeyError:
            raise KeyError(f"Error: field name <{field_name}> not found in the parent node ({prev_node_data})")

        try:
            value_float = float(field_value) if field_value else 0.
            value_int = int(field_value) if field_value else 0
        except (ValueError, TypeError):
            value_int = 0
            value_float = 0.0

        field_value = f"{value_prefix}{str(field_value)}{value_suffix}"
        return io.NodeOutput(
            json.dumps(cls.hidden.extra_pnginfo),
            field_value,
            value_int,
            value_float,
            node_data,
        )
