import os
import subprocess
import json
import requests
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# --- Your TMDb API Key ---
TMDB_API_KEY = "f538d773495a28a5ea4743384102b9b2"

# --- Helper to get video duration using ffprobe ---
def get_video_duration(filepath):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                filepath
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        duration = float(result.stdout.strip())
        return duration
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return 0

# --- Get episode metadata from TMDb ---
def get_episode_titles(tv_show_name, season_number):
    try:
        search_url = f"https://api.themoviedb.org/3/search/tv?api_key={TMDB_API_KEY}&query={tv_show_name}"
        response = requests.get(search_url)
        response.raise_for_status()
        results = response.json()["results"]
        if not results:
            raise Exception(f"No TV show found for {tv_show_name}.")

        tv_id = results[0]["id"]
        season_url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}?api_key={TMDB_API_KEY}"
        response = requests.get(season_url)
        response.raise_for_status()
        episodes = response.json()["episodes"]

        episode_titles = [ep["name"] for ep in episodes]
        return episode_titles
    except Exception as e:
        print(f"Error fetching TMDb data: {e}")
        return []

# --- Helper to delete empty folders ---
def delete_empty_folders(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for dir in dirs:
            full_path = os.path.join(root, dir)
            if not os.listdir(full_path):  # Folder is empty
                print(f"Deleting empty folder: {full_path}")
                os.rmdir(full_path)

# --- Main renaming function ---
def relabel_episodes(folder_path, season_number, extras_folder_name, skip_short_clips, clip_length_seconds):
    tv_show_name = os.path.basename(folder_path)

    episode_titles = get_episode_titles(tv_show_name, season_number)

    # Gather all video files
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov']
    all_videos = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in video_extensions:
                full_path = os.path.join(root, file)
                creation_time = os.path.getctime(full_path)
                all_videos.append((full_path, creation_time))
    
    # Sort videos by creation time
    all_videos.sort(key=lambda x: x[1])

    # Prepare extras folder
    extras_folder = os.path.join(folder_path, extras_folder_name)
    os.makedirs(extras_folder, exist_ok=True)

    episode_num = 1
    for video_path, _ in all_videos:
        ext = os.path.splitext(video_path)[1]
        duration = get_video_duration(video_path)

        if skip_short_clips and duration < clip_length_seconds:
            print(f"Moving short clip to extras: {video_path}")
            shutil.move(video_path, os.path.join(extras_folder, os.path.basename(video_path)))
            continue

        if episode_num <= len(episode_titles):
            episode_title = episode_titles[episode_num - 1]
            clean_title = "".join(c for c in episode_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            new_filename = f"{tv_show_name} - S{season_number:02d}E{episode_num:02d} - {clean_title}{ext}"
        else:
            # No episode title available, use generic
            new_filename = f"{tv_show_name} - S{season_number:02d}E{episode_num:02d}{ext}"

        new_path = os.path.join(folder_path, new_filename)
        print(f"Renaming {os.path.basename(video_path)} → {new_filename}")
        shutil.move(video_path, new_path)

        episode_num += 1

    # After relabeling, delete empty folders
    delete_empty_folders(folder_path)

# --- GUI setup ---
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_path_var.set(folder_selected)

def start_relabel():
    folder_path = folder_path_var.get()
    if not folder_path:
        messagebox.showerror("Error", "Please select a folder first.")
        return
    
    try:
        season_number = int(season_number_var.get())
    except:
        messagebox.showerror("Error", "Please enter a valid Season Number.")
        return

    skip_clips = skip_var.get()
    clip_length = clip_length_entry.get()
    try:
        clip_length_seconds = int(clip_length) * 60  # Minutes to seconds
    except:
        clip_length_seconds = 300  # Default 5 minutes if invalid

    relabel_episodes(folder_path, season_number, "Extras", skip_clips, clip_length_seconds)
    messagebox.showinfo("Done", "Relabeling complete!")

# --- Tkinter GUI ---
root = tk.Tk()
root.title("TV Series Relabeler")
root.geometry("600x350")

frame = ttk.Frame(root, padding=20)
frame.pack(fill=tk.BOTH, expand=True)

folder_path_var = tk.StringVar()
season_number_var = tk.StringVar()

browse_button = ttk.Button(frame, text="Browse Folder", command=browse_folder)
browse_button.grid(row=0, column=0, pady=10, sticky="w")

folder_entry = ttk.Entry(frame, textvariable=folder_path_var, width=50)
folder_entry.grid(row=0, column=1, pady=10, padx=10)

season_label = ttk.Label(frame, text="Season Number:")
season_label.grid(row=1, column=0, pady=10, sticky="w")

season_entry = ttk.Entry(frame, textvariable=season_number_var, width=10)
season_entry.grid(row=1, column=1, sticky="w", pady=10)

skip_var = tk.BooleanVar()
skip_checkbox = ttk.Checkbutton(frame, text="Skip Short Clips?", variable=skip_var)
skip_checkbox.grid(row=2, column=0, pady=10, sticky="w")

clip_length_label = ttk.Label(frame, text="Short Clip Max Length (minutes):")
clip_length_label.grid(row=2, column=1, sticky="w")

clip_length_entry = ttk.Entry(frame, width=5)
clip_length_entry.insert(0, "5")  # Default 5 minutes
clip_length_entry.grid(row=2, column=1, padx=(220, 0))

submit_button = ttk.Button(frame, text="Submit", command=start_relabel)
submit_button.grid(row=3, column=0, columnspan=2, pady=20)

root.mainloop()
