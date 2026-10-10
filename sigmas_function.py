import torch
import numpy as np
from comfy_api.latest import io
from comfy.comfy_types.node_typing import StrEnum
from sympy.parsing.sympy_parser import parse_expr


class FunctionType(StrEnum):
    exponential = "Exponential (x^p)"
    cosine = "Cosine (from 0 to pi/2)"
    gauss = "Gauss (e^-x^2 from 0 to p)"
    custom = "Custom function (use x and p)"


class SigmasFunction(io.ComfyNode):
    """ Create exponential sigmas:
    output = input ^ exponent
    """
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="hangover_sigmas_function",  # keep the V1 class type so existing workflows still resolve
            display_name="Hangover Sigmas Function",
            description="Create sigmas from an function with a parameter",
            category="Hangover",
            search_aliases=["sigmas", "exponential", "scheduler"],
            inputs=[
                io.Combo.Input("function", options=FunctionType),
                io.Int.Input("steps", default=8, min=2),
                io.Float.Input("p", default=1.0, step=0.001),
                io.String.Input("custom_function", default="x**p"),
                io.Float.Input("x_from", default=0.0, step=0.001),
                io.Float.Input("x_to", default=1.0, step=0.001),
            ],
            outputs=[
                io.Sigmas.Output(display_name="sigmas"),
                io.Int.Output("steps")
            ],
        )

    @staticmethod
    def _eval_expression(expression:str, x:float, p:float) -> float:
        return float(parse_expr(expression, local_dict={'x': x, 'p': p}))


    @classmethod
    def execute(cls, *, 
                function:FunctionType, 
                steps:io.Int.Type, 
                p:io.Float.Type, 
                custom_function:io.String.Type,
                x_from:io.Float.Type,
                x_to:io.Float.Type,
                **kwargs) -> io.NodeOutput:

        sigmas = torch.tensor([1.0, 0.0])
        match function:
            case FunctionType.exponential:
                linspace = torch.linspace(1.0, 0.0, steps+1)
                sigmas = linspace ** p

            case FunctionType.cosine:
                linspace = torch.linspace(0, torch.pi/2.0, steps+1)
                sigmas = torch.cos(linspace)

            case FunctionType.gauss:
                linspace = torch.linspace(0.0, p, steps+1)
                sigmas = torch.exp(-torch.square(linspace))

            case FunctionType.custom:
                linspace = torch.linspace(x_from, x_to, steps+1)
                f = lambda x: cls._eval_expression(custom_function, x, p)
                sigmas = linspace.apply_(f)

        
        sigmas = torch.round(sigmas, decimals=5)
        return io.NodeOutput(sigmas, steps)


if __name__ == "__main__":
    result = SigmasFunction.execute(function=FunctionType.custom, steps=10, p=10.0, custom_function="p-x", x_from=0, x_to=1.0)
    print(result.args)
