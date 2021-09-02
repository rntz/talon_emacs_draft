emacs draft show: user.emacs_draft_show()
emacs draft empty: user.emacs_draft_empty()
emacs [draft] submit: user.emacs_draft_submit()

emacs edit clipboard: user.emacs_draft_clipboard()
emacs edit [{user.emacs_draft_copy_or_cut}] (this|that):
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
emacs edit [{user.emacs_draft_copy_or_cut}] line:
  edit.select_line()
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
emacs edit [{user.emacs_draft_copy_or_cut}] all:
  edit.select_all()
  user.emacs_draft_selection(emacs_draft_copy_or_cut or "default")
