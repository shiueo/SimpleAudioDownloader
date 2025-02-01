import sys
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QTextEdit, QComboBox, QLabel, QFileDialog, QProgressBar
)
from PySide6.QtCore import QThread, Signal, Qt
from yt_dlp import YoutubeDL


# 다운로드를 백그라운드에서 실행하기 위한 스레드 클래스
class DownloadThread(QThread):
    log_signal = Signal(str)  # 로그 출력을 위한 시그널
    progress_signal = Signal(float)  # 진행률 출력을 위한 시그널

    def __init__(self, url, options):
        super().__init__()
        self.url = url
        self.options = options

    def run(self):
        try:
            def progress_hook(d):
                if d['status'] == 'downloading':
                    progress = d.get('_percent_str', '0%').strip('%')
                    self.progress_signal.emit(float(progress))

            self.options['progress_hooks'] = [progress_hook]
            with YoutubeDL(self.options) as ydl:
                ydl.download([self.url])
            self.log_signal.emit("다운로드 완료!")
        except Exception as e:
            self.log_signal.emit(f"오류 발생: {str(e)}")


# 메인 윈도우 클래스
class YouTubeDownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video/Audio Downloader")
        self.setGeometry(100, 100, 600, 400)

        # 메인 위젯 및 레이아웃 설정
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # 플랫폼 선택
        self.platform_label = QLabel("플랫폼 선택:", self)
        self.layout.addWidget(self.platform_label)

        self.platform_combo = QComboBox(self)
        self.platform_combo.addItem("YouTube")
        self.platform_combo.addItem("SoundCloud")
        self.platform_combo.addItem("Vimeo")
        self.layout.addWidget(self.platform_combo)

        # URL 입력 필드
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("URL을 입력하세요...")
        self.layout.addWidget(self.url_input)

        # 다운로드 옵션 선택
        self.option_label = QLabel("다운로드 옵션:", self)
        self.layout.addWidget(self.option_label)

        self.option_combo = QComboBox(self)
        self.option_combo.addItem("고화질 동영상 (MP4)")
        self.option_combo.addItem("오디오만 (MP3)")
        self.layout.addWidget(self.option_combo)

        # 다운로드 폴더 선택
        self.folder_button = QPushButton("다운로드 폴더 선택", self)
        self.folder_button.clicked.connect(self.select_folder)
        self.layout.addWidget(self.folder_button)

        self.folder_label = QLabel("선택된 폴더: 없음", self)
        self.layout.addWidget(self.folder_label)

        # 진행률 표시
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.progress_bar)

        # 다운로드 버튼
        self.download_button = QPushButton("다운로드 시작", self)
        self.download_button.clicked.connect(self.start_download)
        self.layout.addWidget(self.download_button)

        # 로그 출력 창
        self.log_output = QTextEdit(self)
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        # 다운로드 폴더 초기화
        self.download_folder = None

    def select_folder(self):
        # 폴더 선택 다이얼로그 열기
        folder = QFileDialog.getExistingDirectory(self, "다운로드 폴더 선택")
        if folder:
            self.download_folder = folder
            self.folder_label.setText(f"선택된 폴더: {folder}")

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_output.append("URL을 입력하세요.")
            return

        if not self.download_folder:
            self.log_output.append("다운로드 폴더를 선택하세요.")
            return

        # 선택한 플랫폼과 옵션에 따라 yt-dlp 설정
        selected_platform = self.platform_combo.currentText()
        selected_option = self.option_combo.currentText()

        options = {
            'outtmpl': os.path.join(self.download_folder, '%(title)s.%(ext)s'),
        }

        if selected_platform == "YouTube":
            if selected_option == "고화질 동영상 (MP4)":
                options.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })
            elif selected_option == "오디오만 (MP3)":
                options.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                })
        elif selected_platform == "SoundCloud":
            if selected_option == "고화질 동영상 (MP4)":
                self.log_output.append("SoundCloud은 오디오만 지원됩니다. 오디오로 다운로드합니다.")
                options.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                })
            elif selected_option == "오디오만 (MP3)":
                options.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                })
        elif selected_platform == "Vimeo":
            if selected_option == "고화질 동영상 (MP4)":
                options.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })
            elif selected_option == "오디오만 (MP3)":
                options.update({
                    'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                })

        # 다운로드 스레드 시작
        self.log_output.append(f"다운로드 시작: {url} ({selected_platform})")
        self.download_thread = DownloadThread(url, options)
        self.download_thread.log_signal.connect(self.log_output.append)
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.start()

    def update_progress(self, progress):
        self.progress_bar.setValue(int(progress))


# 애플리케이션 실행
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = YouTubeDownloaderApp()
    window.show()
    sys.exit(app.exec())