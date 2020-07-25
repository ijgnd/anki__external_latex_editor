# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl.html
# Copyright: github.com/pointtonull
#            ijgnd
#            Damien Elmes
#
#
#
#
# This add-on uses a octicons-tools.svg covered by the following copyright
# and permission notice:
#
#     Copyright © GithHub
#
#     Permission is hereby granted, free of charge, to any person obtaining a copy of this software
#     and associated documentation files (the "Software"), to deal in the Software without
#     restriction, including without limitation the rights to use, copy, modify, merge, publish,
#     distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the
#     Software is furnished to do so, subject to the following conditions:
#
#     The above copyright notice and this permission notice shall be included in all copies or
#     substantial portions of the Software.
#
#     The Software is provided "as is", without warranty of any kind, express or implied, including
#     but not limited to the warranties of merchantability, fitness for a particular purpose
#     and noninfringement. In no event shall the authors or copyright holders be liable for any
#     claim, damages or other liability, whether in an action of contract, tort or otherwise,
#     arising from, out of or in connection with the Software or the use or other dealings in
#     the Software.

import os

from anki.hooks import wrap, addHook
from anki.utils import (
    stripHTML,
)
from aqt import gui_hooks
from aqt import mw
from aqt.editor import Editor
from aqt.qt import Qt
from aqt.utils import tooltip

from .config import addon_path, gc
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
        self.nid_latex_helper = True  # can't set to self.note.id because it's 0 for new.
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





def restore_prior(self):
    if not thefield == self.currentField:
        tooltip("active field is not the last field edited externally. Aborting.")
        return
    if self.currentField is not None:
        active = self.currentField + 1  # zero is False
    else:
        active = None
    self.note.fields[thefield] = oldcontent
    if active:
        self.loadNote(focusTo=active-1)
    else:
        self.loadNote()
        self.web.setFocus()


def button_helper(self):
    # self is editor
    modifiers = self.mw.app.queryKeyboardModifiers()
    shift_and_click = modifiers == Qt.ShiftModifier
    if shift_and_click:
        if self.nid_latex_helper:
            restore_prior(self)
        else:
            tooltip("no prior version stored. Aborting")
        return
    editor_helper(self, saveback=True)



def reset(self):
    self.nid_latex_helper = None
gui_hooks.editor_did_init.append(reset)




if gc("show button to edit selection externally and save it back"):
    tip = "send selection to external editor and save back"
    cut = gc("shortcut editor to send selected field content to text editor and save back")
    if cut:
        tip += f" ({cut}"
    def setupEditorButtonsFilterFD(buttons, editor):
        b = editor.addButton(
                icon=os.path.join(addon_path, "octicons-tools.svg"),
                cmd="restore_prior_external_text_editor_fork",
                func=button_helper,
                tip=tip,
            )
        buttons.append(b)
        return buttons
    addHook("setupEditorButtons", setupEditorButtonsFilterFD)
