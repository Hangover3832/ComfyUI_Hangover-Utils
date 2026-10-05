"""
@author: AlexL
@title: ComfyUI-Hangover-Sympy_Interpreter
@nickname: Hangover-Sympy_Interpreter
@description: A mathematic expression interpreter based on the sympy library

V3 node with io.Autogrow for dynamically growing numeric inputs (a, b, c, …).
"""
import math
import string
from sympy.parsing.sympy_parser import parse_expr
from comfy_api.latest import io, ui


class SympyInterpreter(io.ComfyNode):
    """Mathematical expression interpreter based on SymPy.

    Allows adding unlimited inputs at runtime via the Autogrow mechanism.
    Ports are automatically named a, b, c, … (lowercase letters).
    """

    @classmethod
    def define_schema(cls) -> io.Schema:
        autogrow = io.Autogrow.TemplateNames(
            input=io.MultiType.Input("value", [io.Float, io.Int]),
            names=list("abcdefghijklmnopqrstuvw"),  # a, b, c, d, … 
            min=0,
        )
        return io.Schema(
            node_id="SympyInterpreter",
            display_name="Sympy Interpreter",
            description="Mathematical expression interpreter based on SymPy",
            category="Hangover",
            search_aliases=[
                "sympy", "math", "interpreter", "expression",
                "form", "calculate", "evaluate", "symbolic",
            ],
            inputs=[
                io.String.Input(
                    "expression",
                    default="a",
                    multiline=True,
                ),
                io.Autogrow.Input("values", template=autogrow),
                io.MultiType.Input("x", [io.Float, io.Int], optional=True),
            ],
            outputs=[
                io.Int.Output(display_name="int_A"),
                io.Float.Output(display_name="float_A"),
                io.String.Output(display_name="str_A"),
            ],
        )

    @classmethod
    def execute(cls, *, expression: str, values: io.Autogrow.Type, x:io.Float | io.Int | None = None, **kwargs) -> io.NodeOutput:
        """Evaluate the expression and return the results."""
        if not expression.strip():
            raise ValueError("Expression cannot be empty.")

        # Gather dynamic ports as dict (a, b, c, …)
        variables: dict = dict(values)
        if x is not None:
            variables['x'] = x

        print(f"Math_Interpreter: evaluating expression '{expression}'")
        print(f"  Variables: {variables}")

        expr_A = parse_expr(s=expression, local_dict=variables)

        try:
            result_A = float(expr_A)
        except TypeError:
            result_A = 0.0  # symbolic result, only str_A is meaningful

        result_str = str(expr_A)
        return io.NodeOutput(
            math.floor(result_A),
            result_A,
            result_str,
            ui=ui.PreviewText(result_str),
        )
