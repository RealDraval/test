TV Series Relabeler - Help

This tool renames episode files for TV series folders using official episode titles from TheMovieDB (TMDb).

How it works:
1. Click "Browse Folder" and select the top-level folder for your TV show.
   - The folder should contain subfolders like "Season 1", "Season 2", etc.
2. A list of seasons will appear. Check the boxes next to the seasons you want to relabel.
   - You can use "Select All Seasons" to check all.
3. If you want to skip short clips (like intros, trailers, etc.), check "Skip Short Clips?".
   - Set the minimum length (in minutes) to identify short clips.
   - Short clips will be moved to a central "Extras" folder.
4. Click "Start Relabeling".
   - Each episode file will be renamed using this format:
     Show Name - S01E01 - Episode Title.ext
   - If no episode title is found from TMDb, it uses just the episode number.
   - Episode numbering is based on file creation time (oldest = Episode 1).
   - Extras folders inside each season are merged into the top-level Extras folder.
5. When relabeling is complete, a message will appear.

Requirements:
- An internet connection to access TMDb.
- FFmpeg installed and accessible (for checking video duration).

This tool is useful for organizing ripped or downloaded TV series into a clean, media-server-friendly format.
