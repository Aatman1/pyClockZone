import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QLineEdit, QLabel, QListWidget, QGraphicsView, QGraphicsScene)
from PyQt6.QtCore import QTimer, Qt, QRectF, QPointF
from PyQt6.QtGui import QPen, QBrush, QColor, QPainter
from datetime import datetime
import math
import pytz
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

class ClockWidget(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setFixedSize(150, 150)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def update_time(self, time):
        self.scene.clear()
        
        # Draw clock face
        self.scene.addEllipse(QRectF(0, 0, 140, 140), QPen(Qt.GlobalColor.black), QBrush(Qt.GlobalColor.white))
        
        # Draw hour marks
        for i in range(12):
            angle = i * 30
            x1 = 70 + 65 * math.cos(math.radians(angle))
            y1 = 70 + 65 * math.sin(math.radians(angle))
            x2 = 70 + 60 * math.cos(math.radians(angle))
            y2 = 70 + 60 * math.sin(math.radians(angle))
            self.scene.addLine(x1, y1, x2, y2, QPen(Qt.GlobalColor.black))
        
        # Draw hands
        self.draw_hand(time.hour % 12 * 30 + time.minute / 2, 40, 3, Qt.GlobalColor.black)  # Hour hand
        self.draw_hand(time.minute * 6, 55, 2, Qt.GlobalColor.blue)  # Minute hand
        self.draw_hand(time.second * 6, 60, 1, Qt.GlobalColor.red)  # Second hand

    def draw_hand(self, angle, length, width, color):
        x = 70 + length * math.sin(math.radians(angle))
        y = 70 - length * math.cos(math.radians(angle))
        self.scene.addLine(70, 70, x, y, QPen(color, width))

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

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.location_input)
        input_layout.addWidget(self.add_button)
        self.layout.addLayout(input_layout)

        self.location_list = QListWidget()
        self.layout.addWidget(self.location_list)

        self.clocks_layout = QHBoxLayout()
        self.layout.addLayout(self.clocks_layout)

        self.time_display = QLabel()
        self.time_display.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.addWidget(self.time_display)

        self.locations = []
        self.clocks = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_times)
        self.timer.start(1000)  # Update every second

        self.geolocator = Nominatim(user_agent="world_clock_comparison")
        self.tf = TimezoneFinder()

    def add_location(self):
        city = self.location_input.text().strip()
        if city and city not in [loc[0] for loc in self.locations]:
            try:
                location = self.geolocator.geocode(city)
                if location:
                    timezone_str = self.tf.timezone_at(lng=location.longitude, lat=location.latitude)
                    if timezone_str:
                        self.locations.append((city, timezone_str))
                        self.location_list.addItem(f"{city} ({timezone_str})")
                        self.location_input.clear()
                        
                        # Add new clock
                        clock = ClockWidget()
                        self.clocks_layout.addWidget(clock)
                        self.clocks.append(clock)
                    else:
                        self.time_display.setText(f"Could not determine timezone for {city}")
                else:
                    self.time_display.setText(f"Could not find location: {city}")
            except Exception as e:
                self.time_display.setText(f"Error adding location: {str(e)}")

    def update_times(self):
        if not self.locations:
            self.time_display.setText("No locations added")
            return

        times = []
        for (city, timezone_str), clock in zip(self.locations, self.clocks):
            tz = pytz.timezone(timezone_str)
            current_time = datetime.now(tz)
            times.append((city, current_time, timezone_str))
            clock.update_time(current_time)

        times.sort(key=lambda x: x[1])
        
        time_diff_text = []
        for i, (city, time, timezone_str) in enumerate(times):
            time_str = time.strftime("%Y-%m-%d %H:%M:%S")
            time_diff_text.append(f"{city} ({timezone_str}): {time_str}")
            
            if i > 0:
                prev_city, prev_time, prev_timezone = times[i-1]
                
                time_diff = time.replace(tzinfo=None) - prev_time.replace(tzinfo=None)
                total_minutes = int(time_diff.total_seconds() / 60)
                hours, minutes = divmod(abs(total_minutes), 60)
                direction = "ahead of" if total_minutes > 0 else "behind"
                
                diff_str = f"{hours}h {minutes}m {direction}"
                time_diff_text.append(f"  Δ {diff_str} {prev_city}")

        self.time_display.setText("\n".join(time_diff_text))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WorldClockComparison()
    window.show()
    sys.exit(app.exec())