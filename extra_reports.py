from contextlib import contextmanager
import tokenize

import autopep8
import pycodestyle

DEFAULT_INDENT_SIZE = autopep8.DEFAULT_INDENT_SIZE

def unregister_check(check_callable):
    if check_callable in pycodestyle._checks['logical_line']:
        del pycodestyle._checks['logical_line'][check_callable]

def report_e123_on_double_default_indent_size(
    logical_line, tokens, indent_level, hang_closing,
    indent_char, noqa,
):
    """Report (and later fix) E123 when indentation match 2 * default_indent (4).

    By default pycodestyle and autopep8 does not report E123 when indentation match
    2 * default_indent.
    """

    first_row = tokens[0][2][0]
    nrows = 1 + tokens[-1][2][0] - first_row
    if noqa or nrows == 1:
        return

    row = depth = 0
    valid_hangs = (
        (DEFAULT_INDENT_SIZE,)
        if indent_char != '\t' else (
            DEFAULT_INDENT_SIZE,
            2 * DEFAULT_INDENT_SIZE,
        )
    )

    # Relative indents of physical lines.
    rel_indent = [0] * nrows

    # For each depth, collect a list of opening rows.
    open_rows = [[0]]
    # For each depth, memorize the hanging indentation.
    hangs = [None]

    last_token_multiline = None
    line = None
    hang = 0
    for token_type, text, start, end, line in tokens:

        newline = row < start[0] - first_row
        if newline:
            row = start[0] - first_row
            newline = (
                not last_token_multiline and
                token_type not in (tokenize.NL, tokenize.NEWLINE)
            )

        if newline:
            # Record the initial indent.
            rel_indent[row] = pycodestyle.expand_indent(line) - indent_level

            # Is the indent relative to an opening bracket line?
            for open_row in reversed(open_rows[depth]):
                hang = rel_indent[row] - rel_indent[open_row]
                hanging_indent = hang in valid_hangs
                if hanging_indent:
                    break
            if hangs[depth]:
                hanging_indent = (hang == hangs[depth])

            if rel_indent[row] == 2 * DEFAULT_INDENT_SIZE:
                # TODO: this should be reported only for function calls
                yield (start, 'E123 {}'.format(2 * DEFAULT_INDENT_SIZE))



@contextmanager
def enable_check(check_callable):
    """Temporary enable pycodestyle check."""

    if check_callable is not None:
        pycodestyle.register_check(check_callable)
    yield
    if check_callable is not None:
        unregister_check(check_callable)
