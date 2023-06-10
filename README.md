# easyextract.tmux

`easyextract.tmux` extracts words from the screen

## Requirements

- Tmux >= 3.0
- Python >= 3.8
- Bash
- [FZF](https://github.com/junegunn/fzf)

## Installation

- [TPM](https://github.com/tmux-plugins/tpm)

  1. Add to `~/.tmux.conf`:

     ```tmux
     set-option -g @plugin "roy2220/easyextract.tmux"
     ```

  2. Press `prefix` + <kbd>I</kbd> to install the plugin.

- Manual

  1. Fetch the source:

     ```sh
     git clone https://github.com/roy2220/easyextract.tmux.git /PATH/TO/DIR
     ```

  2. Add to `~/.tmux.conf`:

     ```tmux
     run-shell "/PATH/TO/DIR/easyextract.tmux"
     ```

  3. Reload Tmux configuration:

     ```sh
     tmux source ~/.tmux.conf
     ```

## Usage

- Press `prefix` + <kbd>e</kbd> to extract a word from the screen.
- Press <kbd>Ctrl</kbd> + <kbd>e</kbd> to extract a word from the screen in `copy mode`.
- Press <kbd>Escape</kbd> to quit.

## Configuration

defaults:

```tmux
set-option -g @easyextract-key-binding "e"
set-option -g @easyextract-delimiters "- . @ : / , #"
set-option -g @easyextract-width "0.38"
set-option -g @easyextract-height "0.38"
```
