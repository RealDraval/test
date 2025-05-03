# [Same imports as before]
import os
import subprocess
import json
import requests
import shutil
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --- Your TMDb API Key ---
TMDB_API_KEY = "f538d773495a28a5ea4743384102b9b2"

def get_video_duration(filepath):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", filepath],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return float(result.stdout.strip())
    except:
        return 0

def get_episode_titles(tv_show_name, season_number):
    try:
        search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={tv_show_name}"
        response = requests.get(search_url)
        response.raise_for_status()
        results = response.json()["results"]
        if not results:
            raise Exception("No TV show found.")

        tv_id = results[0]["id"]
        season_url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}?api_key={TMDB_API_KEY}"
        response = requests.get(season_url)
        response.raise_for_status()
        return [ep["name"] for ep in response.json()["episodes"]]
    except Exception as e:
        print(f"TMDb error: {e}")
        return []

def delete_empty_folders(folder_path):
    for root, dirs, _ in os.walk(folder_path, topdown=False):
        for dir in dirs:
            full_path = os.path.join(root, dir)
            if not os.listdir(full_path):
                os.rmdir(full_path)

def move_season_extras_to_main_extras(top_folder, extras_folder_name="Extras"):
    extras_folder = os.path.join(top_folder, extras_folder_name)
    os.makedirs(extras_folder, exist_ok=True)

    for name in os.listdir(top_folder):
        season_folder = os.path.join(top_folder, name)
        if os.path.isdir(season_folder) and "season" in name.lower():
            season_extras_folder = os.path.join(season_folder, "Extras")
            if os.path.exists(season_extras_folder):
                for file in os.listdir(season_extras_folder):
                    src_path = os.path.join(season_extras_folder, file)
                    if os.path.isfile(src_path):
                        shutil.move(src_path, os.path.join(extras_folder, file))
                delete_empty_folders(season_extras_folder)

def relabel_episodes(folder_path, season_number, episode_titles, extras_folder, skip_short_clips, clip_length_seconds):
    tv_show_name = os.path.basename(os.path.dirname(folder_path))
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov']
    all_videos = []

    for root, _, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in video_extensions:
                full_path = os.path.join(root, file)
                creation_time = os.path.getctime(full_path)
                all_videos.append((full_path, creation_time))

    all_videos.sort(key=lambda x: x[1])
    episode_num = 1

    for video_path, _ in all_videos:
        ext = os.path.splitext(video_path)[1]
        duration = get_video_duration(video_path)

        if skip_short_clips and duration < clip_length_seconds:
            print(f"Moving short clip to extras: {video_path}")
            shutil.move(video_path, os.path.join(extras_folder, os.path.basename(video_path)))
            continue

        if episode_num <= len(episode_titles):
            title = episode_titles[episode_num - 1]
            clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            new_filename = f"{tv_show_name} - S{season_number:02d}E{episode_num:02d} - {clean_title}{ext}"
        else:
            new_filename = f"{tv_show_name} - S{season_number:02d}E{episode_num:02d}{ext}"

        new_path = os.path.join(folder_path, new_filename)
        shutil.move(video_path, new_path)
        print(f"Renamed: {os.path.basename(video_path)} → {new_filename}")
        episode_num += 1

    delete_empty_folders(folder_path)

# --- GUI logic ---
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if not folder_selected:
        return
    folder_path_var.set(folder_selected)

    for widget in checkbox_frame.winfo_children():
        widget.destroy()
    season_checkboxes.clear()

    for name in os.listdir(folder_selected):
        subfolder = os.path.join(folder_selected, name)
        if os.path.isdir(subfolder) and "season" in name.lower():
            try:
                season_number = int(''.join(filter(str.isdigit, name)))
                var = tk.BooleanVar()
                cb = ctk.CTkCheckBox(checkbox_frame, text=name, variable=var)
                cb.grid(row=len(season_checkboxes), column=0, sticky="w", padx=10, pady=5)
                season_checkboxes.append((season_number, subfolder, var))
            except ValueError:
                continue

def toggle_select_all():
    for _, _, var in season_checkboxes:
        var.set(select_all_var.get())

def start_relabel():
    folder_path = folder_path_var.get()
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder.")
        return

    skip_clips = skip_var.get()
    try:
        clip_length_seconds = int(clip_length_entry.get()) * 60
    except:
        clip_length_seconds = 300

    selected = [item for item in season_checkboxes if item[2].get()]
    if not selected:
        messagebox.showerror("Error", "Please select at least one season.")
        return

    # --- Ensure main Extras folder exists and collect existing extras from seasons
    extras_folder = os.path.join(folder_path, "Extras")
    os.makedirs(extras_folder, exist_ok=True)
    move_season_extras_to_main_extras(folder_path, "Extras")

    for season_number, folder, _ in selected:
        episode_titles = get_episode_titles(os.path.basename(folder_path), season_number)
        relabel_episodes(folder, season_number, episode_titles, extras_folder, skip_clips, clip_length_seconds)

    messagebox.showinfo("Done", "Relabeling complete!")

# --- GUI Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("TV Series Relabeler")
root.geometry("800x600")

frame = ctk.CTkFrame(root, corner_radius=15)
frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

canvas = tk.Canvas(frame)
canvas.grid(row=2, column=0, columnspan=2, sticky="nsew")

scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
scrollbar.grid(row=2, column=2, sticky="ns")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.bind_all("<Configure>", lambda e, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))

checkbox_frame = ctk.CTkFrame(canvas, corner_radius=10)
canvas.create_window((0, 0), window=checkbox_frame, anchor="nw")

folder_path_var = tk.StringVar()
season_checkboxes = []

browse_button = ctk.CTkButton(frame, text="Browse Folder", command=browse_folder)
browse_button.grid(row=0, column=0, pady=10, sticky="w")

folder_entry = ctk.CTkEntry(frame, textvariable=folder_path_var, width=300)
folder_entry.grid(row=0, column=1, pady=10, padx=10)

def show_help():
    help_text = """
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
"""
    messagebox.showinfo("Help - TV Series Relabeler", help_text)

# Add the Help button at the top right
help_button = ctk.CTkButton(frame, text="Help", command=show_help)
help_button.grid(row=0, column=2, pady=10, padx=10, sticky="e")


select_all_var = tk.BooleanVar()
select_all_checkbox = ctk.CTkCheckBox(frame, text="Select All Seasons", variable=select_all_var, command=toggle_select_all)
select_all_checkbox.grid(row=1, column=0, columnspan=2, pady=10, sticky="w", padx=10)

skip_var = tk.BooleanVar()
skip_checkbox = ctk.CTkCheckBox(frame, text="Skip Short Clips?", variable=skip_var)
skip_checkbox.grid(row=3, column=0, columnspan=2, pady=10, sticky="w", padx=10)

clip_length_label = ctk.CTkLabel(frame, text="Clip Length (Minutes):")
clip_length_label.grid(row=4, column=0, pady=10, sticky="w", padx=10)

clip_length_entry = ctk.CTkEntry(frame)
clip_length_entry.grid(row=4, column=1, pady=10, padx=10)

relabel_button = ctk.CTkButton(frame, text="Start Relabeling", command=start_relabel)
relabel_button.grid(row=5, column=0, columnspan=2, pady=20)

root.mainloop()
