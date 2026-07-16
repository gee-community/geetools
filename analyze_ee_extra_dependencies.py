#!/usr/bin/env python3
"""Identify all functions in geetools that depend on ee_extra methods."""

import ast
from collections import defaultdict
from pathlib import Path


class EEExtraDependencyAnalyzer(ast.NodeVisitor):
    """Analyzes Python AST to find ee_extra dependencies."""

    def __init__(self, filename):
        """Initialize the analyzer."""
        self.filename = filename
        self.current_function = None
        self.functions_with_ee_extra = []
        self.ee_extra_calls = []

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node):
        """Visit async function definitions."""
        prev_function = self.current_function
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_Call(self, node):
        """Visit function calls to find ee_extra usage."""
        call_str = self._get_call_string(node)

        if call_str and "ee_extra" in call_str:
            if self.current_function:
                self.functions_with_ee_extra.append(self.current_function)
                self.ee_extra_calls.append({"function": self.current_function, "call": call_str})

        self.generic_visit(node)

    def _get_call_string(self, node):
        """Extract the call string from an AST Call node."""
        try:
            if isinstance(node.func, ast.Attribute):
                parts = []
                current = node.func

                while isinstance(current, ast.Attribute):
                    parts.insert(0, current.attr)
                    current = current.value

                if isinstance(current, ast.Name):
                    parts.insert(0, current.id)
                    return ".".join(parts)
            elif isinstance(node.func, ast.Name):
                return node.func.id
        except Exception:
            pass
        return None


def analyze_file(filepath):
    """Analyze a single Python file for ee_extra dependencies."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = EEExtraDependencyAnalyzer(filepath)
        analyzer.visit(tree)

        return analyzer
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return None


def main():
    """Main function to scan geetools directory."""
    geetools_dir = Path("/home/rambap/github/geetools/geetools")

    # Collect all dependencies
    all_dependencies = defaultdict(list)
    file_to_functions = defaultdict(set)

    # Walk through all Python files
    for py_file in sorted(geetools_dir.glob("*.py")):
        analyzer = analyze_file(py_file)

        if analyzer and analyzer.functions_with_ee_extra:
            functions = set(analyzer.functions_with_ee_extra)
            file_to_functions[py_file.name] = functions

            for call_info in analyzer.ee_extra_calls:
                func_name = call_info["function"]
                call = call_info["call"]
                all_dependencies[py_file.name].append({"function": func_name, "call": call})

    # Generate report
    output_file = Path("/home/rambap/github/geetools/ee_extra_dependencies.txt")

    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("EE_EXTRA DEPENDENCIES IN GEETOOLS\n")
        f.write("=" * 80 + "\n")
        f.write("Analysis Date: 2026-07-15\n")
        f.write(f"Total files with ee_extra dependencies: {len(file_to_functions)}\n")

        # Count total unique functions
        all_functions = set()
        for functions in file_to_functions.values():
            all_functions.update(functions)

        f.write(f"Total unique functions with ee_extra dependencies: {len(all_functions)}\n\n")

        # Detailed report by file
        f.write("=" * 80 + "\n")
        f.write("DETAILED BREAKDOWN BY FILE\n")
        f.write("=" * 80 + "\n\n")

        for file_name in sorted(file_to_functions.keys()):
            functions = sorted(file_to_functions[file_name])
            f.write(f"\nFile: {file_name}\n")
            f.write(f"  Functions with ee_extra dependencies ({len(functions)}):\n")

            for func in functions:
                f.write(f"    - {func}\n")

            # Show ee_extra calls for this file
            f.write("\n  ee_extra Method Calls:\n")
            seen_calls = set()
            for dep_info in all_dependencies[file_name]:
                call = dep_info["call"]
                if call not in seen_calls:
                    f.write(f"    - {call}\n")
                    seen_calls.add(call)
            f.write("\n")

        # Summary list of all functions
        f.write("\n" + "=" * 80 + "\n")
        f.write("SUMMARY: ALL FUNCTIONS WITH EE_EXTRA DEPENDENCIES\n")
        f.write("=" * 80 + "\n\n")

        for func_name in sorted(all_functions):
            # Find which file this function is in
            for file_name, functions in file_to_functions.items():
                if func_name in functions:
                    f.write(f"{func_name} (in {file_name})\n")
                    break

    print("\n✓ Analysis complete!")
    print(f"✓ Results written to: {output_file}")
    print("\nSummary:")
    print(f"  - Files with ee_extra dependencies: {len(file_to_functions)}")
    print(f"  - Total unique functions: {len(all_functions)}")
    print(f"  - Total ee_extra calls: {len([d for deps in all_dependencies.values() for d in deps])}")

    # Print to console as well
    print("\nFunctions with ee_extra dependencies:")
    for file_name in sorted(file_to_functions.keys()):
        functions = sorted(file_to_functions[file_name])
        print(f"\n{file_name}:")
        for func in functions:
            print(f"  - {func}")


if __name__ == "__main__":
    main()
