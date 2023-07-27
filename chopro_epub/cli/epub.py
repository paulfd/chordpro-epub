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

import codecs
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from ebooklib import epub

from chopro_epub.parser import chordpro2html

if sys.version_info < (3, 9):
    # importlib.resources either doesn't exist or lacks the files()
    # function, so use the PyPI version:
    import importlib_resources
else:
    # importlib.resources has files(), so use that:
    import importlib.resources as importlib_resources


@typer.run
def main(
    song_list: Path = typer.Argument(
        help="The path to the file containing the list of songs with one song per line."
    ),
    output: Path = typer.Option(
        "songbook.epub", help="The output path for the generated EPUB songbook."
    ),
    css: Optional[Path] = typer.Option(
        None,
        help="The path to a custom CSS file to style the EPUB.",
    ),
    book_title: str = typer.Option("Songbook", help="The title of the generated EPUB songbook."),
    book_id: str = typer.Option("songbook31415926535", help="An identifier for the EPUB songbook."),
    book_author: Optional[str] = typer.Option(
        None, help="The author or creator of the EPUB songbook."
    ),
    wrap_chords: bool = typer.Option(
        False, help="If True, chords within the song lyrics will be wrapped in square brackets."
    ),
    verbose: bool = False,
):
    """Generate an EPUB songbook from a list of songs."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    song_skeleton = """<h3>{0} ({1})</h3>{2}"""
    remove_punctuation_map = dict((ord(char), None) for char in r'\/*?:"<>|')

    ### Starting script per say
    book = epub.EpubBook()

    # Add metadata
    book.set_identifier(book_id)
    book.set_title(book_title)
    logging.debug(f"Book ID: {book_id}")
    logging.debug(f"Book title: {book_title}")

    if book_author is not None:
        book.add_author(book_author)
        logging.debug(f"Book author: {book_author}")

    # Read the list
    assert song_list.exists() and song_list.is_file(), "Nonexistent list file"

    # Parse chordpro files and fill the epub structure
    for f in song_list.open():
        file_name = Path(f.strip())
        if not file_name.exists():
            logging.error(f"Could not open {file_name}, skipping")
            continue

        logging.debug(f"Parsing {file_name}")
        with codecs.open(file_name, "r", "utf-8") as file:
            body, title, artist = chordpro2html(file.read(), wrap_chords=wrap_chords)

        song_title = f"{title} ({artist})"
        song_filename = f"{title}_{artist}.xhtml".translate(remove_punctuation_map)
        chapter = epub.EpubHtml(
            title=song_title,
            file_name=song_filename,
            lang="en",
        )
        chapter.add_link(href="style.css", rel="stylesheet", type="text/css")
        chapter.content = song_skeleton.format(title, artist, body)
        book.add_item(chapter)

    # Setup TOC
    chapter_list = list(book.get_items())
    book.toc = tuple(chapter_list)

    # Add style with default if none is specified
    if css is not None:
        assert css.exists() and css.is_file(), f"CSS file {css} is not a file"
    else:
        pkg = importlib_resources.files("chopro_epub")
        css = pkg / "chopro-epub.css"

    logging.debug(f"Using CSS file {css}")
    with css.open() as css_file:
        style_css = epub.EpubItem(
            uid="style",
            file_name="style.css",
            media_type="text/css",
            content=css_file.read(),
        )
    book.add_item(style_css)

    # add navigation files
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    # create spine
    book.spine = ["nav"] + chapter_list

    logging.info(f"Writing output to {output}")
    epub.write_epub(output, book)


if __name__ == "__main__":
    main()
