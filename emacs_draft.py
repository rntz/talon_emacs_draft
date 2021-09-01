from talon import ui, Context, Module, actions, clip
import subprocess

mod = Module()
ctx = Context()

setting_copy_or_cut = mod.setting(
    "emacs_draft_copy_or_cut",
    type=str,
    desc="Whether to copy or cut by default",
    default="cut")

mod.list("emacs_draft_copy_or_cut",
         desc="Whether to copy or cut stuff sent to emacs for editing.")
ctx.lists["user.emacs_draft_copy_or_cut"] = ["copy", "cut"]

# window from which `emacs edit` was invoked
source_window = None

# lisp_copy_draft = '''
# (with-current-buffer "*Draft*"
#   (gui-set-selection 'CLIPBOARD (buffer-substring-no-properties (point-min) (point-max))))
# '''

# This seems to work more reliably than emacs' built in clipboard commands. :(
lisp_copy_draft = '''
(with-current-buffer "*Draft*"
  (shell-command-on-region (point-min) (point-max) "xsel -ib"))
'''

lisp_edit_clipboard = '''
(with-current-buffer (switch-to-buffer "*Draft*")
  (goto-char (point-min))
  (clipboard-yank)
  (kill-region (point) (point-max)))
'''

@mod.action_class
class ModuleActions:
    def emacs_draft_clipboard():
        """Focus or create an appropriate emacs window, switch to the draft buffer, and update it to clipboard contents."""
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
            # Make a new emacs window editing clipboard.
            ui.launch(path='emacsclient', args=['-nca', '', '-e', lisp_edit_clipboard])
            actions.sleep("400ms")
        actions.user.switcher_focus("Emacs")
        if reuse_window:
            # Tell the focused window to edit the clipboard.
            ui.launch(path='emacsclient', args=['-e', lisp_edit_clipboard])

    def emacs_draft_selection(copy_or_cut: str = "default"):
        """Open an emacs draft buffer editing the current selection."""
        assert copy_or_cut in ["copy", "cut", "default"]
        if copy_or_cut == "default": copy_or_cut = setting_copy_or_cut.get()
        global source_window
        source_window = ui.active_window()
        clip.set_text("")
        actions.edit.copy() if copy_or_cut == "copy" else actions.edit.cut()
        clip.await_change(old="")
        actions.user.emacs_draft_clipboard()

    def emacs_draft_submit():
        """Submit the contents of the draft buffer."""
        # If we are in emacs, we want to focus source_window and paste in the
        # contents of the current(?) buffer. Otherwise, we want to paste the
        # contents of the draft buffer.
        try: in_emacs = ui.active_window().app == actions.user.get_running_app("Emacs")
        except: in_emacs = False
        if in_emacs:
            if source_window is None:
                raise ValueError("no source window")
            elif source_window not in ui.windows():
                raise ValueError("window no longer exists")
            else:
                source_window.focus()
                # maybe we should use the contents of the current buffer?

        clip.clear()
        ui.launch(path="emacsclient", args=['-e', lisp_copy_draft])
        #print(f"********** before clip.text() = {clip.text()!r} **********")
        clip.await_change(timeout=0.5, old="")
        # actions.sleep("200ms")
        #print(f"********** after  clip.text() = {clip.text()!r} **********")
        actions.edit.paste()
