import sys
import io
import contextlib


@contextlib.contextmanager
def capture_output():
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err


def execute_generated_code(
    code_str: str, globals_dict: dict = None, locals_dict: dict = None
):
    """
    Executes a string of Python code and captures the output.
    Returns (stdout, stderr, exception_if_any).
    """
    if globals_dict is None:
        globals_dict = {}
    if locals_dict is None:
        locals_dict = {}

    stdout_val = ""
    stderr_val = ""
    exception_val = None

    with capture_output() as (out, err):
        try:
            exec(code_str, globals_dict, locals_dict)
        except Exception as e:
            exception_val = e
            # Print traceback to stderr captured string
            import traceback

            traceback.print_exc(file=err)

    stdout_val = out.getvalue()
    stderr_val = err.getvalue()

    return stdout_val, stderr_val, exception_val
