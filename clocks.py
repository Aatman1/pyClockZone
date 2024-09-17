import sys
import io
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                                QLineEdit, QLabel, QListWidget, QGraphicsView, QGraphicsScene, QFrame)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter, QFont, QPixmap, QImage, QIcon
from datetime import datetime
import math
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pycountry
import geopandas as gpd
import matplotlib.pyplot as plt

try:
    import requests
except ImportError as e:
    print(f"Error importing requests: {e}")
    sys.exit(1)

class CountryShapeWidget(QLabel):
    world = None  # Define world attribute as a class variable

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(100, 100)
        self.country_code = ""
        self.setStyleSheet("border-radius: 10px; background-color: #2C2C2C;")

    def update_country(self, country_code):
        if country_code != self.country_code:
            self.country_code = country_code
            country = pycountry.countries.get(alpha_2=country_code)
            country_name = country.name.replace(' ', '-').replace(',', '')
            
            print(f"regular name: {country_name}")

            # Try to download the image using the regular country name
            url = f"https://teuteuf-dashboard-assets.pages.dev/data/common/country-shapes/{country_code}.svg"
            flag_url = f"https://flagicons.lipis.dev/flags/4x3/{country_code}.svg"
            try:
                response = requests.get(url)
                flag_response = requests.get(flag_url)
                if response.status_code == 200 and flag_response.status_code == 200:
                    # If the regular country name works, use it
                    img_data = response.content
                    flag_img_data = flag_response.content
                    pixmap = QPixmap()
                    pixmap.loadFromData(img_data)
                    flag_pixmap = QPixmap()
                    flag_pixmap.loadFromData(flag_img_data)
                    self.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.flag_pixmap = flag_pixmap.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    
                    pixmap.loadFromData(flag_img_data)
                    self.parent().flag_label.setPixmap(self.flag_pixmap)  # Set the flag pixmap to the flag_label
                    self.update()
                else:
                    print(f"Failed to download image for {country_code}. Status code: {response.status_code}")
                    self.clear()
            except Exception as e:
                print(f"Error updating shape for {country_code}: {e}")
                self.clear()
                
    def update_shape(self):
        if not self.country_code or self.world is None:
            self.clear()
            return

        # Get the country shape
        country = self.world[self.world['ISO_A2'] == self.country_code]
        
        if country.empty:
            self.clear()
            return

        # Create a figure and axis
        fig, ax = plt.subplots(figsize=(2, 2))
        
        # Plot the country shape
        country.plot(ax=ax, color='white', edgecolor='#8553ad')  # Change edgecolor to #8553ad
        
        # Remove axis and set tight layout
        ax.axis('off')
        plt.tight_layout()
        
        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        
        # Create QPixmap from the buffer
        buf.seek(0)
        img = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(img)
        
        # Set the pixmap to the label
        self.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

class ClockWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedSize(150, 150)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.location_abbr = ""
        self.country_code = ""
        self.setStyleSheet("border-radius: 10px; background-color: #2C2C2C;")

    def update_time(self, time, location_abbr, country_code):
        self.scene.clear()
        self.location_abbr = location_abbr
        self.country_code = country_code
        
        bg_color = QColor("#2C2C2C")
        fg_color = QColor("#FFFFFF")
        
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
        self.draw_hand(time.minute * 6, 55, 2, QColor("#66B2FF"))  # Minute hand
        self.draw_hand(time.second * 6, 60, 1, QColor("#FF6666"))  # Second hand

        # Add location abbreviation and flag
        abbr_text = self.scene.addText(f"{self.location_abbr} {self.get_flag_emoji(self.country_code)}", QFont("Arial", 18, QFont.Weight.Bold))  # Increase font size to 18
        abbr_text.setDefaultTextColor(fg_color)
        abbr_text.setPos(70 - abbr_text.boundingRect().width() / 2, 40)

    def draw_hand(self, angle, length, width, color):
        x = 70 + length * math.sin(math.radians(angle))
        y = 70 - length * math.cos(math.radians(angle))
        self.scene.addLine(70, 70, x, y, QPen(color, width))

    def get_flag_emoji(self, country_code):
        if country_code:
            return ''.join(chr(ord(c.upper()) + 127397) for c in country_code)
        return ''
class LocationSection(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)  # Change to QHBoxLayout
        self.clock = ClockWidget()
        self.country_shape = CountryShapeWidget()
        self.flag_label = QLabel()  # Add a QLabel to display the flag
        self.flag_label.setFixedSize(50, 50)  # Set fixed size to 50x50
        self.info_label = QLabel()
        self.info_label.setFont(QFont("Arial", 14))  # Increase font size to 14
        self.info_label.setStyleSheet("color: #FFFFFF;")
        self.layout.addWidget(self.clock)
        self.layout.addWidget(self.country_shape)
        self.layout.addWidget(self.flag_label)
        self.layout.addWidget(self.info_label)
        self.setFrameShape(QFrame.Shape.Box)
        self.setStyleSheet("QFrame { border-radius: 15px; background-color: #1E1E1E; }")
        self.layout.setContentsMargins(10, 10, 10, 10)  # Add margins to the layout
        self.layout.setSpacing(10)  # Add spacing between widgets

