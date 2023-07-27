#!python3
# -*- encoding: utf-8 -*-

# Copyright(c) 2019-2023 Paul Ferrand

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
from enum import Enum

import pyparsing as pp


def chordpro2html(song: str, wrap_chords: bool = True) -> str:
    """Converts a ChordPro file to HTML

    Args:
        song (str): The ChordPro file content
        wrap_chords (bool, optional): Wrap chords. Defaults to True.

    Returns:
        str: the HTML formatted ChordPro file
    """
    title = "Unknown Title"
    artist = "Unknown Artist"
    output = ""

    SongState = Enum("SongState", "NONE VERSE CHORUS TAB BRIDGE")
    song_state = SongState.NONE
    text_buffer = ""

    # pyparsing parse-action handler

    def div(cls, content):
        return f'<div class="{cls}">{content}</div>'

    def handle_empty_line(t):  # switch-bak songState
        nonlocal song_state
        if song_state == SongState.VERSE:  # reset from default state
            song_state = SongState.NONE
            return "</div>\n<br>"
        else:
            return "<br>"

    def handle_song_line(t):  # postponed handling of total line
        nonlocal text_buffer, song_state
        line_has_text = len(text_buffer.strip()) > 0
        text_buffer = ""  # not needed any longer
        line = ""  # prepare output-line

        if song_state == SongState.NONE:  # default state!
            song_state = SongState.VERSE
            line += '<div class="verse">'

        line += '<div class="songline">'

        for item in t:
            if not all(key in ["text", "chord"] for key in item.keys()):
                logging.info(f"Unexpected keys in item: {list(item.keys())}")
                continue

            if "chord" in item:
                chord = item.chord if wrap_chords else item.chord[1:-1]
                chord_div = div("chord", chord)

            text = ""
            if line_has_text:
                if "text" not in item:
                    text = "&nbsp;"
                else:
                    text = item.text
                    if text[-1].isspace():
                        text = text[:-1] + "&nbsp;"
                text_div = div("text", text)

            if "chord" in item:
                if text:
                    line += div("chordbox", chord_div + text_div)
                else:
                    line += div("chordbox", chord_div)
            else:
                line += div("chordbox", text_div)

        line += "</div>"  # ...songLine
        return line

    def handle_text(t):  # store text in shadow buffer for later analysis
        nonlocal text_buffer
        text_buffer += t[0]
        return t

    def handle_env_directive(t):  # switch songState
        nonlocal song_state
        token = t[0].strip().lower()
        str_return = ""

        if song_state != SongState.NONE:  # force switching!
            song_state = SongState.NONE
            str_return += "</div>"

        if token in ["start_of_chorus", "soc"]:
            song_state = SongState.CHORUS
            str_return += '<div class="chorus">'
        elif token in ["start_of_tab", "sot"]:
            song_state = SongState.TAB
            str_return += '<div class="tab">'

        return str_return

    def handle_form_directive(t):  # only comments so far....
        token = t[0].strip().lower()
        arg = t[1].strip()
        if token in ["comment", "c"]:
            arg = arg.replace("\n", "<br>")
            return div("comment", arg)
        elif token in ["comment_box", "cb"]:
            arg = arg.replace("\n", "<br>")
            return div("commentbox", arg)
        else:  # unhandled...
            logging.info(f"Unhandled form directive: {t.dump()}")

    def handle_meta_directive(t):
        nonlocal title, artist
        token = t[0].strip().lower()
        arg = t[1].strip()
        if token in ["title", "t"]:
            title = arg
            return div("title", arg)
        elif token in ["artist", "a"]:
            artist = arg
            return div("artist", arg)
        else:  # unhandled...
            logging.info(f"Unhandled meta directive: {t.dump()}")

    # pyparsing grammar definition: directives
    pp.ParserElement.setDefaultWhitespaceChars("")

    # lyricCharSet = pp.alphanums+pp.alphas8bit+",-_:;.!?#+*^°§$%&/|()='`´\\\"\t "
    # everything but "{}[]"
    lyric_char_set = pp.pyparsing_unicode.Latin1.printables + "\t "
    chord_char_set = pp.alphanums + " -#(%)/='`´."

    cmd = pp.oneOf("title t artist a")
    arg = pp.SkipTo("}")
    meta_directive = pp.Suppress("{") + cmd + pp.Suppress(":") + arg
    meta_directive.setParseAction(handle_meta_directive)

    cmd = pp.oneOf("comment c comment_box cb")
    arg = pp.SkipTo("}")
    form_directive = pp.Suppress("{") + cmd + pp.Suppress(":") + arg
    form_directive.setParseAction(handle_form_directive)

    cmd = pp.oneOf("start_of_chorus soc end_of_chorus eoc start_of_tab sot end_of_tab eot")
    env_directive = pp.Suppress("{") + cmd + pp.Suppress("}")
    env_directive.setParseAction(handle_env_directive)

    directives = meta_directive | form_directive | env_directive

    # pyparsing grammar definition: chordlines

    white_spaces = pp.Word(" \t")
    empty_line = pp.LineStart() + pp.Optional(white_spaces) + pp.LineEnd()  # incl. whiteSpaces
    empty_line.setParseAction(handle_empty_line)

    line_start = pp.LineStart()
    line_end = pp.Suppress(pp.LineEnd())  ####### needs Unix type line-endings (at the moment...)

    chord = pp.Combine("[" + pp.Word(chord_char_set) + "]")  # leave square brackets there....
    text = pp.Word(lyric_char_set, excludeChars="[]{}")
    text.setParseAction(handle_text)

    chord_box = pp.Group(
        (chord("chord") + white_spaces("text"))  # Lone chord with white space afterwards
        | (chord("chord") + text("text"))  # standard chordbox with chord AND text
        | chord("chord")  # single chord w/o text
        | text("text")  # single text w/o chord
    )

    song_line = line_start + pp.OneOrMore(chord_box) + line_end
    song_line.setParseAction(handle_song_line)

    markup = (
        empty_line | song_line | directives
    )  # >emptyLine< MUST be bofore >songLine< to catch emptyLine-action

    for result in markup.searchString(song):
        output += result[0] + "\n"

    # logging.info(output)
    return output, title, artist
