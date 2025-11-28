import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini Audio Transcription")
        self.root.geometry("600x450")
        
        # Variables
        self.api_key_var = tk.StringVar(value=os.getenv("GEMINI_API_KEY", ""))
        self.file_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.model_var = tk.StringVar(value="gemini-2.5-pro")
        
        self.create_widgets()

    def create_widgets(self):
        # API Key Section
        api_frame = ttk.LabelFrame(self.root, text="API Key Settings", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side="left")
        self.api_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=40)
        self.api_entry.pack(side="left", padx=5, expand=True, fill="x")
        
        # File Selection Section
        file_frame = ttk.LabelFrame(self.root, text="Audio File", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(file_frame, text="Select File", command=self.select_file).pack(side="left")
        ttk.Label(file_frame, textvariable=self.file_path_var, wraplength=400).pack(side="left", padx=10)
        
        # Model Selection Section
        model_frame = ttk.LabelFrame(self.root, text="Model Selection", padding=10)
        model_frame.pack(fill="x", padx=10, pady=5)
        
        models = [
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-3-pro"
        ]
        self.model_combo = ttk.Combobox(model_frame, textvariable=self.model_var, values=models, state="readonly")
        self.model_combo.pack(fill="x")

        # Action Section
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x", padx=10, pady=5)
        
        self.transcribe_btn = ttk.Button(action_frame, text="Start Transcription", command=self.start_transcription_thread)
        self.transcribe_btn.pack(fill="x", pady=5)
        
        # Status Section
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, wraplength=550)
        self.status_label.pack(fill="both", expand=True)

    def select_file(self):
        filetypes = (
            ('Audio files', '*.mp3 *.m4a *.wav'),
            ('All files', '*.*')
        )
        filename = filedialog.askopenfilename(
            title='Open an audio file',
            initialdir='/',
            filetypes=filetypes
        )
        if filename:
            self.file_path_var.set(filename)
            self.status_var.set(f"Selected: {os.path.basename(filename)}")

    def start_transcription_thread(self):
        if not self.api_key_var.get():
            messagebox.showerror("Error", "Please enter a Gemini API Key")
            return
        if not self.file_path_var.get():
            messagebox.showerror("Error", "Please select an audio file")
            return
            
        self.transcribe_btn.config(state="disabled")
        threading.Thread(target=self.run_transcription, daemon=True).start()

    def run_transcription(self):
        try:
            api_key = self.api_key_var.get()
            file_path = self.file_path_var.get()
            model_name = self.model_var.get()
            
            genai.configure(api_key=api_key)
            
            self.status_var.set("Uploading audio file...")
            audio_file = genai.upload_file(file_path)
            
            # Wait for processing if necessary (usually fast for audio)
            while audio_file.state.name == "PROCESSING":
                time.sleep(1)
                audio_file = genai.get_file(audio_file.name)
                
            if audio_file.state.name == "FAILED":
                raise Exception("Audio file processing failed on server.")

            self.status_var.set(f"Transcribing with {model_name}...")
            
            model = genai.GenerativeModel(model_name)
            
            prompt = (
                "音声データを一字一句、聞こえたまま忠実に文字起こししてください。\n"
                "整文、要約、言い換え、話者分離のタグ付けは一切行わないでください。\n"
                "フィラー（えー、あー等）も発話されている通りに記述してください。"
            )
            
            response = model.generate_content([prompt, audio_file])
            
            # Save to file
            base_name = os.path.splitext(file_path)[0]
            output_path = f"{base_name}.txt"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(response.text)
                
            self.status_var.set(f"Success! Saved to:\n{output_path}")
            messagebox.showinfo("Success", f"Transcription saved to:\n{output_path}")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        finally:
            self.root.after(0, lambda: self.transcribe_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
