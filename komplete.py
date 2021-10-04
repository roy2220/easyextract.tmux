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
    arg_parser.add_argument("--width")
    arg_parser.add_argument("--height")

    class Args(argparse.Namespace):
        def __init__(self):
            self.delimiters = ""
            self.width = ""
            self.height = ""

    args = arg_parser.parse_args(sys.argv[1:], namespace=Args())

    global DELIMITERS, WIDTH, HEIGHT
    DELIMITERS = args.delimiters or "- . @ : / , #"
    WIDTH = float(args.width or "0.62")
    HEIGHT = float(args.height or "10")


parse_args()


def get_tmux_vars(*tmux_var_names: str) -> typing.Dict[str, str]:
    result = _run_tmux_command(
        "display-message", "-p", "\n".join("#{%s}" % s for s in tmux_var_names)
    )
    tmux_var_values = result.split("\n")
    tmux_vars = dict(zip(tmux_var_names, tmux_var_values))
    return tmux_vars


def get_words(tmux_vars: typing.Dict[str, str]) -> typing.List[str]:
    screen = _capture_screen(tmux_vars)
    # words0
    words0 = set(screen.splitlines())
    words1 = set(words0)
    for raw_pattern in (
        r'"((?:\\"|[^"])*)"',
        r"'((?:\\'|[^'])*)'",
        r"<((?:\\<|\\>|[^<>])*)>",
        r"\[((?:\\\[|\\\]|[^\[\]])*)\]",
        r"\{((?:\\\{|\\\}|[^\{\}])*)\}",
        r"\(((?:\\\(|\\\)|[^\(\)])*)\)",
    ):
        pattern1 = re.compile(raw_pattern)
        for word in words0:
            for match in pattern1.finditer(word):
                words1.add(match.group())
                words1.add(match.groups()[0])
    # words2
    pattern2 = re.compile(r"\s+")
    words2 = set()
    for word in words1:
        words2.update(pattern2.split(word))
    # words3
    delimiters = set(
        re.escape(str(delimiter)) for delimiter in re.split(r"\s+", DELIMITERS)
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
    words5.discard("")
    return list(words5)


def _capture_screen(tmux_vars: typing.Dict[str, str]) -> str:
    pane_id = tmux_vars["pane_id"]
    args = ["capture-pane", "-t", pane_id]
    scroll_position = tmux_vars["scroll_position"]
    if scroll_position != "":
        start_line_number = -int(scroll_position)
        pane_height = int(tmux_vars["pane_height"])
        end_line_number = start_line_number + pane_height - 1
        args.extend(("-S", str(start_line_number), "-E", str(end_line_number)))
    args.append("-p")
    pane_ids = _run_tmux_command("list-panes", "-F", "#{pane_id}").splitlines()
    for pane_id2 in pane_ids:
        if pane_id2 == pane_id:
            continue
        args.extend((";", "capture-pane", "-t", pane_id2, "-p"))
    screen = _run_tmux_command(*args)
    return screen


def select_and_send_word(
    words: typing.List[str], tmux_vars: typing.Dict[str, str]
) -> None:
    match = re.match(r"^(\d+).(\d+)", tmux_vars["version"])
    assert match is not None
    version = int(match.group(1)), int(match.group(2))
    if version < (3, 2):
        pane_id = tmux_vars["pane_id"]
        args = [
            "set-window-option",
            "synchronize-panes",
            "off",
            ";",
            "set-window-option",
            "remain-on-exit",
            "off",
            ";",
            "split-window",
            "-t",
            pane_id,
        ]
        if HEIGHT < 1:
            args.extend(("-p", str(int(100 * HEIGHT))))
        else:
            args.extend(("-l", str(int(HEIGHT))))
        script = _generate_script(words, tmux_vars)
    else:
        args = [
            "display-popup",
            "-E",
        ]
        args.append("-w")
        if WIDTH < 1:
            args.append(str(int(100 * WIDTH)) + "%")
        else:
            args.append(str(int(WIDTH)))
        args.append("-h")
        if HEIGHT < 1:
            args.append(str(int(100 * HEIGHT)) + "%")
        else:
            args.append(str(int(HEIGHT)))
        script = _generate_script_2(words, tmux_vars)
    script_file_name = tempfile.mktemp()
    with open(script_file_name, "w") as f:
        f.write(script)
    args.extend(("bash", script_file_name))
    _run_tmux_command(*args)


def _generate_script(words: typing.List[str], tmux_vars: typing.Dict[str, str]) -> str:
    pane_id = tmux_vars["pane_id"]
    scroll_position = tmux_vars["scroll_position"]
    history_size = tmux_vars["history_size"]
    fzf_default_opts = os.environ.get("FZF_DEFAULT_OPTS", "")
    fzf_default_command = os.environ.get("FZF_DEFAULT_COMMAND", "")
    in_copy_mode = scroll_position != ""
    script = """\
trap 'rm "${{0}}"' EXIT
[[ -z {in_copy_mode} ]] && tmux copy-mode -t {pane_id}
HISTORY_SIZE=$(tmux display-message -t {pane_id} -p '#{{history_size}}')
HISTORY_SIZE_DELTA=$((${{HISTORY_SIZE}} - {history_size}))
[[ ${{HISTORY_SIZE_DELTA}} -ne 0 ]] && tmux send-keys -t {pane_id} -X goto-line "$(({scroll_position} + ${{HISTORY_SIZE_DELTA}}))"
WORD=$(FZF_DEFAULT_OPTS={fzf_default_opts} FZF_DEFAULT_COMMAND={fzf_default_command} fzf --prompt='Word> ' --no-height --bind=ctrl-z:ignore <<< {words})
if [[ -z ${{WORD}} ]]; then
    if [[ -z {in_copy_mode} ]]; then
        tmux send-keys -t {pane_id} -X cancel
    else
        [[ ${{HISTORY_SIZE_DELTA}} -ne 0 ]] && tmux send-keys -t {pane_id} -X goto-line {scroll_position}
    fi
    exit
fi
tmux send-keys -t {pane_id} -X cancel\\; send-keys -t {pane_id} -l -- "${{WORD}}"
""".format(
        pane_id=shlex.quote(pane_id),
        scroll_position=shlex.quote(scroll_position or "0"),
        history_size=shlex.quote(history_size),
        fzf_default_opts=shlex.quote(fzf_default_opts),
        fzf_default_command=shlex.quote(fzf_default_command),
        words=shlex.quote("\n".join(words)),
        in_copy_mode=shlex.quote("1" if in_copy_mode else ""),
    )
    return script


def _generate_script_2(
    words: typing.List[str], tmux_vars: typing.Dict[str, str]
) -> str:
    pane_id = tmux_vars["pane_id"]
    scroll_position = tmux_vars["scroll_position"]
    fzf_default_opts = os.environ.get("FZF_DEFAULT_OPTS", "")
    fzf_default_command = os.environ.get("FZF_DEFAULT_COMMAND", "")
    in_copy_mode = scroll_position != ""
    script = """\
trap 'rm "${{0}}"' EXIT
WORD=$(FZF_DEFAULT_OPTS={fzf_default_opts} FZF_DEFAULT_COMMAND={fzf_default_command} fzf --prompt='Word> ' --no-height --bind=ctrl-z:ignore <<< {words})
if [[ -z ${{WORD}} ]]; then
    exit
fi
if [[ -z {in_copy_mode} ]]; then
    tmux send-keys -t {pane_id} -l -- "${{WORD}}"
else
    tmux send-keys -t {pane_id} -X cancel\\; send-keys -t {pane_id} -l -- "${{WORD}}"
fi
""".format(
        pane_id=shlex.quote(pane_id),
        fzf_default_opts=shlex.quote(fzf_default_opts),
        fzf_default_command=shlex.quote(fzf_default_command),
        words=shlex.quote("\n".join(words)),
        in_copy_mode=shlex.quote("1" if in_copy_mode else ""),
    )
    return script


def _run_tmux_command(*args: str) -> str:
    proc = subprocess.run(("tmux", *args), check=True, capture_output=True)
    result = proc.stdout.decode()[:-1]
    return result


def main() -> None:
    tmux_vars = get_tmux_vars(
        "pane_id",
        "pane_height",
        "scroll_position",
        "history_size",
        "version",
    )
    words = get_words(tmux_vars)
    select_and_send_word(words, tmux_vars)


main()
