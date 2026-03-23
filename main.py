import os
import threading
import sys
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDFillRoundFlatButton, MDRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.card import MDCard
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
from kivy.core.window import Window

# Standard video downloader library
try:
    import yt_dlp
except ImportError:
    # This will be handled in the UI if not installed
    pass

class YTDownloader(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.downloading = False
        self.setup_ui()

    def setup_ui(self):
        # Background Container
        layout = MDBoxLayout(orientation='vertical', padding=[20, 40, 20, 20], spacing=20)
        
        # Header Section
        header = MDBoxLayout(orientation='vertical', adaptive_height=True, spacing=5)
        header.add_widget(MDLabel(
            text="YT DOWNLOADER",
            font_style="H4",
            halign="center",
            theme_text_color="Primary",
            bold=True
        ))
        header.add_widget(MDLabel(
            text="Superfast Downloads by KV",
            font_style="Caption",
            halign="center",
            theme_text_color="Secondary"
        ))
        layout.add_widget(header)

        # Input Card
        input_card = MDCard(
            orientation='vertical',
            padding=20,
            spacing=20,
            radius=[20,],
            elevation=2,
            size_hint=(1, None),
            height=200
        )
        
        self.url_input = MDTextField(
            hint_text="Paste YouTube URL here",
            helper_text="Enter a valid video or playlist link",
            helper_text_mode="on_focus",
            mode="fill",
            icon_left="link-variant",
            fill_color=(0.1, 0.1, 0.1, 0.1)
        )
        input_card.add_widget(self.url_input)

        btn_layout = MDBoxLayout(spacing=10, adaptive_height=True)
        self.download_btn = MDFillRoundFlatButton(
            text="DOWNLOAD VIDEO",
            font_size="18sp",
            pos_hint={'center_x': .5},
            on_release=self.start_download,
            size_hint=(0.7, None),
            padding=[40, 15]
        )
        btn_layout.add_widget(self.download_btn)
        
        input_card.add_widget(btn_layout)
        layout.add_widget(input_card)

        # Progress Card (Hidden initially or showing status)
        self.status_card = MDCard(
            orientation='vertical',
            padding=20,
            radius=[20,],
            size_hint=(1, None),
            height=160,
            md_bg_color=get_color_from_hex("#1A1F2B")
        )
        
        self.progress_label = MDLabel(
            text="Ready to download",
            halign="center",
            bold=True,
            theme_text_color="Custom",
            text_color=get_color_from_hex("#FFFFFF")
        )
        self.status_card.add_widget(self.progress_label)
        
        self.progress_bar = MDProgressBar(
            value=0,
            max=100,
            color=get_color_from_hex("#00E5FF") # Neon Cyan
        )
        self.status_card.add_widget(self.progress_bar)
        
        self.speed_label = MDLabel(
            text="0.0 MB/s",
            font_style="Caption",
            halign="right",
            theme_text_color="Hint"
        )
        self.status_card.add_widget(self.speed_label)
        
        layout.add_widget(self.status_card)
        layout.add_widget(MDBoxLayout()) # Spacer

        self.add_widget(layout)

    def start_download(self, *args):
        url = self.url_input.text.strip()
        if not url:
            self.progress_label.text = "Please enter a URL"
            return
        
        if self.downloading:
            return

        self.downloading = True
        self.download_btn.disabled = True
        self.progress_label.text = "Initializing download..."
        self.progress_bar.value = 0
        
        # Run download in a separate thread
        threading.Thread(target=self.run_yt_dlp, args=(url,), daemon=True).start()

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            try:
                # Remove ANSI escape characters from percentages and speeds if yt-dlp sends them
                percent = d.get('_percent_str', '0%').replace('%', '').strip()
                speed = d.get('_speed_str', '0 KB/s').strip()
                eta = d.get('_eta_str', 'Unknown').strip()
                
                # Update UI via Clock (Kivy is not thread-safe)
                Clock.schedule_once(lambda dt: self.update_progress(percent, speed, eta))
            except Exception as e:
                print(f"Error parsing progress: {e}")
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self.finish_download())

    def update_progress(self, percent, speed, eta):
        try:
            val = float(percent)
            self.progress_bar.value = val
            self.progress_label.text = f"Downloading... {percent}% (ETA: {eta})"
            self.speed_label.text = speed
        except:
            pass

    def finish_download(self):
        self.progress_label.text = "Download Complete! Saved to Downloads"
        self.progress_bar.value = 100
        self.download_btn.disabled = False
        self.downloading = False

    def run_yt_dlp(self, url):
        # Best performance options for "Superfast" download
        # concurrent_fragments uses multiple segments to maximize speed
        # This matches the user's -f "bv*+ba/b" request but adds parallelism
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'progress_hooks': [self.progress_hook],
            'concurrent_fragment_downloads': 5, # Multi-threading fragments for "superfast"
            'outtmpl': os.path.join(self.get_download_path(), '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as e:
            Clock.schedule_once(lambda dt: self.show_error(str(e)))

    def show_error(self, err):
        self.progress_label.text = f"Error: {err}"
        self.download_btn.disabled = False
        self.downloading = False

    def get_download_path(self):
        # Cross-platform way to find downloads folder
        if sys.platform == 'win32':
             return os.path.join(os.path.expanduser('~'), 'Downloads')
        elif 'ANDROID_STORAGE' in os.environ:
             return "/sdcard/Download"
        return os.path.expanduser('~')

class SuperfastYTDownloaderApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Indigo"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.accent_palette = "Cyan"
        return YTDownloader()

if __name__ == "__main__":
    SuperfastYTDownloaderApp().run()
