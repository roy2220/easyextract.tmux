# komplete.tmux

`komplete.tmux` extracts words from the screen

## Requirements

- Tmux >= 3.1
- Python >= 3.8
- Bash
- [FZF](https://github.com/junegunn/fzf)

## Installation

- [TPM](https://github.com/tmux-plugins/tpm)

  1. Add to `~/.tmux.conf`:

     ```tmux
     set-option -g @plugin "roy2220/komplete.tmux"
     ```

  2. Press `prefix` + <kbd>I</kbd> to install the plugin.

- Manual

  1. Fetch the source:

     ```sh
     git clone https://github.com/roy2220/komplete.tmux.git /PATH/TO/DIR
     ```

  2. Add to `~/.tmux.conf`:

     ```tmux
     run-shell "/PATH/TO/DIR/komplete.tmux"
     ```

  3. Reload Tmux configuration:

     ```sh
     tmux source ~/.tmux.conf
     ```

## Usage

- Press `prefix` + <kbd>k</kbd> to extract a word from the screen.

## Configuration

defaults:

```tmux
set-option -g @komplete-key-binding "k"
set-option -g @komplete-delimiters "- . @ : / ,"
set-option -g @komplete-height "10"
```
