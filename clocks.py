import sys
import io
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QLineEdit, QLabel, QListWidget, QGraphicsView, QGraphicsScene, QFrame)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPixmap
from datetime import datetime
import math
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from suntime import Sun
import pycountry
import geopandas as gpd
import matplotlib.pyplot as plt

class CountryShapeWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.country_code = ""
        self.setStyleSheet("border-radius: 10px; background-color: white;")

    def update_country(self, country_code):
        if country_code != self.country_code:
            self.country_code = country_code
            self.update_shape()

    def update_shape(self):
        if not self.country_code:
            self.clear()
            return

        # Get country shape data
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        country = world[world['iso_a2'] == self.country_code]

        if country.empty:
            self.clear()
            return

        # Plot the country shape
        fig, ax = plt.subplots(figsize=(2, 2))
        country.plot(ax=ax, color='lightblue', edgecolor='black')
        ax.axis('off')
        plt.tight_layout()

        # Convert plot to QPixmap
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.getvalue())
        
        self.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        plt.close(fig)

class ClockWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedSize(150, 150)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.is_dark_mode = False
        self.location_abbr = ""
        self.country_code = ""

    def update_time(self, time, is_dark_mode, location_abbr, country_code):
        self.scene.clear()
        self.is_dark_mode = is_dark_mode
        self.location_abbr = location_abbr
        self.country_code = country_code
        
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

        # Add location abbreviation
        abbr_text = self.scene.addText(self.location_abbr, QFont("Arial", 10))
        abbr_text.setDefaultTextColor(fg_color)
        abbr_text.setPos(70 - abbr_text.boundingRect().width() / 2, 40)

        # Add country flag (emoji)
        flag_emoji = self.get_flag_emoji(self.country_code)
        flag_text = self.scene.addText(flag_emoji, QFont("Arial", 12))
        flag_text.setPos(70 - flag_text.boundingRect().width() / 2, 100)

    def draw_hand(self, angle, length, width, color):
        x = 70 + length * math.sin(math.radians(angle))
        y = 70 - length * math.cos(math.radians(angle))
        self.scene.addLine(70, 70, x, y, QPen(color, width))

    def get_flag_emoji(self, country_code):
        if country_code:
            # Convert country code to regional indicator symbols
            return ''.join(chr(ord(c.upper()) + 127397) for c in country_code)
        return ''  # White flag as fallback

class LocationSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.clock = ClockWidget()
        self.country_shape = CountryShapeWidget()
        self.info_label = QLabel()
        self.layout.addWidget(self.clock)
        self.layout.addWidget(self.country_shape)
        self.layout.addWidget(self.info_label)
        self.setFrameShape(QFrame.Shape.Box)

class WorldClockComparison(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("World Clock Comparison")
        self.setGeometry(100, 100, 1000, 600)  # Increased width to accommodate country shapes

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter city name (e.g., 'London', 'New York', 'Tokyo')")
        self.add_button = QPushButton("Add Location")
        self.add_button.clicked.connect(self.add_location)
        self.location_input.returnPressed.connect(self.add_button.click)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete and self.location_list.hasFocus():
            self.remove_location()
        else:
            super().keyPressEvent(event)

    def add_location(self):
        city = self.location_input.text().strip().capitalize()
        if city and city not in [loc[0] for loc in self.locations]:
            try:
                location = self.geolocator.geocode(city)
                if location:
                    timezone_str = self.tf.timezone_at(lng=location.longitude, lat=location.latitude)
                    if timezone_str:
                        country = pycountry.countries.get(alpha_2=location.raw['display_name'].split(', ')[-1])
                        country_code = country.alpha_2 if country else ''
                        self.locations.append((city, timezone_str, location.latitude, location.longitude, country_code))
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
        for (city, timezone_str, lat, lon, country_code), section in zip(self.locations, self.location_sections):
            tz = pytz.timezone(timezone_str)
            current_time = datetime.now(tz)
            utc_time = current_time.astimezone(pytz.UTC)
            
            # Calculate if it's day or night using suntime
            sun = Sun(lat, lon)
            today_sr = sun.get_local_sunrise_time(current_time.date()).astimezone(pytz.UTC).time()
            today_ss = sun.get_local_sunset_time(current_time.date()).astimezone(pytz.UTC).time()
            is_dark = utc_time.time() > today_ss or utc_time.time() < today_sr

            times.append((city, current_time, timezone_str, utc_time, is_dark, country_code))
            section.clock.update_time(current_time, is_dark, city[:3].upper(), country_code)
            section.country_shape.update_country(country_code)

        times.sort(key=lambda x: x[1])
        
        for i, (city, time, timezone_str, utc_time, is_dark, country_code) in enumerate(times):
            time_format = "%Y-%m-%d %H:%M:%S" if self.use_24_hour else "%Y-%m-%d %I:%M:%S %p"
            time_str = time.strftime(time_format)
            info_text = f"{city} ({timezone_str}):\n{time_str}"
            
            if i > 0:
                prev_city, prev_time, _, _, _, _ = times[i-1]
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