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
    chordpro_file: Path = typer.Argument(help="The file to conver"),
    output: Path = typer.Option("song.html", help="The output path for the generated HTML song."),
    css: Optional[Path] = typer.Option(
        None,
        help="The path to a custom CSS file to style the EPUB.",
    ),
    wrap_chords: bool = typer.Option(
        False, help="If True, chords within the song lyrics will be wrapped in square brackets."
    ),
    verbose: bool = False,
):
    """Generate an EPUB songbook from a list of songs."""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    # Add style with default if none is specified
    if css is not None:
        assert css.exists() and css.is_file(), f"CSS file {css} is not a file"
    else:
        pkg = importlib_resources.files("chopro_epub")
        css = pkg / "chopro-epub.css"

    logging.debug(f"Using CSS file {css}")
    with css.open() as css_file:
        css_content = css_file.read()

    logging.debug(f"Parsing {chordpro_file}")
    with codecs.open(chordpro_file, "r", "utf-8") as file:
        body, title, artist = chordpro2html(file.read(), wrap_chords=wrap_chords)
    content = f"<h3>{title} ({artist})</h3>"
    content += f"<style>{css_content}</style>"
    content += body

    logging.info(f"Writing output to {output}")
    with output.open("w") as f:
        f.write(content)


if __name__ == "__main__":
    main()
