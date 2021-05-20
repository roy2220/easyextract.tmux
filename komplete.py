import argparse
import itertools
import os
import re
import shlex
import subprocess
import sys
import tempfile
import typing


def parse_args() -> None:
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--delimiters")
    arg_parser.add_argument("--height")

    class Args(argparse.Namespace):
        def __init__(self):
            self.delimiters = ""
            self.height = ""

    args = arg_parser.parse_args(sys.argv[1:], namespace=Args())

    global DELIMITERS, HEIGHT
    DELIMITERS = args.delimiters or "- . @ : / ,"
    HEIGHT = int(args.height or "10")


parse_args()


def get_words() -> typing.List[str]:
    # words1
    screen = _run_tmux_command("capture-pane", "-p")
    words1 = set(screen.split("\n"))
    # words2
    pattern2 = re.compile(r"\s+")
    words2 = set()
    for word in words1:
        words2.update(pattern2.split(word))
    # words3
    delimiters = set(
        re.escape(word_delimiter) for word_delimiter in re.split(r"\s+", DELIMITERS)
    )
    words3 = set()
    for n in range(0, len(delimiters) + 1):
        for sub_delimiters in itertools.combinations(delimiters, n):
            pattern3 = re.compile(r"[_a-zA-Z0-9{}]+".format("".join(sub_delimiters)))
            for word in words2:
                words3.update(pattern3.findall(word))
    # words4
    pattern4 = re.compile(r"[a-zA-Z]+|[0-9]+")
    words4 = set()
    for word in words3:
        words4.update(pattern4.findall(word))
    # words5
    words5 = words1.union(words2).union(words3).union(words4)
    words5.remove("")
    return list(words5)


def select_and_send_word(words: typing.List[str]) -> None:
    script_file_name = _generate_script_file(words)
    _run_tmux_command(
        "set-window-option",
        "synchronize-panes",
        "off",
        ";",
        "set-window-option",
        "remain-on-exit",
        "off",
        ";",
        "split-window",
        "-l",
        str(HEIGHT),
        "bash",
        script_file_name,
    )


def _generate_script_file(words: typing.List[str]) -> str:
    fzf_default_opts = os.environ.get("FZF_DEFAULT_OPTS", "")
    fzf_default_command = os.environ.get("FZF_DEFAULT_COMMAND", "")
    pane_id = _get_tmux_vars("pane_id")["pane_id"]
    script = """
trap 'rm "${{0}}"' EXIT
WORD=$(FZF_DEFAULT_OPTS={fzf_default_opts} FZF_DEFAULT_COMMAND={fzf_default_command} fzf --no-height --bind=ctrl-z:ignore <<< {words})
if [[ -z ${{WORD}} ]]; then
    exit
fi
tmux send-keys -t {pane_id} -l -- "${{WORD}}"
""".format(
        fzf_default_opts=shlex.quote(fzf_default_opts),
        fzf_default_command=shlex.quote(fzf_default_command),
        words=shlex.quote("\n".join(words)),
        pane_id=shlex.quote(pane_id),
    )
    script_file_name = tempfile.mktemp()
    with open(script_file_name, "w") as f:
        f.write(script)
    return script_file_name


def _get_tmux_vars(*tmux_var_names: str) -> typing.Dict[str, str]:
    result = _run_tmux_command(
        "display-message", "-p", "\n".join("#{%s}" % s for s in tmux_var_names)
    )
    tmux_var_values = result.split("\n")
    tmux_vars = dict(zip(tmux_var_names, tmux_var_values))
    return tmux_vars


def _run_tmux_command(*args: str) -> str:
    proc = subprocess.run(("tmux", *args), check=True, capture_output=True)
    result = proc.stdout.decode()[:-1]
    return result


def main() -> None:
    words = get_words()
    select_and_send_word(words)


main()
