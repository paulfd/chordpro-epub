#!python3

# Copyright(c) 2019 Paul Ferrand

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

import re
from enum import Enum
import argparse
from ebooklib import epub
import os

parser = argparse.ArgumentParser(
    description="Converts a batch of chordpro files into an epub")
parser.add_argument(
    'list', type=str, help="A list of chordpro files, one by line, to gather")
parser.add_argument('--wrap-chords', action='store_true',
                    help='Wrap chords in square brackets')
parser.add_argument('--css', type=str, help='CSS file to embed')
parser.add_argument('--output', type=str,
                    help='Output file name', default='songbook.epub')
parser.add_argument('--book-title', type=str,
                    help='Book title', default='Songbook')
parser.add_argument('--book-id', type=str, help='Book identifier',
                    default='songbook31415926535')
parser.add_argument('--book-author', type=str, help='Songbook author')
args = parser.parse_args()

song_skeleton = """
<h3>{0} ({1})</h3>
{2}"""

default_css = """
div.without-chords {
    line-height: 1;
	text-indent: -2em;
	padding-left: 2em;
}
div.with-chords {
    line-height: 1.7;
	text-indent: -2em;
	padding-left: 2em;
}
div.chorus {
    margin-top : 0.5em;
    font-style: italic;
    font-weight: normal;
}
div.verse {
    margin-top : 0.5em;
    font-weight: normal;
    font-style: normal;
}
div.bridge {
    margin-top : 0.5em;
    font-style: italic;
    font-weight: normal;
}
span.chord {
	display: inline-block;
	position: relative;
	font-weight: bold;
	font-size: 0.7em;
    bottom: 1.2em;
    left: 0.2em;
    width: 0;
	text-indent: 0;
	padding-left: 0;
}
span.whitespace{
    margin: 0.5em;
}
span.double-whitespace{
    margin: 1em;
}
"""

comments_re = re.compile(r"(.*?)\#.*")
title_re = re.compile(r"{title:\s*(.*?)}")
artist_re = re.compile(r"{artist:\s*(.*?)}")
comment_re = re.compile(r"{comment:\s*(.*?)}")

Status = Enum('Status', 'NONE VERSE CHORUS BRIDGE')

def clean_lines(lines):
    """ Strip lines, remove comments and put directives on their own line always."""
    cleaned_lines = []
    for line in lines:
            line = line.strip()
            start_idx = 0
            char_idx = 0
            in_chord = False
            while char_idx < len(line):
                if line[char_idx] == "[":
                    in_chord = True
                if line[char_idx] == "]":
                    in_chord = False
                if line[char_idx] == "#" and in_chord == False:
                    break
                
                if line[char_idx] == "{":
                    start_idx = char_idx
                    if char_idx != start_idx:
                        cleaned_lines.append(line[start_idx:char_idx].strip())
                if line[char_idx] == "}":
                    cleaned_lines.append(line[start_idx:char_idx + 1].strip())
                    start_idx = char_idx + 1
                char_idx += 1
            if start_idx != char_idx:
                cleaned_lines.append(line[start_idx:char_idx].strip())
            if len(line) == 0:
                cleaned_lines.append("")
    return cleaned_lines

