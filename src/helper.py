import html
import re


# TODO check changes from https://github.com/ankitects/anki/pull/703
# 2nd half of Editor._processText from 2.1.28
def adjust_text_to_html(txt):
    # normal text; convert it to HTML
    txt = html.escape(txt)
    txt = txt.replace("\n", "<br>").replace("\t", " " * 4)
    # if there's more than one consecutive space,
    # use non-breaking spaces for the second one on
    def repl(match):
        return match.group(1).replace(" ", "&nbsp;") + " "
    txt = re.sub(" ( +)", repl, txt)
    return txt
