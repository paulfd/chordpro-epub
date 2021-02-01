# chordpro-epub
Simple script to create a songbook from a list of chordpro files

# Usage

The script requires the `ebooklib` library available from pip, in order to create epub files.
You can select specific `css` files on creation depending on your target (phone or ereader with various level of CSS compatibility).
The understood chopro format is barebones, basically only title, author, comments, choruses and bridges are taken into account, everything else is just discarded.

```bash
[user@foo chopro-epub]$ python3 chopro-epub.py --help
usage: chopro-epub.py [-h] [--wrap-chords] [--css CSS] [--output OUTPUT]
                      [--book-title BOOK_TITLE] [--book-id BOOK_ID]
                      [--book-author BOOK_AUTHOR]
                      list

Converts a batch of chordpro files into an epub

positional arguments:
  list                  A list of chordpro files, one by line, to gather

optional arguments:
  -h, --help            show this help message and exit
  --wrap-chords         Wrap chords in square brackets
  --css CSS             CSS file to embed
  --output OUTPUT       Output file name
  --book-title BOOK_TITLE
                        Book title
  --book-id BOOK_ID     Book identifier
  --book-author BOOK_AUTHOR
                        Songbook author
```

Example usage
```bash
$ python3 chopro-epub.py --css songbook.css --output songbook.epub list.txt
$ python3 chopro-epub.py --wrap-chords --css sony.css --output songbook-sony.epub list.txt

```