def chopro_to_html(lines):
    """ Parse a chordpro file as a curated list of strings.
        In particular, we assume here that directives are on their 
            own line and do not span multiple lines.
        Empty lines indicate the end of a block (verse, bridge or chorus).
        Unknown directives are ignored.
    """
    cleaned_lines = clean_lines(lines)
    status = Status.NONE
    title = "No title found"
    artist = "Unknown artist"

    body = []

    for line in cleaned_lines:
        if (line == "{start_of_chorus}" or line == "{soc}") and (status == Status.NONE):
            status = Status.CHORUS
            body.append('<div class="chorus">')
            continue

        if (line == "{end_of_chorus}" or line == "{eoc}") and (status == Status.CHORUS):
            status = Status.NONE
            body.append('</div>')
            continue

        if (line == "{start_of_bridge}" or line == "{sob}") and (status == Status.NONE):
            status = Status.BRIDGE
            body.append('<div class="bridge">')
            continue

        if (line == "{end_of_bridge}" or line == "{eob}") and (status == Status.BRIDGE):
            status = Status.NONE
            body.append('</div>')
            continue

        title_match = title_re.match(line)
        if title_match is not None:
            title = title_match.group(1)
            continue

        artist_match = artist_re.match(line)
        if artist_match is not None:
            artist = artist_match.group(1)
            continue

        comment_match = comment_re.match(line)
        if comment_match is not None:
            body.append(f'<div class="comment">{comment_match.group(1)}</div>')
            continue

        if line == '':
            if status != Status.NONE:
                status = Status.NONE
                body.append('</div>')
            continue

        # Ignore unknown directives
        if line[0] == '{':
            continue

        if status == Status.NONE:
            status = Status.VERSE
            body.append('<div class="verse">')

        # Split on chords
        song_line = ''
        split_lines = line.split("[")
        if len(split_lines) > 1:
            song_line += '<div class="with-chords">'
        else:
            song_line += '<div class="without-chords">'

        if (split_lines[0] != ''):
            song_line += split_lines[0]

        for l in split_lines[1:]:
            # resplit between chord and text
            resplit = l.split("]")
            if len(resplit) == 1:
                chord = ''
                text = resplit[0]
            else:
                chord = resplit[0]
                text = ''.join(resplit[1:])
            if len(text) == 0 or text[0] == ' ':
                # Phantom space would be better but meh
                if len(chord) == 1:
                    text = f'<span class="whitespace"/>' + text
                else:
                    text = f'<span class="double-whitespace"/>' + text
            if args.wrap_chords:
                song_line += f'<span class="chord">[{chord}]</span>{text}'
            else:
                song_line += f'<span class="chord">{chord}</span>{text}'
        song_line += '</div>'
        body.append(song_line)

    body.append('</div>')
    full_body = '\n'.join(body)
    return full_body, title, artist

remove_punctuation_map = dict((ord(char), None) for char in r'\/*?:"<>|')

### Starting script per say

book = epub.EpubBook()

# Add metadata
book.set_identifier(args.book_id)
book.set_title(args.book_title)
if args.book_author is not None:
    book.add_author(args.book_author)

# Read the list
assert os.path.exists(args.list), "Nonexistent list file"
with open(args.list) as input_file:
    file_list = input_file.readlines()

# Parse chordpro files and fill the epub structure
for f in file_list:
    file_name = f.strip()
    if not os.path.exists(file_name):
        print(f"Could not open {file_name}, skipping")
        continue

    with open(file_name) as file:
        body, title, artist = chopro_to_html(file.readlines())
    song_title = f'{title} ({artist})'
    song_filename = f'{title}_{artist}.xhtml'.translate(remove_punctuation_map)
    chapter = epub.EpubHtml(title=song_title, file_name=song_filename, lang='en', )
    chapter.add_link(href='style.css', rel='stylesheet', type='text/css')
    chapter.content = song_skeleton.format(title, artist, body)
    book.add_item(chapter)

# Setup TOC
chapter_list = list(book.get_items())
book.toc = (tuple(chapter_list))

# Add style with default is none is specified
if (args.css is not None) and (os.path.exists(args.css)):
    with open(args.css) as css_file:
        style_css = epub.EpubItem(
            uid="style", file_name="style.css", media_type="text/css", content=css_file.read())
else:
    style_css = epub.EpubItem(uid="style", file_name="style.css", media_type="text/css", content=default_css)
book.add_item(style_css)

# add navigation files
book.add_item(epub.EpubNcx())
book.add_item(epub.EpubNav())

# create spine
book.spine = ['nav'] + chapter_list

epub.write_epub(args.output, book)
