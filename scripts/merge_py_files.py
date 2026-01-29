from __future__ import annotations
import argparse
import ast
import os
import re
from pathlib import Path
from typing import List, Tuple, Dict


def safe_name(path: Path) -> str:
    # create a valid Python identifier from path
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", str(path.with_suffix("")))
    name = name.strip("_")
    if not name:
        name = "module"
    # ensure it doesn't start with digit
    if name[0].isdigit():
        name = "_" + name
    return name


def read_file_lines(path: Path) -> List[str]:
    with path.open("r", encoding="utf-8") as f:
        return f.read().splitlines()


def get_source_segment(lines: List[str], node: ast.AST) -> str:
    # ast nodes have lineno and end_lineno (1-based)
    start = getattr(node, "lineno", None)
    end = getattr(node, "end_lineno", None)
    if start is None or end is None:
        return ""
    # slice lines (inclusive)
    seg = lines[start - 1 : end]
    return "\n".join(seg)


def is_docstring_expr(node: ast.Expr) -> bool:
    return isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)


def find_main_if(node: ast.If) -> bool:
    # detect: if __name__ == "__main__" (allow simple variants)
    try:
        left = (
            node.test.left
            if isinstance(node.test, ast.Compare) and node.test.left
            else node.test
        )
    except Exception:
        left = None
    # We'll use textual check on source if AST variant is complicated
    # But simple check:
    if isinstance(node.test, ast.Compare):
        # patterns: __name__ == '__main__' or '__main__' == __name__
        for comp in [node.test.left] + node.test.comparators:
            if isinstance(comp, ast.Name) and comp.id == "__name__":
                # presence of string in the other side is a good signal
                for other in node.test.comparators + [node.test.left]:
                    if isinstance(other, ast.Constant) and other.value == "__main__":
                        return True
    return False


def process_file(path: Path) -> Dict:
    lines = read_file_lines(path)
    src = "\n".join(lines) + "\n"
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        raise SyntaxError(f"Failed to parse {path}: {e}")

    imports: List[str] = []
    module_level: List[str] = []
    exec_block: List[str] = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            seg = get_source_segment(lines, node).strip()
            if seg:
                imports.append(seg)
            continue

        # Detect and extract if __name__ == '__main__'
        if isinstance(node, ast.If) and find_main_if(node):
            # extract body into exec_block
            for sub in node.body:
                seg = get_source_segment(lines, sub)
                if seg:
                    exec_block.append(seg)
            # also consider else/elif? skip for now
            continue

        # Keep docstring as module-level if at top
        if isinstance(node, ast.Expr) and is_docstring_expr(node):
            seg = get_source_segment(lines, node)
            if seg:
                module_level.append(seg)
            continue

        # Keep definitions and assignments at top-level
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
                ast.Assign,
                ast.AnnAssign,
            ),
        ):
            seg = get_source_segment(lines, node)
            if seg:
                module_level.append(seg)
            continue

        # For other statements (loops, if, exprs), treat as executable
        seg = get_source_segment(lines, node)
        if seg:
            exec_block.append(seg)

    return {
        "path": str(path),
        "imports": imports,
        "module_level": module_level,
        "exec_block": exec_block,
    }


def merge(src_dir: Path, out_file: Path, exclude: List[str] = None) -> None:
    exclude = exclude or []
    py_files: List[Path] = []

    for root, dirs, files in os.walk(src_dir):
        # skip excluded directories
        if any(ex in root for ex in exclude):
            continue
        for f in files:
            if f.endswith(".py"):
                full = Path(root) / f
                # skip this script itself if in src
                if full.resolve() == Path(__file__).resolve():
                    continue
                py_files.append(full)

    py_files = sorted(py_files)

    all_imports: List[str] = []
    files_data: List[Dict] = []

    for p in py_files:
        try:
            info = process_file(p)
        except SyntaxError as e:
            print(f"Warning: skipping {p} ({e})")
            continue

        files_data.append(info)
        all_imports.extend(info["imports"])

    # Deduplicate imports while preserving order
    seen = set()
    unique_imports = []
    for imp in all_imports:
        key = imp.strip()
        if key not in seen:
            seen.add(key)
            unique_imports.append(key)

    # Build combined content
    out_lines: List[str] = []
    out_lines.append("# Auto-generated combined Python file")
    out_lines.append("# Source directory: " + str(src_dir))
    out_lines.append("# Note: original files are not modified")
    out_lines.append("\n")

    # Write imports
    if unique_imports:
        out_lines.append("# --- Consolidated imports ---")
        out_lines.extend(unique_imports)
        out_lines.append("\n")

    runner_names: List[str] = []

    for idx, info in enumerate(files_data, start=1):
        p = Path(info["path"])
        name = safe_name(p)
        runner = f"_run_{name}"
        runner_names.append(runner)

        out_lines.append(f"# === File: {p.relative_to(src_dir)} ===")

        if info["module_level"]:
            out_lines.append(
                "\n# -- module-level definitions (functions/classes/assigns) --"
            )
            out_lines.extend(info["module_level"])
            out_lines.append("\n")

        # Add run function which contains executable blocks
        out_lines.append(f"def {runner}():")
        if info["exec_block"]:
            for seg in info["exec_block"]:
                # indent each line
                for line in seg.splitlines():
                    out_lines.append("    " + line)
            out_lines.append("\n")
        else:
            out_lines.append("    pass\n")

    # Add master main that calls each runner in order
    out_lines.append("\n# --- Runner ---")
    out_lines.append("def main():")
    out_lines.append(
        '    """Execute top-level code blocks from source files in traversal order."""'
    )
    for r in runner_names:
        out_lines.append(f"    try:")
        out_lines.append(f"        {r}()")
        out_lines.append(f"    except Exception as e:")
        out_lines.append(f"        print('Error running {r}:', e)")
    out_lines.append("\n")
    out_lines.append("if __name__ == '__main__':")
    out_lines.append("    main()")

    # Write to disk
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")

    print(f"Combined {len(files_data)} files into: {out_file}")


def parse_args():
    p = argparse.ArgumentParser(
        description="Merge .py files into a single combined file"
    )
    p.add_argument(
        "--src",
        "-s",
        type=str,
        default=".",
        help="Source directory to search for .py files",
    )
    p.add_argument(
        "--out", "-o", type=str, default="combined_all.py", help="Output combined file"
    )
    p.add_argument(
        "--exclude",
        "-x",
        type=str,
        nargs="*",
        default=[".git", "__pycache__", "venv", "env", "outputs"],
        help="Directories to exclude",
    )
    return p.parse_args()


def main_cli():
    args = parse_args()
    src_dir = Path(args.src).resolve()
    out_file = Path(args.out).resolve()
    merge(src_dir, out_file, exclude=args.exclude)


if __name__ == "__main__":
    main_cli()
