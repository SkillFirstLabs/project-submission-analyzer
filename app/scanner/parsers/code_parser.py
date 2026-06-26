"""
Code Parser: deep static analysis of Python source files using the `ast` module.

Extracts:
- ClassEvidence    – class definitions and their file paths
- FunctionEvidence – top-level and method function definitions
- RouteEvidence    – FastAPI / Flask / Starlette HTTP route decorators
"""

import ast
from pathlib import Path
from typing import List, Optional, Union

from app.config import get_logger
from app.models.evidence import ClassEvidence, FunctionEvidence, RouteEvidence

logger = get_logger("app.scanner.parsers.code_parser")

# HTTP method names we look for in route decorators
_HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


class CodeParser:
    """
    Uses Python's built-in `ast` module to parse `.py` source files and
    extract structural information (classes, functions, HTTP routes).
    """

    def parse(
        self, workspace_dir: Path, source_files: list
    ) -> tuple[List[ClassEvidence], List[FunctionEvidence], List[RouteEvidence]]:
        """
        Parse all Python source files in the workspace.

        Args:
            workspace_dir: Root of the extracted project workspace.
            source_files: Pre-collected FileEvidence list from LanguageParser.

        Returns:
            Tuple of (classes, functions, routes).
        """
        all_classes: List[ClassEvidence] = []
        all_functions: List[FunctionEvidence] = []
        all_routes: List[RouteEvidence] = []

        python_files = [fe for fe in source_files if fe.path.endswith(".py")]

        for file_ev in python_files:
            file_path = workspace_dir / file_ev.path
            if not file_path.is_file():
                continue

            try:
                source = file_path.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(source, filename=file_ev.path)
            except SyntaxError:
                logger.debug("Skipping file with syntax errors: %s", file_ev.path)
                continue
            except OSError as e:
                logger.warning("Could not read file %s: %s", file_ev.path, e)
                continue

            visitor = _ASTVisitor(relative_path=file_ev.path)
            visitor.visit(tree)

            all_classes.extend(visitor.classes)
            all_functions.extend(visitor.functions)
            all_routes.extend(visitor.routes)

        logger.info(
            "Code scan complete: %d classes, %d functions, %d routes extracted from %d Python files",
            len(all_classes),
            len(all_functions),
            len(all_routes),
            len(python_files),
        )

        return all_classes, all_functions, all_routes


class _ASTVisitor(ast.NodeVisitor):
    """
    AST visitor that collects class definitions, function definitions,
    and HTTP route decorators from a single Python file.
    """

    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.classes: List[ClassEvidence] = []
        self.functions: List[FunctionEvidence] = []
        self.routes: List[RouteEvidence] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.classes.append(
            ClassEvidence(name=node.name, file=self.relative_path)
        )
        # Continue visiting nested class members
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._process_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._process_function(node)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _process_function(
        self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]
    ) -> None:
        """Extract function evidence and check for route decorators."""
        self.functions.append(
            FunctionEvidence(name=node.name, file=self.relative_path)
        )

        for decorator in node.decorator_list:
            route = self._extract_route(decorator)
            if route:
                self.routes.append(route)

        self.generic_visit(node)

    def _extract_route(self, decorator: ast.expr) -> Optional[RouteEvidence]:
        """
        Attempt to extract an HTTP route from a decorator expression.

        Handles patterns like:
          @app.get("/path")
          @router.post("/items/{id}")
          @blueprint.route("/home", methods=["GET"])
        """
        # Pattern 1: @obj.method("/path") – e.g. @router.get("/users")
        if isinstance(decorator, ast.Call):
            func = decorator.func

            if isinstance(func, ast.Attribute):
                method_name = func.attr.lower()

                # FastAPI / Starlette / Flask route methods
                if method_name in _HTTP_METHODS:
                    path = self._extract_first_string_arg(decorator)
                    if path:
                        return RouteEvidence(
                            method=method_name.upper(),
                            path=path,
                            file=self.relative_path,
                        )

                # Flask-style: @app.route("/path", methods=["GET", "POST"])
                if method_name == "route":
                    path = self._extract_first_string_arg(decorator)
                    methods = self._extract_methods_kwarg(decorator)
                    if path:
                        for m in methods:
                            return RouteEvidence(
                                method=m.upper(),
                                path=path,
                                file=self.relative_path,
                            )
                        # Default to GET if no methods specified
                        return RouteEvidence(
                            method="GET",
                            path=path,
                            file=self.relative_path,
                        )

        return None

    @staticmethod
    def _extract_first_string_arg(call_node: ast.Call) -> Optional[str]:
        """Return the first positional string argument of a call node."""
        if call_node.args:
            first = call_node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                return first.value
        return None

    @staticmethod
    def _extract_methods_kwarg(call_node: ast.Call) -> List[str]:
        """Extract the `methods=[...]` keyword argument from a decorator."""
        for kw in call_node.keywords:
            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                return [
                    elt.value
                    for elt in kw.value.elts
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                ]
        return []
