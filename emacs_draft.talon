emacs [draft] submit: user.emacs_draft_submit()
emacs edit clipboard: user.emacs_draft_clipboard()

emacs [{user.emacs_draft_copy_or_cut}] edit that:
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
emacs [{user.emacs_draft_copy_or_cut}] edit line:
  edit.select_line()
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
emacs [{user.emacs_draft_copy_or_cut}] edit all:
  edit.select_all()
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
