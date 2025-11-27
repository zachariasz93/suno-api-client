"""
Suno API GUI Application
Lightweight GUI using Tkinter for music generation
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.settings import get_api_key, ensure_downloads_dir, AVAILABLE_MODELS, DEFAULT_MODEL
from src.api.client import SunoAPI
from src.api.models import Model, TaskStatusEnum, SeparationType
from src.api.exceptions import SunoAPIError, TaskFailedError, TaskTimeoutError


class SunoGUI:
    """Main GUI Application for Suno API"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎵 Suno AI Music Generator")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Initialize API
        self.api = None
        self.current_task_id = None
        self.is_generating = False
        
        # Configure style
        self.style = ttk.Style()
        self.style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Heading.TLabel", font=("Segoe UI", 11, "bold"))
        self.style.configure("Status.TLabel", font=("Segoe UI", 10))
        self.style.configure("Big.TButton", font=("Segoe UI", 11), padding=10)
        
        self._create_widgets()
        self._connect_api()
    
    def _connect_api(self):
        """Initialize API connection"""
        try:
            api_key = get_api_key()
            self.api = SunoAPI(api_key)
            self._update_credits()
            self.status_var.set("✓ Connected to Suno API")
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to connect: {e}")
            self.status_var.set("✗ Not connected")
    
    def _update_credits(self):
        """Update credits display"""
        if self.api:
            try:
                credits = self.api.get_credits()
                self.credits_var.set(f"💰 Credits: {credits}")
            except Exception as e:
                self.credits_var.set("💰 Credits: Error")
    
    def _create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(header_frame, text="🎵 Suno AI Music Generator", style="Title.TLabel").pack(side=tk.LEFT)
        
        self.credits_var = tk.StringVar(value="💰 Credits: ...")
        ttk.Label(header_frame, textvariable=self.credits_var, style="Heading.TLabel").pack(side=tk.RIGHT)
        
        ttk.Button(header_frame, text="↻ Refresh", command=self._update_credits, width=10).pack(side=tk.RIGHT, padx=5)
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create tabs
        self._create_generate_tab()
        self._create_lyrics_tab()
        self._create_process_tab()
        self._create_history_tab()
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(side=tk.LEFT)
        
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", length=200)
        self.progress.pack(side=tk.RIGHT)
    
    def _create_generate_tab(self):
        """Create Music Generation tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="🎵 Generate Music")
        
        # Left panel - Input
        left_frame = ttk.LabelFrame(tab, text="Music Settings", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Prompt
        ttk.Label(left_frame, text="Prompt / Lyrics:", style="Heading.TLabel").pack(anchor=tk.W)
        self.prompt_text = scrolledtext.ScrolledText(left_frame, height=6, wrap=tk.WORD, font=("Segoe UI", 10))
        self.prompt_text.pack(fill=tk.X, pady=(5, 10))
        self.prompt_text.insert("1.0", "A peaceful acoustic guitar melody with soft vocals, folk style")
        
        # Model selection
        model_frame = ttk.Frame(left_frame)
        model_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(model_frame, text="Model:").pack(side=tk.LEFT)
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, values=AVAILABLE_MODELS, state="readonly", width=15)
        model_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(model_frame, text="(V5 = fastest, V4_5 = best quality)", foreground="gray").pack(side=tk.LEFT)
        
        # Options frame
        options_frame = ttk.Frame(left_frame)
        options_frame.pack(fill=tk.X, pady=10)
        
        # Custom mode
        self.custom_var = tk.BooleanVar(value=False)
        custom_check = ttk.Checkbutton(options_frame, text="Custom Mode", variable=self.custom_var, command=self._toggle_custom_mode)
        custom_check.pack(side=tk.LEFT)
        
        # Instrumental
        self.instrumental_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Instrumental (no vocals)", variable=self.instrumental_var).pack(side=tk.LEFT, padx=20)
        
        # Custom mode fields (initially hidden)
        self.custom_frame = ttk.LabelFrame(left_frame, text="Custom Mode Options", padding="10")
        
        # Style
        style_frame = ttk.Frame(self.custom_frame)
        style_frame.pack(fill=tk.X, pady=2)
        ttk.Label(style_frame, text="Style:", width=10).pack(side=tk.LEFT)
        self.style_var = tk.StringVar(value="Pop")
        ttk.Entry(style_frame, textvariable=self.style_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Title
        title_frame = ttk.Frame(self.custom_frame)
        title_frame.pack(fill=tk.X, pady=2)
        ttk.Label(title_frame, text="Title:", width=10).pack(side=tk.LEFT)
        self.title_var = tk.StringVar(value="My Song")
        ttk.Entry(title_frame, textvariable=self.title_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Vocal Gender
        vocal_frame = ttk.Frame(self.custom_frame)
        vocal_frame.pack(fill=tk.X, pady=2)
        ttk.Label(vocal_frame, text="Vocal:", width=10).pack(side=tk.LEFT)
        self.vocal_var = tk.StringVar(value="")
        ttk.Radiobutton(vocal_frame, text="Auto", variable=self.vocal_var, value="").pack(side=tk.LEFT)
        ttk.Radiobutton(vocal_frame, text="Male", variable=self.vocal_var, value="m").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(vocal_frame, text="Female", variable=self.vocal_var, value="f").pack(side=tk.LEFT)
        
        # Negative tags
        neg_frame = ttk.Frame(self.custom_frame)
        neg_frame.pack(fill=tk.X, pady=2)
        ttk.Label(neg_frame, text="Exclude:", width=10).pack(side=tk.LEFT)
        self.negative_var = tk.StringVar(value="")
        ttk.Entry(neg_frame, textvariable=self.negative_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Download option
        self.download_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left_frame, text="Auto-download generated files", variable=self.download_var).pack(anchor=tk.W, pady=10)
        
        # Generate button
        self.generate_btn = ttk.Button(left_frame, text="🎵 Generate Music", style="Big.TButton", command=self._generate_music)
        self.generate_btn.pack(fill=tk.X, pady=10)
        
        # Right panel - Results
        right_frame = ttk.LabelFrame(tab, text="Results", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.result_text = scrolledtext.ScrolledText(right_frame, height=20, wrap=tk.WORD, font=("Consolas", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self.result_text.insert("1.0", "Results will appear here...\n")
        
        # Action buttons
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(btn_frame, text="📋 Copy URLs", command=self._copy_urls).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="📁 Open Downloads", command=self._open_downloads).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear", command=lambda: self.result_text.delete("1.0", tk.END)).pack(side=tk.RIGHT)
    
    def _toggle_custom_mode(self):
        """Show/hide custom mode options"""
        if self.custom_var.get():
            self.custom_frame.pack(fill=tk.X, pady=10, after=self.prompt_text.master)
        else:
            self.custom_frame.pack_forget()
    
    def _create_lyrics_tab(self):
        """Create Lyrics Generation tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="📝 Generate Lyrics")
        
        # Input
        ttk.Label(tab, text="Describe the lyrics you want:", style="Heading.TLabel").pack(anchor=tk.W)
        self.lyrics_prompt = scrolledtext.ScrolledText(tab, height=4, wrap=tk.WORD, font=("Segoe UI", 10))
        self.lyrics_prompt.pack(fill=tk.X, pady=(5, 10))
        self.lyrics_prompt.insert("1.0", "A song about adventure and discovering new places")
        
        # Generate button
        self.lyrics_btn = ttk.Button(tab, text="📝 Generate Lyrics", style="Big.TButton", command=self._generate_lyrics)
        self.lyrics_btn.pack(fill=tk.X, pady=10)
        
        # Results
        ttk.Label(tab, text="Generated Lyrics:", style="Heading.TLabel").pack(anchor=tk.W)
        self.lyrics_result = scrolledtext.ScrolledText(tab, height=20, wrap=tk.WORD, font=("Segoe UI", 10))
        self.lyrics_result.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Copy button
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X)
        ttk.Button(btn_frame, text="📋 Copy to Clipboard", command=self._copy_lyrics).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="➡️ Use in Generate", command=self._use_lyrics_in_generate).pack(side=tk.LEFT, padx=5)
    
    def _create_process_tab(self):
        """Create Audio Processing tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="🔧 Process Audio")
        
        # Task/Audio ID inputs
        id_frame = ttk.LabelFrame(tab, text="Track Identification", padding="10")
        id_frame.pack(fill=tk.X, pady=(0, 10))
        
        task_frame = ttk.Frame(id_frame)
        task_frame.pack(fill=tk.X, pady=2)
        ttk.Label(task_frame, text="Task ID:", width=12).pack(side=tk.LEFT)
        self.process_task_var = tk.StringVar()
        ttk.Entry(task_frame, textvariable=self.process_task_var, width=50).pack(side=tk.LEFT, padx=5)
        
        audio_frame = ttk.Frame(id_frame)
        audio_frame.pack(fill=tk.X, pady=2)
        ttk.Label(audio_frame, text="Audio ID:", width=12).pack(side=tk.LEFT)
        self.process_audio_var = tk.StringVar()
        ttk.Entry(audio_frame, textvariable=self.process_audio_var, width=50).pack(side=tk.LEFT, padx=5)
        
        # Actions
        actions_frame = ttk.LabelFrame(tab, text="Actions", padding="10")
        actions_frame.pack(fill=tk.X, pady=10)
        
        # Separate Vocals
        sep_frame = ttk.Frame(actions_frame)
        sep_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(sep_frame, text="🎤 Separate Vocals", command=lambda: self._process_audio("separate")).pack(side=tk.LEFT)
        self.sep_type_var = tk.StringVar(value="vocal")
        ttk.Radiobutton(sep_frame, text="2 stems (vocal/instrumental)", variable=self.sep_type_var, value="vocal").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(sep_frame, text="12 stems (all instruments)", variable=self.sep_type_var, value="stem").pack(side=tk.LEFT)
        
        # Other actions
        btn_frame = ttk.Frame(actions_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="🎬 Create Video", command=lambda: self._process_audio("video")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🔊 Convert to WAV", command=lambda: self._process_audio("wav")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Check Status", command=self._check_status).pack(side=tk.LEFT, padx=5)
        
        # Video options
        video_frame = ttk.LabelFrame(tab, text="Video Options (optional)", padding="10")
        video_frame.pack(fill=tk.X, pady=10)
        
        author_frame = ttk.Frame(video_frame)
        author_frame.pack(fill=tk.X, pady=2)
        ttk.Label(author_frame, text="Author:", width=12).pack(side=tk.LEFT)
        self.author_var = tk.StringVar()
        ttk.Entry(author_frame, textvariable=self.author_var, width=40).pack(side=tk.LEFT, padx=5)
        
        domain_frame = ttk.Frame(video_frame)
        domain_frame.pack(fill=tk.X, pady=2)
        ttk.Label(domain_frame, text="Domain:", width=12).pack(side=tk.LEFT)
        self.domain_var = tk.StringVar()
        ttk.Entry(domain_frame, textvariable=self.domain_var, width=40).pack(side=tk.LEFT, padx=5)
        
        # Process results
        ttk.Label(tab, text="Results:", style="Heading.TLabel").pack(anchor=tk.W, pady=(10, 0))
        self.process_result = scrolledtext.ScrolledText(tab, height=10, wrap=tk.WORD, font=("Consolas", 9))
        self.process_result.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _create_history_tab(self):
        """Create History tab"""
        tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab, text="📜 History")
        
        ttk.Label(tab, text="Generation History:", style="Heading.TLabel").pack(anchor=tk.W)
        
        # Treeview for history
        columns = ("Time", "Type", "Task ID", "Status")
        self.history_tree = ttk.Treeview(tab, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=150)
        
        self.history_tree.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="📋 Copy Task ID", command=self._copy_selected_task).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="🔍 Check Status", command=self._check_selected_status).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear History", command=self._clear_history).pack(side=tk.RIGHT)
    
    def _add_to_history(self, task_type: str, task_id: str, status: str = "Started"):
        """Add entry to history"""
        timestamp = time.strftime("%H:%M:%S")
        self.history_tree.insert("", 0, values=(timestamp, task_type, task_id, status))
    
    def _generate_music(self):
        """Generate music in background thread"""
        if self.is_generating:
            messagebox.showwarning("Busy", "A generation is already in progress!")
            return
        
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Required", "Please enter a prompt!")
            return
        
        if self.custom_var.get():
            if not self.style_var.get() or not self.title_var.get():
                messagebox.showwarning("Custom Mode", "Style and Title are required in custom mode!")
                return
        
        self.is_generating = True
        self.generate_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Generating music...")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", "🎵 Starting music generation...\n\n")
        
        # Run in thread
        thread = threading.Thread(target=self._generate_music_thread, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _generate_music_thread(self, prompt: str):
        """Background thread for music generation"""
        try:
            # Submit generation request
            task_id = self.api.generate_music(
                prompt=prompt,
                model=self.model_var.get(),
                custom_mode=self.custom_var.get(),
                instrumental=self.instrumental_var.get(),
                style=self.style_var.get() if self.custom_var.get() else None,
                title=self.title_var.get() if self.custom_var.get() else None,
                vocal_gender=self.vocal_var.get() if self.vocal_var.get() else None,
                negative_tags=self.negative_var.get() if self.negative_var.get() else None
            )
            
            self.current_task_id = task_id
            self._append_result(f"✓ Task created: {task_id}\n")
            self._append_result("⏳ Waiting for generation (this may take 2-3 minutes)...\n\n")
            self.root.after(0, lambda: self._add_to_history("Music", task_id, "Generating"))
            
            # Wait for completion
            start_time = time.time()
            while True:
                status = self.api.get_task_status(task_id)
                elapsed = int(time.time() - start_time)
                
                self.root.after(0, lambda e=elapsed, s=status.status.value: self.status_var.set(f"Generating... {e}s ({s})"))
                
                if status.is_complete:
                    self._append_result(f"✓ Generation complete! ({elapsed}s)\n\n")
                    
                    # Show tracks
                    for i, track in enumerate(status.tracks, 1):
                        self._append_result(f"🎵 Track {i}: {track.title or 'Untitled'}\n")
                        self._append_result(f"   Duration: {int(track.duration // 60)}:{int(track.duration % 60):02d}\n")
                        self._append_result(f"   Audio ID: {track.id}\n")
                        self._append_result(f"   URL: {track.audio_url}\n\n")
                        
                        # Download if enabled
                        if self.download_var.get() and track.audio_url:
                            try:
                                downloads_dir = ensure_downloads_dir()
                                filename = f"{track.title or 'track'}_{track.id[:8]}.mp3"
                                filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
                                output_path = downloads_dir / filename
                                
                                self.api.download_file(track.audio_url, output_path)
                                self._append_result(f"   ✓ Downloaded: {output_path}\n\n")
                            except Exception as e:
                                self._append_result(f"   ✗ Download failed: {e}\n\n")
                    
                    self.root.after(0, lambda: self._add_to_history("Music", task_id, "Complete"))
                    break
                    
                elif status.is_failed:
                    self._append_result(f"✗ Generation failed: {status.error_message}\n")
                    self.root.after(0, lambda: self._add_to_history("Music", task_id, "Failed"))
                    break
                
                if elapsed > 600:
                    self._append_result("✗ Timeout: Generation took too long\n")
                    break
                
                time.sleep(10)
            
        except Exception as e:
            self._append_result(f"\n✗ Error: {e}\n")
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.generate_btn.config(state=tk.NORMAL))
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.status_var.set("Ready"))
            self.root.after(0, self._update_credits)
    
    def _generate_lyrics(self):
        """Generate lyrics in background thread"""
        if self.is_generating:
            messagebox.showwarning("Busy", "A generation is already in progress!")
            return
        
        prompt = self.lyrics_prompt.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Input Required", "Please enter a prompt!")
            return
        
        self.is_generating = True
        self.lyrics_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Generating lyrics...")
        self.lyrics_result.delete("1.0", tk.END)
        
        thread = threading.Thread(target=self._generate_lyrics_thread, args=(prompt,))
        thread.daemon = True
        thread.start()
    
    def _generate_lyrics_thread(self, prompt: str):
        """Background thread for lyrics generation"""
        try:
            task_id = self.api.generate_lyrics(prompt)
            self.root.after(0, lambda: self._add_to_history("Lyrics", task_id, "Generating"))
            
            # Wait for completion
            start_time = time.time()
            while True:
                status = self.api.get_task_status(task_id)
                elapsed = int(time.time() - start_time)
                
                self.root.after(0, lambda e=elapsed: self.status_var.set(f"Generating lyrics... {e}s"))
                
                if status.is_complete:
                    for lyric in status.lyrics:
                        self.root.after(0, lambda t=lyric.text: self.lyrics_result.insert("1.0", t))
                    self.root.after(0, lambda: self._add_to_history("Lyrics", task_id, "Complete"))
                    break
                elif status.is_failed:
                    self.root.after(0, lambda: self.lyrics_result.insert("1.0", f"Error: {status.error_message}"))
                    break
                
                if elapsed > 300:
                    self.root.after(0, lambda: self.lyrics_result.insert("1.0", "Timeout"))
                    break
                
                time.sleep(5)
                
        except Exception as e:
            self.root.after(0, lambda: self.lyrics_result.insert("1.0", f"Error: {e}"))
        finally:
            self.is_generating = False
            self.root.after(0, lambda: self.lyrics_btn.config(state=tk.NORMAL))
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def _process_audio(self, action: str):
        """Process audio (separate, video, wav)"""
        task_id = self.process_task_var.get().strip()
        audio_id = self.process_audio_var.get().strip()
        
        if not task_id or not audio_id:
            messagebox.showwarning("Input Required", "Please enter both Task ID and Audio ID!")
            return
        
        self.progress.start()
        self.status_var.set(f"Processing: {action}...")
        self.process_result.delete("1.0", tk.END)
        
        thread = threading.Thread(target=self._process_audio_thread, args=(action, task_id, audio_id))
        thread.daemon = True
        thread.start()
    
    def _process_audio_thread(self, action: str, task_id: str, audio_id: str):
        """Background thread for audio processing"""
        try:
            if action == "separate":
                sep_type = SeparationType.SPLIT_STEM if self.sep_type_var.get() == "stem" else SeparationType.SEPARATE_VOCAL
                new_task_id = self.api.separate_vocals(task_id, audio_id, sep_type)
                self._append_process_result(f"✓ Vocal separation started: {new_task_id}\n")
                
            elif action == "video":
                author = self.author_var.get() or None
                domain = self.domain_var.get() or None
                new_task_id = self.api.create_video(task_id, audio_id, author, domain)
                self._append_process_result(f"✓ Video creation started: {new_task_id}\n")
                
            elif action == "wav":
                new_task_id = self.api.convert_to_wav(task_id, audio_id)
                self._append_process_result(f"✓ WAV conversion started: {new_task_id}\n")
            
            self.root.after(0, lambda: self._add_to_history(action.title(), new_task_id, "Processing"))
            self._append_process_result("\nUse 'Check Status' with the new Task ID to get results.\n")
            
        except Exception as e:
            self._append_process_result(f"✗ Error: {e}\n")
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.status_var.set("Ready"))
    
    def _check_status(self):
        """Check task status"""
        task_id = self.process_task_var.get().strip()
        if not task_id:
            messagebox.showwarning("Input Required", "Please enter a Task ID!")
            return
        
        try:
            status = self.api.get_task_status(task_id)
            self.process_result.delete("1.0", tk.END)
            self.process_result.insert("1.0", f"Task: {task_id}\n")
            self.process_result.insert(tk.END, f"Status: {status.status.value}\n\n")
            
            if status.tracks:
                for i, track in enumerate(status.tracks, 1):
                    self.process_result.insert(tk.END, f"Track {i}: {track.title}\n")
                    self.process_result.insert(tk.END, f"  URL: {track.audio_url}\n\n")
            
            if status.error_message:
                self.process_result.insert(tk.END, f"Error: {status.error_message}\n")
                
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def _append_result(self, text: str):
        """Thread-safe append to result text"""
        self.root.after(0, lambda: self.result_text.insert(tk.END, text))
        self.root.after(0, lambda: self.result_text.see(tk.END))
    
    def _append_process_result(self, text: str):
        """Thread-safe append to process result text"""
        self.root.after(0, lambda: self.process_result.insert(tk.END, text))
    
    def _copy_urls(self):
        """Copy audio URLs to clipboard"""
        text = self.result_text.get("1.0", tk.END)
        urls = [line.split("URL: ")[1].strip() for line in text.split("\n") if "URL: " in line]
        if urls:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(urls))
            messagebox.showinfo("Copied", f"Copied {len(urls)} URL(s) to clipboard!")
        else:
            messagebox.showinfo("No URLs", "No URLs found to copy.")
    
    def _copy_lyrics(self):
        """Copy lyrics to clipboard"""
        text = self.lyrics_result.get("1.0", tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Copied", "Lyrics copied to clipboard!")
    
    def _use_lyrics_in_generate(self):
        """Copy lyrics to generate tab prompt"""
        text = self.lyrics_result.get("1.0", tk.END).strip()
        if text:
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", text)
            self.custom_var.set(True)
            self._toggle_custom_mode()
            self.notebook.select(0)  # Switch to generate tab
            messagebox.showinfo("Ready", "Lyrics added to prompt. Enable custom mode and set style/title!")
    
    def _open_downloads(self):
        """Open downloads folder"""
        downloads_dir = ensure_downloads_dir()
        import os
        os.startfile(downloads_dir)
    
    def _copy_selected_task(self):
        """Copy selected task ID from history"""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            task_id = item["values"][2]
            self.root.clipboard_clear()
            self.root.clipboard_append(task_id)
            messagebox.showinfo("Copied", f"Task ID copied: {task_id}")
    
    def _check_selected_status(self):
        """Check status of selected task from history"""
        selection = self.history_tree.selection()
        if selection:
            item = self.history_tree.item(selection[0])
            task_id = item["values"][2]
            self.process_task_var.set(task_id)
            self.notebook.select(2)  # Switch to process tab
            self._check_status()
    
    def _clear_history(self):
        """Clear history"""
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)
    
    def run(self):
        """Start the GUI"""
        self.root.mainloop()


def main():
    """Entry point"""
    app = SunoGUI()
    app.run()


if __name__ == "__main__":
    main()
