import ast
import pathlib

def find_imports(path="."):
    path = pathlib.Path(path)
    imports = set()

    for pyfile in path.rglob("*.py"):
        with pyfile.open("r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=str(pyfile))
            except SyntaxError:
                continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.add(n.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split(".")[0])
    return sorted(imports)


if __name__ == "__main__":
    modules = find_imports()
    print(f"Modules:\n{modules}")