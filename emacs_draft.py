from talon import ui, Context, Module, actions, clip, app
import subprocess

mod = Module()
ctx = Context()

setting_copy_or_cut = mod.setting(
    "emacs_draft_copy_or_cut",
    type=str,
    desc="Whether to copy or cut stuff sent to emacs for editing by default.",
    default="cut")

mod.list("emacs_draft_copy_or_cut",
         desc="Whether to copy or cut stuff sent to emacs for editing.")
ctx.lists["user.emacs_draft_copy_or_cut"] = ["copy", "cut"]

# window from which `emacs edit` was invoked
source_window = None

# `xsel` seems to work more reliably than Emacs' built in clipboard commands. :(
# Prefer it, but fall back on e.g. Windows with an additional 0.5s delay.
# TODO: is the delay necessary?
lisp_submit_draft = '''
(with-current-buffer "*Draft*"
  (if (executable-find "xsel")
      (shell-command-on-region (point-min) (point-max) "xsel -ib")
    (gui-select-text (buffer-substring-no-properties (point-min) (point-max)))
    (sleep-for 0.5))
  (bury-buffer))
'''

lisp_edit_empty = """
(with-current-buffer (switch-to-buffer "*Draft*")
  (kill-region (point-min) (point-max)))
"""

lisp_edit_clipboard = '''
(with-current-buffer (switch-to-buffer "*Draft*")
  (goto-char (point-min))
  (clipboard-yank)
  (kill-region (point) (point-max)))
'''

@mod.action_class
class ModuleActions:
    def emacs_draft_run(lisp_code: str):
        """Focus an emacs window (optionally creating it) and run the given emacs lisp code in it."""
        # If there's an emacs window on the current workspace, reuse it;
        # otherwise, create one.
        reuse_window = False
        try: # in case emacs is not running, or talon doesn't support workspace API
            emacs = actions.user.get_running_app("Emacs")
            current_workspace = ui.active_workspace()
            reuse_window = emacs and any(w.workspace == current_workspace
                                         for w in emacs.windows())
        except: pass
        if not reuse_window:
            ui.launch(path='emacsclient', args=['-ca', '', '-e', lisp_code])
            actions.sleep("400ms")
        actions.user.switcher_focus("Emacs")
        if reuse_window:
            ui.launch(path='emacsclient', args=['-e', lisp_code])

    def emacs_draft_show():
        """Opens the emacs draft buffer."""
        actions.user.emacs_draft_run('(switch-to-buffer "*Draft*")')

    def emacs_draft_empty():
        """Open an empty emacs draft buffer."""
        actions.user.emacs_draft_run(lisp_edit_empty)

    def emacs_draft_clipboard():
        """Focus or create an appropriate emacs window, switch to the draft buffer, and update it to clipboard contents."""
        actions.user.emacs_draft_run(lisp_edit_clipboard)

    def emacs_draft_selection(copy_or_cut: str = "default"):
        """Open an emacs draft buffer editing the current selection."""
        assert copy_or_cut in ["copy", "cut", "default"]
        if copy_or_cut == "default": copy_or_cut = setting_copy_or_cut.get()
        assert copy_or_cut in ["copy", "cut"]
        global source_window
        source_window = ui.active_window()
        clip.set_text("")
        actions.edit.copy() if copy_or_cut == "copy" else actions.edit.cut()
        clip.await_change(old="")
        #print(f"***** clip.text() = {clip.text()!r} *****")
        if clip.text(): actions.user.emacs_draft_clipboard()
        else: actions.user.emacs_draft_empty()

    def emacs_draft_submit():
        """Submit the contents of the draft buffer."""
        # If we are in emacs, we want to focus source_window and paste in the
        # contents of the draft buffer. Otherwise, we want to paste the contents
        # of the draft buffer.
        try: in_emacs = ui.active_window().app == actions.user.get_running_app("Emacs")
        except: in_emacs = False
        if in_emacs:
            if source_window not in ui.windows():
                message = ("Don't know what window to submit to!"
                           if source_window is None else
                           "Window to submit to no longer exists!")
                app.notify(title="emacs_draft.py", body=message)
                raise ValueError(message)
            source_window.focus()
            # maybe use the contents of the current buffer instead?

        clip.clear()
        ui.launch(path="emacsclient", args=['-e', lisp_submit_draft])
        #print(f"********** before clip.text() = {clip.text()!r} **********")
        clip.await_change(timeout=0.5, old="")
        #print(f"********** after  clip.text() = {clip.text()!r} **********")
        actions.edit.paste()
