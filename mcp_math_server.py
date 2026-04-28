# mcp_math_server.py
from mcp.server.fastmcp import FastMCP
import ast
import operator

mcp = FastMCP("math-server")

# Bezpieczne obliczenia (ze starego kodu)
ALLOWED_OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.USub: operator.neg,
}

def eval_expr(node):
    if isinstance(node, ast.Constant): return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_expr(node.left), eval_expr(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in ALLOWED_OPERATORS:
        return ALLOWED_OPERATORS[type(node.op)](eval_expr(node.operand))
    raise ValueError("Niedozwolone wyrażenie")

@mcp.tool()
def math(expression: str) -> float:
    """Oblicza wyrażenie matematyczne (np. (3+5)*12)."""
    try:
        # Czyszczenie proste
        cleaned = "".join(c for c in expression if c.isdigit() or c in "+-*/()*^ .")
        cleaned = cleaned.replace("^", "**")
        tree = ast.parse(cleaned, mode='eval').body
        return eval_expr(tree)
    except Exception as e:
        return f"Błąd: {e}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