class WorldClockComparison(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("World Clock Comparison")
        self.setGeometry(100, 100, 1000, 600)
        icon = QIcon("Wclock.png")
        self.setWindowIcon(icon)
        self.setStyleSheet("""
            QMainWindow, QWidget { background-color: #121212; color: #FFFFFF; }
            QLineEdit, QPushButton, QListWidget { 
                font-size: 14px; 
                padding: 5px; 
                border-radius: 5px;
                background-color: #2C2C2C;
                color: #FFFFFF;
                border: 1px solid #3A3A3A;
            }
            QPushButton { 
                background-color: #0D47A1; 
                font-weight: bold; 
            }
            QPushButton:hover { background-color: #1565C0; }
            QListWidget::item { padding: 5px; }
            QListWidget::item:selected { background-color: #1E1E1E; }
        """)

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

        # self.location_list = QListWidget()
        # self.location_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        # self.location_list.itemChanged.connect(self.update_location_order)
        # self.layout.addWidget(self.location_list)

        # self.remove_button = QPushButton("Remove Selected Location")
        # self.remove_button.clicked.connect(self.remove_location)
        # self.layout.addWidget(self.remove_button)

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

    def update_times(self):
        if not self.location_sections:
            return

        times = []
        for section in self.location_sections:
            city, timezone_str, lat, lon, country_code = section.location_info
            tz = pytz.timezone(timezone_str)
            current_time = datetime.now(tz)
            utc_time = current_time.astimezone(pytz.UTC)

            times.append((city, current_time, timezone_str, utc_time, country_code))
            section.clock.update_time(current_time, city[:3].upper(), country_code)
            section.country_shape.update_country(country_code)

        times.sort(key=lambda x: x[1])

        for i, (city, time, timezone_str, utc_time, country_code) in enumerate(times):
            time_format = "%Y-%m-%d %H:%M:%S" if self.use_24_hour else "%Y-%m-%d %I:%M:%S %p"
            time_str = time.strftime(time_format)
            info_text = f"{city} ({timezone_str})\n{time_str}"

            if i > 0:
                prev_city, prev_time, _, _, _ = times[i-1]
                time_diff = time.replace(tzinfo=None) - prev_time.replace(tzinfo=None)
                total_minutes = int(time_diff.total_seconds() / 60)
                hours, minutes = divmod(abs(total_minutes), 60)
                direction = "ahead of" if total_minutes > 0 else "behind"
                diff_str = f"{hours}h {minutes}m {direction} {prev_city}"
                info_text += f"\nΔ {diff_str}"

            section.info_label.setText(info_text)

    def toggle_time_format(self):
        self.use_24_hour = not self.use_24_hour
        self.format_toggle.setText("12 hr" if self.use_24_hour else "24 hr")
        self.update_times()

    def add_location(self):
        city = self.location_input.text().strip().capitalize()
        if city:
            try:
                location = self.geolocator.geocode(city)
                if location:
                    timezone_str = self.tf.timezone_at(lng=location.longitude, lat=location.latitude)
                    if timezone_str:
                        country = self.geolocator.reverse((location.latitude, location.longitude)).raw['address']['country_code']
                        country_code = country if country else ''
                        section = LocationSection()
                        section.location_info = (city, timezone_str, location.latitude, location.longitude, country_code)
                        self.location_sections.append(section)
                        self.clocks_layout.addWidget(section)
                        self.location_input.clear()
                    else:
                        self.show_error(f"Could not determine timezone for {city}")
                else:
                    self.show_error(f"Could not find location: {city}")
            except Exception as e:
                self.show_error(f"Error adding location: {str(e)}")

    def remove_location(self, section):
        self.location_sections.remove(section)
        self.clocks_layout.removeWidget(section)
        section.deleteLater()
        self.update_times()

    def update_location_order(self):
        for i, section in enumerate(self.location_sections):
            self.clocks_layout.removeWidget(section)
            self.clocks_layout.insertWidget(i, section)
        self.update_times()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            for section in self.location_sections:
                if section.underMouse():
                    self.remove_location(section)
                    break
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for section in self.location_sections:
                if section.hasFocus():
                    self.remove_location(section)
                    break
        else:
            super().keyPressEvent(event)

    def show_error(self, message):
        error_label = QLabel(message)
        error_label.setStyleSheet("color: #FF6666; font-size: 14px; font-weight: bold;")
        self.layout.addWidget(error_label)
        QTimer.singleShot(3000, error_label.deleteLater)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorldClockComparison()
    window.show()
    sys.exit(app.exec())