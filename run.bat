@echo off
echo ================================================================================ Syncing ChordPro files....
echo xcopy C:\Users\rhh\Documents\DATA\MobileSheets\LocalState\*.cho ..\  /d /i /f /y
echo xcopy ..\*.cho C:\Users\rhh\Documents\DATA\MobileSheets\LocalState\  /d /i /f /y

echo ================================================================================ Creating EPUB
dir /b *.cho > list.txt
python3 chopro-epub.py --css chopro-epub.css --book-author "Tester" --book-title "chopro-epub book" --output .\songbook.epub list.txt
del list.txt
del info.log
echo .
pause