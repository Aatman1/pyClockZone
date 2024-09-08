import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QLineEdit, QLabel, QListWidget, QGraphicsView, QGraphicsScene, QFrame)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from datetime import datetime
import math
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from suntime import Sun

class ClockWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedSize(150, 150)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.is_dark_mode = False

    def update_time(self, time, is_dark_mode):
        self.scene.clear()
        self.is_dark_mode = is_dark_mode
        
        # Set colors based on mode
        bg_color = Qt.GlobalColor.black if is_dark_mode else Qt.GlobalColor.white
        fg_color = Qt.GlobalColor.white if is_dark_mode else Qt.GlobalColor.black
        
        # Draw clock face
        self.scene.addEllipse(QRectF(0, 0, 140, 140), QPen(fg_color), QBrush(bg_color))
        
        # Draw hour marks
        for i in range(12):
            angle = i * 30
            x1 = 70 + 65 * math.cos(math.radians(angle))
            y1 = 70 + 65 * math.sin(math.radians(angle))
            x2 = 70 + 60 * math.cos(math.radians(angle))
            y2 = 70 + 60 * math.sin(math.radians(angle))
            self.scene.addLine(x1, y1, x2, y2, QPen(fg_color))
        
        # Draw hands
        self.draw_hand(time.hour % 12 * 30 + time.minute / 2, 40, 3, fg_color)  # Hour hand
        self.draw_hand(time.minute * 6, 55, 2, QColor(100, 100, 255))  # Minute hand
        self.draw_hand(time.second * 6, 60, 1, Qt.GlobalColor.red)  # Second hand

    def draw_hand(self, angle, length, width, color):
        x = 70 + length * math.sin(math.radians(angle))
        y = 70 - length * math.cos(math.radians(angle))
        self.scene.addLine(70, 70, x, y, QPen(color, width))

class LocationSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.clock = ClockWidget()
        self.info_label = QLabel()
        self.layout.addWidget(self.clock)
        self.layout.addWidget(self.info_label)
        self.setFrameShape(QFrame.Shape.Box)

class WorldClockComparison(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("World Clock Comparison")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city name (e.g., 'London', 'New York', 'Tokyo')")
        self.add_button = QPushButton("Add Location")
        self.add_button.clicked.connect(self.add_location)

        self.format_toggle = QPushButton("12/24 Hr")
        self.format_toggle.clicked.connect(self.toggle_time_format)
        self.use_24_hour = False

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.location_input)
        input_layout.addWidget(self.add_button)
        input_layout.addWidget(self.format_toggle)
        self.layout.addLayout(input_layout)

        self.location_list = QListWidget()
        self.location_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.location_list.itemChanged.connect(self.update_location_order)
        self.layout.addWidget(self.location_list)

        self.remove_button = QPushButton("Remove Selected Location")
        self.remove_button.clicked.connect(self.remove_location)
        self.layout.addWidget(self.remove_button)

        self.clocks_layout = QVBoxLayout()
        self.layout.addLayout(self.clocks_layout)

        self.locations = []
        self.location_sections = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)  # Update every second

        self.geolocator = Nominatim(user_agent="world_clock_comparison")
        self.tf = TimezoneFinder()

    def add_location(self):
        city = self.location_input.text().strip().capitalize()
        if city and city not in [loc[0] for loc in self.locations]:
            try:
                location = self.geolocator.geocode(city)
                if location:
                    timezone_str = self.tf.timezone_at(lng=location.longitude, lat=location.latitude)
                    if timezone_str:
                        self.locations.append((city, timezone_str, location.latitude, location.longitude))
                        self.location_list.addItem(f"{city} ({timezone_str})")
                        self.location_input.clear()
                        
                        # Add new location section
                        section = LocationSection()
                        self.clocks_layout.addWidget(section)
                        self.location_sections.append(section)
                    else:
                        self.show_error(f"Could not determine timezone for {city}")
                else:
                    self.show_error(f"Could not find location: {city}")
            except Exception as e:
                self.show_error(f"Error adding location: {str(e)}")

    def update_times(self):
        if not self.locations:
            return

        times = []
        for (city, timezone_str, lat, lon), section in zip(self.locations, self.location_sections):
            tz = pytz.timezone(timezone_str)
            current_time = datetime.now(tz)
            utc_time = current_time.astimezone(pytz.UTC)
            
            # Calculate if it's day or night using suntime
            sun = Sun(lat, lon)
            today_sr = sun.get_local_sunrise_time(current_time.date())
            today_ss = sun.get_local_sunset_time(current_time.date())
            is_dark = current_time.time() > today_ss.time() or current_time.time() < today_sr.time()

            times.append((city, current_time, timezone_str, utc_time, is_dark))
            section.clock.update_time(current_time, is_dark)

        times.sort(key=lambda x: x[1])
        
        for i, (city, time, timezone_str, utc_time, is_dark) in enumerate(times):
            time_format = "%Y-%m-%d %H:%M:%S" if self.use_24_hour else "%Y-%m-%d %I:%M:%S %p"
            time_str = time.strftime(time_format)
            # utc_str = utc_time.strftime("%H:%M:%S UTC")
            info_text = f"{city} ({timezone_str}):\n{time_str}"
            # \n{utc_str}"
            
            if i > 0:
                prev_city, prev_time, _, _, _ = times[i-1]
                time_diff = time.replace(tzinfo=None) - prev_time.replace(tzinfo=None)
                total_minutes = int(time_diff.total_seconds() / 60)
                hours, minutes = divmod(abs(total_minutes), 60)
                direction = "ahead of" if total_minutes > 0 else "behind"
                diff_str = f"{hours}h {minutes}m {direction} {prev_city}"
                info_text += f"\nΔ {diff_str}"

            self.location_sections[i].info_label.setText(info_text)

    def toggle_time_format(self):
        self.use_24_hour = not self.use_24_hour
        self.format_toggle.setText("12 hr" if self.use_24_hour else "24 hr")
        self.update_times()

    def remove_location(self):
        current_row = self.location_list.currentRow()
        if current_row >= 0:
            self.location_list.takeItem(current_row)
            del self.locations[current_row]
            section = self.location_sections.pop(current_row)
            self.clocks_layout.removeWidget(section)
            section.deleteLater()
            self.update_times()

    def update_location_order(self):
        new_order = [self.location_list.item(i).text().split(' (')[0] for i in range(self.location_list.count())]
        self.locations = [loc for loc in self.locations if loc[0] in new_order]
        self.locations.sort(key=lambda x: new_order.index(x[0]))
        self.location_sections = [section for _, section in sorted(zip(new_order, self.location_sections), key=lambda x: new_order.index(x[0]))]
        for i, section in enumerate(self.location_sections):
            self.clocks_layout.removeWidget(section)
            self.clocks_layout.insertWidget(i, section)
        self.update_times()

    def show_error(self, message):
        error_label = QLabel(message)
        error_label.setStyleSheet("color: red")
        self.layout.addWidget(error_label)
        QTimer.singleShot(3000, error_label.deleteLater)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorldClockComparison()
    window.show()
    sys.exit(app.exec())