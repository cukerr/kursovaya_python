import sys
import vlc
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QSlider,
    QPushButton,
    QLabel,
    QFileDialog,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QListWidgetItem,
    QInputDialog,
)
from PyQt5.QtGui import QIcon, QPixmap


class Playlist:
    def __init__(self, name="Новый плейлист", image_path=None):
        self.name = name
        self.image_path = image_path
        self.tracks = []

    def add_track(self, track_path):
        if track_path not in self.tracks:
            self.tracks.append(track_path)

    def remove_track(self, track_path):
        if track_path in self.tracks:
            self.tracks.remove(track_path)


class AudioPlayer(QWidget):
    def __init__(self):
        super().__init__()

        # Инициализация VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.audio_file = None  # Путь к аудиофайлу
        self.is_playing = False  # Флаг воспроизведения
        self.paused = False  # Флаг паузы
        self.timer = QTimer(self)  # Таймер для обновления времени
        self.slider_moving = False  # Флаг перемещения слайдера
        self.playlists = []  # Список плейлистов
        self.current_playlist = None  # Текущий плейлист
        self.current_track_index = -1  # Индекс текущего трека

        # Настройка интерфейса
        self.setWindowTitle("Audio Player")
        self.setGeometry(100, 100, 600, 600)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Слайдер для времени
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.sliderPressed.connect(self.slider_pressed)
        self.slider.sliderReleased.connect(self.slider_released)
        self.slider.sliderMoved.connect(self.slider_moved)
        layout.addWidget(self.slider)

        # Метка для отображения текущего времени
        self.time_label = QLabel("00:00")
        layout.addWidget(self.time_label)

        # Панель кнопок (play, pause, stop)
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.play_button = QPushButton("Играть")
        self.play_button.clicked.connect(self.toggle_play_pause)
        button_layout.addWidget(self.play_button)

        self.stop_button = QPushButton("Стоп")
        self.stop_button.clicked.connect(self.stop_music)
        button_layout.addWidget(self.stop_button)

        self.open_button = QPushButton("Открыть")
        self.open_button.clicked.connect(self.open_file)
        button_layout.addWidget(self.open_button)

        # Настройка таймера
        self.timer.timeout.connect(self.update_time)
        self.timer.start(500)  # Обновляем каждые 0.5 секунды

        # Громкость
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.valueChanged.connect(self.set_volume)
        layout.addWidget(self.volume_slider)

        # Метка для отображения громкости
        self.volume_label = QLabel("Громкость: 100%")
        layout.addWidget(self.volume_label)

        # Информация о поддерживаемых типах файлов
        self.info_label = QLabel("Поддерживаемые типы файлов: .mp3, .wav, .ogg")
        layout.addWidget(self.info_label)

        # Список плейлистов
        playlist_layout = QHBoxLayout()
        layout.addLayout(playlist_layout)

        self.playlist_list = QListWidget()
        self.playlist_list.itemClicked.connect(self.select_playlist)
        playlist_layout.addWidget(self.playlist_list)

        # Кнопки для управления плейлистами
        playlist_button_layout = QVBoxLayout()
        playlist_layout.addLayout(playlist_button_layout)

        self.new_playlist_button = QPushButton("Новый плейлист")
        self.new_playlist_button.clicked.connect(self.create_playlist)
        playlist_button_layout.addWidget(self.new_playlist_button)

        self.rename_playlist_button = QPushButton("Переименовать")
        self.rename_playlist_button.clicked.connect(self.rename_playlist)
        playlist_button_layout.addWidget(self.rename_playlist_button)

        self.change_image_button = QPushButton("Изменить картинку")
        self.change_image_button.clicked.connect(self.change_playlist_image)
        playlist_button_layout.addWidget(self.change_image_button)

        # Список треков в плейлисте
        self.track_list = QListWidget()
        self.track_list.itemDoubleClicked.connect(self.play_selected_track)
        layout.addWidget(self.track_list)

        # Кнопки для управления треками
        track_button_layout = QHBoxLayout()
        layout.addLayout(track_button_layout)

        self.add_track_button = QPushButton("Добавить трек")
        self.add_track_button.clicked.connect(self.add_track_to_playlist)
        track_button_layout.addWidget(self.add_track_button)

        self.remove_track_button = QPushButton("Удалить трек")
        self.remove_track_button.clicked.connect(self.remove_track_from_playlist)
        track_button_layout.addWidget(self.remove_track_button)

        # Дизайн
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2e2e2e;
                color: white;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QSlider {
                background-color: #444;
                height: 10px;
            }
            QSlider::handle:horizontal {
                background-color: #f1f1f1;
                width: 15px;
                border-radius: 7px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QListWidget {
                background-color: #3e3e3e;
                color: white;
            }
        """
        )

    def create_playlist(self):
        name, ok = QInputDialog.getText(self, "Новый плейлист", "Введите название плейлиста:")
        if ok and name:
            playlist = Playlist(name)
            self.playlists.append(playlist)
            self.update_playlist_list()

    def rename_playlist(self):
        if self.current_playlist:
            name, ok = QInputDialog.getText(
                self, "Переименовать плейлист", "Введите новое название плейлиста:"
            )
            if ok and name:
                self.current_playlist.name = name
                self.update_playlist_list()

    def change_playlist_image(self):
        if self.current_playlist:
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            file, _ = QFileDialog.getOpenFileName(
                self,
                "Выбрать изображение",
                "",
                "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*)",
                options=options,
            )
            if file:
                self.current_playlist.image_path = file
                self.update_playlist_list()

    def update_playlist_list(self):
        self.playlist_list.clear()
        for playlist in self.playlists:
            item = QListWidgetItem(playlist.name)
            if playlist.image_path:
                pixmap = QPixmap(playlist.image_path).scaled(50, 50)
                icon = QIcon(pixmap)
                item.setIcon(icon)
            self.playlist_list.addItem(item)

    def select_playlist(self, item):
        index = self.playlist_list.row(item)
        self.current_playlist = self.playlists[index]
        self.update_track_list()

    def update_track_list(self):
        self.track_list.clear()
        if self.current_playlist:
            for track in self.current_playlist.tracks:
                from os.path import basename

                self.track_list.addItem(basename(track))

    def add_track_to_playlist(self):
        if self.current_playlist:
            options = QFileDialog.Options()
            options |= QFileDialog.ReadOnly
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Добавить треки",
                "",
                "Аудиофайлы (*.mp3 *.wav *.ogg);;Все файлы (*)",
                options=options,
            )
            for file in files:
                self.current_playlist.add_track(file)
            self.update_track_list()

    def remove_track_from_playlist(self):
        if self.current_playlist:
            selected_items = self.track_list.selectedItems()
            for item in selected_items:
                index = self.track_list.row(item)
                track_path = self.current_playlist.tracks[index]
                self.current_playlist.remove_track(track_path)
            self.update_track_list()

    def open_file(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Открыть аудиофайл",
            "",
            "Аудиофайлы (*.mp3 *.wav *.ogg);;Все файлы (*)",
            options=options,
        )
        if file:
            self.audio_file = file
            self.load_audio()
            self.set_position(0)  # Устанавливаем позицию в начало
            self.play_music()  # Запускаем воспроизведение

    def load_audio(self):
        if self.audio_file:
            media = self.instance.media_new(self.audio_file)
            self.player.set_media(media)
            self.is_playing = False
            self.paused = False
            self.play_button.setText("Играть")
            # Получаем длительность аудиофайла
            media.parse()
            self.total_length = media.get_duration() / 1000  # В секундах
            # Сбрасываем метку времени и слайдер
            self.time_label.setText("00:00")
            self.slider.setValue(0)

    def set_position(self, position):
        pos = position / 100
        self.player.set_position(pos)

    def play_music(self):
        if not self.is_playing:
            self.player.play()
            self.is_playing = True
            self.paused = False
            self.play_button.setText("Пауза")

    def stop_music(self):
        if self.is_playing or self.paused:
            self.player.stop()
            self.is_playing = False
            self.paused = False
            self.play_button.setText("Играть")

    def update_time(self):
        if self.is_playing or self.paused:
            current_time = self.player.get_time() / 1000  # В секундах
            if current_time < 0:
                current_time = 0
            if not self.slider_moving and self.total_length > 0:
                self.slider.setValue(int(current_time / self.total_length * 100))
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            self.time_label.setText(f"{minutes:02}:{seconds:02}")

    def toggle_play_pause(self):
        if self.is_playing:
            self.player.pause()
            self.is_playing = False
            self.paused = True
            self.play_button.setText("Играть")
        else:
            if self.paused:
                self.player.play()
            else:
                self.play_music()
            self.is_playing = True
            self.paused = False
            self.play_button.setText("Пауза")

    def set_volume(self):
        volume = self.volume_slider.value()
        self.player.audio_set_volume(volume)
        self.volume_label.setText(f"Громкость: {volume}%")

    def slider_pressed(self):
        self.slider_moving = True

    def slider_released(self):
        self.slider_moving = False
        self.set_position(self.slider.value())

    def slider_moved(self, position):
        # Обновляем метку времени при перемещении слайдера
        new_time = position / 100 * self.total_length
        minutes = int(new_time // 60)
        seconds = int(new_time % 60)
        self.time_label.setText(f"{minutes:02}:{seconds:02}")

    def play_selected_track(self, item):
        if self.current_playlist:
            index = self.track_list.row(item)
            self.audio_file = self.current_playlist.tracks[index]
            self.load_audio()
            self.set_position(0)
            self.play_music()
            self.play_button.setText("Пауза")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec_())
