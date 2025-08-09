"""
@author: AlexL
@title: ComfyUI-Hangover-Sympy_Interpreter
@nickname: Hangover-Sympy_Interpreter
@description: A mathematic expression interpreter based on the sympy library
"""
from sympy import *
from sympy.parsing.sympy_parser import parse_expr
from comfy.comfy_types import IO
import math

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

    Input_Vars = [chr(c + ord("a")) for c in range(Config["num_vars"])]
    Variables = {"expression": (IO.STRING, {"multiline": False, "default": "0"},)}
    Variables.update({key: (IO.ANY,) for key in Input_Vars})

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "expression": (IO.STRING, {"multiline": False, "default": "0"},),
            },
            "optional" : s.Variables,
        }

    def calc(self, expression:str, **kwargs):
        print(f"Math_Interpreter: evaluating expression A({expression})")
        expr_A = parse_expr(expression, local_dict=kwargs)
        try:
            result_A = float(expr_A)
        except TypeError:
            result_A = 0.0

        return (
            math.floor(result_A),
            result_A,
            str(expr_A),
        )

    def selfTest(self):
        from random import random
        try:
            print(f"{self.INPUT_TYPES()=}")
            print(f"{self.RETURN_TYPES=}, {self.RETURN_NAMES=}")
            print(f"{self.Input_Vars=}")
            variables = {key: random() for key in self.Input_Vars}
            print(f"{variables=}")
            expression = f"{self.Input_Vars[0]}"
            for v in self.Input_Vars[1:-1]:
                expression += f"+{v}"
            res_int, res_flt, res_str = self.calc(expression, **variables)
            print(f"{res_int=}, {res_flt=}, {res_str=}")
            print(f"{type(res_int)=}, {type(res_flt)=}, {type(res_str)=}")
            print("Tests sucess")
        except:
            print("Tests failed")
            raise


if __name__ == "__main__":
    sympy = Sympy_Interpreter()
    sympy.selfTest()