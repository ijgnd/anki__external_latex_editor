# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl.html
# Copyright: github.com/pointtonull 
#            ijgnd
#            Damien Elmes


from anki.hooks import wrap, addHook
from anki.utils import (
    stripHTML,
)
from aqt import mw
from aqt.editor import Editor
from aqt.utils import tooltip

from .config import gc
from .helper import adjust_text_to_html
from .process_string_in_texteditor import edit_string_externally_and_return_mod

from . import js


BUILTIN_EDITOR = Editor._onHtmlEdit
unique_before = "1bf51ff22102480f9948d78d54b034ca"  # random/uuuid
unique_after = "b3f7849150d940d094df6391089ad135"  # random/uuuid


def set_field_to_text(self, field, text):
    self.note.fields[field] = text
    if not self.addMode:
        self.note.flush()
    self.loadNote(focusTo=field)


def edit_with_external_editor(self, field):
    if not gc("replace built-in anki html editor"):
        return BUILTIN_EDITOR(self, field)
    text = self.note.fields[field]
    try:
        text = edit_string_externally_and_return_mod(text)
    except RuntimeError:
        return BUILTIN_EDITOR(self, field)
    else:
        set_field_to_text(self, field, text)
Editor._onHtmlEdit = edit_with_external_editor








def sel_to_external_editor(note, selected, block=False, lang=None):
    # if not selected:
    #     tooltip("no text selected.")
    #     return
    selected = selected.replace(" ", " ")  # remove nbsp;
    if not lang:
        fldname = gc("file extension from field")
        if not fldname:
            tooltip("value missing from config")
            return
        for fname, fcont in note.items():
            if fname == fldname:
                lang = stripHTML(fcont)
        if not lang:
            for t in note.tags:
                for k, v in gc("tags to file ending", {}).items():
                    for l in v:
                        if t == l:
                            lang = k
                            break 
    if lang is None:
        tooltip("no language set. no relevant field or tag found.")
        return
    fn = gc("custom_files_for_langs", {}).get(lang)
    suf = "Irrelevant" if fn else f".{lang}"
    try:
        text = edit_string_externally_and_return_mod(selected, filename=fn, block=block, suffix=suf)
    except RuntimeError:
        tooltip('Error when trying to edit externally')
        return
    if block:
        return text


def reviewer_helper():
    selected = mw.reviewer.web.page().selectedText().strip()
    note = mw.reviewer.card.note()
    sel_to_external_editor(note, selected, block=False, lang=None)


def reviewerShortcuts(cuts):
    cut = gc("shortcut reviewer to open selection in text editor")
    if cut:
        cuts.append((cut, reviewer_helper))
addHook("reviewStateShortcuts", reviewerShortcuts)


def ReviewerContextMenu(view, menu):
    if mw.state != "review":
        return
    menutext = "open selection in text editor"
    cut = gc("shortcut reviewer to open selection in text editor")
    if cut:
        menutext += f" (shortcut: {cut})"
    a = menu.addAction(menutext)
    a.triggered.connect(reviewer_helper)
addHook("AnkiWebView.contextMenuEvent", ReviewerContextMenu)






def __editor_helper(self, saveback):
    lang=gc("editor field content and save back file extension") if saveback else None
    if saveback:
        fieldcontent = self.note.fields[thefield]
        if fieldcontent.count(unique_before) > 1 or fieldcontent.count(unique_after) > 1:
            tooltip("Aborting. helper strings too often in text field.")
            set_field_to_text(self, thefield, oldcontent)  # restore old content
            return
        before, rest = fieldcontent.split(unique_before)
        selection, after = rest.split(unique_after)
        stripped = stripHTML(selection)
    else:
        stripped = self.web.selectedText()
    out = sel_to_external_editor(self.note, stripped, block=saveback, lang=lang)
    if saveback:
        if out:
            new = before + adjust_text_to_html(out) + after
        else:  # restore old content, remove temporary insertion
            new = oldcontent
        set_field_to_text(self, thefield, new)


def _editor_helper(self, saveback): 
    self.saveNow(lambda e=self, s=saveback: __editor_helper(e, s))


def editor_helper(self, saveback):
    global thefield
    thefield = self.currentField
    if not saveback:
        self.saveNow(lambda e=self, s=saveback: __editor_helper(e, s))
    else:
        global oldcontent
        oldcontent = self.note.fields[thefield]
        jsf = f"""surroundSelection("{unique_before}", "{unique_after}")"""
        self.web.evalWithCallback(jsf, lambda _, s=self, b=saveback: _editor_helper(s, b))


def EditorContextMenu(ewv, menu):
    menutext = "open selection in text editor"
    cut = gc("shortcut editor to open selection in text editor")
    if cut:
        menutext += f" (shortcut: {cut})"
    a = menu.addAction(menutext)
    a.triggered.connect(lambda _, e=ewv.editor: editor_helper(e, saveback=False))

    menutext = "send field content to text editor and save back"
    cut = gc("shortcut editor to send selected field content to text editor and save back")
    if cut:
        menutext += f" (shortcut: {cut})"
    a = menu.addAction(menutext)
    a.triggered.connect(lambda _, e=ewv.editor: editor_helper(e, saveback=True))
addHook('EditorWebView.contextMenuEvent', EditorContextMenu)


def editorShortcuts(cuts, editor):
    cut = gc("shortcut editor to open selection in text editor")
    if cut:
        cuts.append((cut, lambda e=editor: editor_helper(e, saveback=False)))
    cut = gc("shortcut editor to send selected field content to text editor and save back")
    if cut:
        cuts.append((cut, lambda e=editor: editor_helper(e, saveback=True)))
addHook("setupEditorShortcuts", editorShortcuts)
