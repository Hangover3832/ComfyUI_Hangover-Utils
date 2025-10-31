"""
@author: AlexL
@title: ComfyUI-Hangover-Sympy_Interpreter
@nickname: Hangover-Sympy_Interpreter
@description: A mathematic expression interpreter based on the sympy library
"""
from sympy.parsing.sympy_parser import parse_expr
from comfy.comfy_types import IO
import math
from typing import Any

class Sympy_Interpreter:
    RETURN_TYPES = (
        IO.INT,
        IO.FLOAT,
        IO.STRING,
    )
    RETURN_NAMES = (
        "int_A",
        "float_A",
        "str_A",
    )

    Config = {
        "num_vars": 6,
    }

    FUNCTION = "calc"
    CATEGORY = "Hangover"

    # Define the input variables dictionary:
    Input_Vars: list[str] = [chr(c + ord("a")) for c in range(Config["num_vars"])]
    Variables: dict[str, tuple] = {key: (IO.ANY,) for key in Input_Vars}

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, dict]:
        return {
            "required": {
                "expression": (IO.STRING, {"multiline": False, "default": "0"},),
            },
            "optional" : cls.Variables,
        }

    
    def calc(self, expression: str, **kwargs: Any) -> tuple[int, float, str]:
        """ Evaluate the expression and return the results.  """
        
        print(f"Math_Interpreter: evaluating expression A({expression})")
        expr_A = parse_expr(s=expression, local_dict=kwargs)
        try:
            result_A = float(expr_A)
        except TypeError:
            result_A = 0.0

        return (
            math.floor(result_A),
            result_A,
            str(expr_A),
        )


def selfTest() -> None:
    from random import random

    sympy: Sympy_Interpreter = Sympy_Interpreter()
    try:
        print(f"{sympy.INPUT_TYPES()=}")
        print(f"{sympy.RETURN_TYPES=}")
        print(f"{sympy.RETURN_NAMES=}")
        print(f"{sympy.Input_Vars=}")
        print(f"{sympy.Variables=}")
        variables = {key: random() for key in sympy.Input_Vars}
        print(f"{variables=}")
        expression = f"{sympy.Input_Vars[0]}"
        for v in sympy.Input_Vars[1:-1]:
            expression += f"+{v}"
        res_int, res_flt, res_str = sympy.calc(expression=expression, **variables)
        print(f"{res_int=}, {res_flt=}, {res_str=}")
        print(f"{type(res_int)=}, {type(res_flt)=}, {type(res_str)=}")
        print("Tests sucess")
    except:
        print("Tests failed")
        raise


if __name__ == "__main__":
    selfTest()