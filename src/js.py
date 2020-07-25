from aqt import gui_hooks

def js_inserter(self):
    # https://stackoverflow.com/questions/17497661/insert-text-before-and-after-selection-in-a-contenteditable
    jsstring = """
function surroundSelection(before, after) {
    var sel = window.getSelection();
    var range = sel.getRangeAt(0);
    var r = range.cloneRange();
    r.collapse(false);
    r.insertNode(document.createTextNode(after));
    r.setStart(range.startContainer, range.startOffset);
    r.insertNode(document.createTextNode(before));
}
"""
    self.web.eval(jsstring)
gui_hooks.editor_did_init.append(js_inserter)
