import sys
import cv2
import argparse

from ultralytics import YOLO
import supervision as sv
import numpy as np
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QMessageBox, QGraphicsView, QSlider, QComboBox
)
import serial
import time

# Python In-built packages
from pathlib import Path
# import PIL

#Machine Learning
import settings
import helper

class VideoThread(QThread):
    frame_update = pyqtSignal(np.ndarray)

    def __init__(self, selected_camera_index=0):
        super().__init__()
        self.selected_camera_index = selected_camera_index
        self.model = YOLO("yolov8s.pt")  # Initialize YOLO model

    def run(self):
        capture = cv2.VideoCapture(self.selected_camera_index)
        while True:
            ret, frame = capture.read()
            if not ret:
                break
            frame = cv2.resize(frame, (1280, 650))

            # YOLOv8 detection
            result = self.model(frame, agnostic_nms=True)[0]
            detections = sv.Detections.from_yolov8(result)
            detections = detections[detections.class_id == 0]  # Filter out class (adjust as needed)

            # Draw bounding boxes
            box_annotator = sv.BoxAnnotator(
                thickness=2,
                text_thickness=2,
                text_scale=1
            )
            labels = [
                f"{self.model.model.names[class_id]} {confidence:0.2f}"
                for _, confidence, class_id, _
                in detections
            ]
            frame = box_annotator.annotate(scene=frame, detections=detections, labels=labels)

            # Emit the frame with annotations
            self.frame_update.emit(frame)

        capture.release()

class VideoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.ser = None
        self.arduino_connection()

        self.video_thread = VideoThread()
        self.video_thread.frame_update.connect(self.update_frame)
        self.video_thread.start()

    def init_ui(self):
        # Layout utama menggunakan QHBoxLayout
        main_layout = QHBoxLayout(self)

        # Sidebar Layout
        sidebar_layout = QVBoxLayout()

        # Create a QVBoxLayout for the Arduino Port label and combo box
        arduino_port_layout = QVBoxLayout()

        # Add the label to the QVBoxLayout
        self.arduino_port_label = QLabel("Arduino Port", self)
        arduino_port_layout.addWidget(self.arduino_port_label)

        # Set font size and make it bold for the label combo box
        self.arduino_port_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.arduino_port_label.font()
        font.setPointSize(14)  # Adjust the font size as needed
        font.setBold(True)
        self.arduino_port_label.setFont(font)

        # Set the spacing between the label and combo box
        arduino_port_layout.setSpacing(0)  # Adjust the spacing as needed

        # 1. Add a QComboBox to your sidebar
        self.arduino_port_combo = QComboBox(self)
        arduino_port_layout.addWidget(self.arduino_port_combo)

        # 2. Populate the QComboBox with port names from COM2 to COM7
        self.populate_arduino_ports()

        # Set font size and make it bold for the combo box
        font = self.arduino_port_combo.font()
        font.setPointSize(12)  # Adjust the font size as needed
        font.setBold(True)
        self.arduino_port_combo.setFont(font)

        # Add the QVBoxLayout to the existing sidebar_layout
        sidebar_layout.addLayout(arduino_port_layout)

        # 3. Connect the currentIndexChanged signal to a function
        self.arduino_port_combo.currentIndexChanged.connect(self.arduino_connection)

        # Slider horizontal pertama (Model Confidence)
        self.model_confidence_label = QLabel("Model Confidence", self)
        self.model_confidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.model_confidence_label.font()
        font.setBold(True)
        font.setPointSize(14)
        self.model_confidence_label.setFont(font)
        self.model_confidence_slider = QSlider(Qt.Orientation.Horizontal)
        self.model_confidence_slider.setRange(0, 100)
        self.model_confidence_slider.setToolTip("Model Confidence")
        sidebar_layout.addWidget(self.model_confidence_label)
        sidebar_layout.addWidget(self.model_confidence_slider)

        # Label untuk menampilkan nilai slider Model Confidence
        self.model_confidence_value_label = QLabel("0", self)
        self.model_confidence_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.model_confidence_value_label.font()
        font.setPointSize(13)  # Sesuaikan ukuran font sesuai keinginan
        self.model_confidence_value_label.setFont(font)
        sidebar_layout.addWidget(self.model_confidence_value_label)

        # Menghubungkan signal slider dengan metode untuk memperbarui nilai
        self.model_confidence_slider.valueChanged.connect(self.model_confidence_changed)

        # Menambahkan properti gaya untuk sidebar
        sidebar_style = """
            background-color: #2C3E50; /* Warna latar belakang sidebar */
            padding: 15px; /* Ruang di dalam sidebar */
            color: white; /* Warna teks */
        """
        sidebar_widget = QWidget(self)
        sidebar_widget.setLayout(sidebar_layout)
        sidebar_widget.setStyleSheet(sidebar_style)
        main_layout.addWidget(sidebar_widget)

        # Konten utama Layout
        content_layout = QVBoxLayout()

        # Label di atas video frame dan tombol "Load Machine Learning"
        label_button_layout = QHBoxLayout()

        # Video Label (Pantai Baron)
        self.video_label = QLabel("Pantai Baron", self)
        font = self.video_label.font()
        font.setPointSize(30)
        font.setBold(True)
        font_color = "#2C3E50"
        self.video_label.setStyleSheet(f"color: {font_color};")
        self.video_label.setFont(font)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Mengatur alignment ke kiri dan sejajar
        label_button_layout.addWidget(self.video_label)

        # Button "Load Machine Learning"
        load_ml_button = QPushButton("Load Machine Learning", self)
        load_ml_button.setStyleSheet("padding: 4px; background-color: #3498db; color: white; font: bold; font-size: 14px")
        load_ml_button.clicked.connect(self.load_machine_learning)
        label_button_layout.addWidget(load_ml_button)

        content_layout.addLayout(label_button_layout)

        # Layout untuk video frame dan slider
        video_slider_layout = QHBoxLayout()

        # Videoframe
        self.video_display = QLabel(self)
        self.video_display.setAlignment(Qt.AlignmentFlag.AlignLeft)
        video_slider_layout.addWidget(self.video_display, 1)  

        content_layout.addLayout(video_slider_layout)

        # Menambahkan QGraphicsView dan QGraphicsScene untuk menggambar titik-titik
        self.graphics_view = QGraphicsView(self)
        self.graphics_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graphics_view.setStyleSheet("background-color: transparent; border: none;")
        video_slider_layout.addWidget(self.graphics_view, 1)  

        # Tombol untuk mengirim perintah ke Arduino
        self.arduino_control_layout = QHBoxLayout()

        # Tombol Hazard
        self.hazard_button = QPushButton("Bahaya!", self)
        self.hazard_button.setStyleSheet("border-radius: 5px; padding: 4px; background-color: #BD0000; color: white; font: bold; font-size: 17px")
        self.hazard_button.clicked.connect(lambda: self.send_command('1'))
        self.arduino_control_layout.addWidget(self.hazard_button)

        # Tombol Safe
        self.safe_button = QPushButton("Aman", self)
        self.safe_button.setStyleSheet("border-radius: 5px; padding: 4px; background-color: #00A86B; color: white; font: bold; font-size: 17px")
        self.safe_button.clicked.connect(lambda: self.send_command('0'))
        self.arduino_control_layout.addWidget(self.safe_button)

        content_layout.addLayout(self.arduino_control_layout)

        # Set margin untuk layout utama
        self.setContentsMargins(0, 5, 5, 5)

        # Menambahkan konten utama ke layout utama
        main_layout.addLayout(content_layout)

        # Set panjang slider sesuai dengan panjang sidebar
        sidebar_width = 230  # Ganti dengan lebar yang Anda inginkan
        self.model_confidence_slider.setFixedWidth(sidebar_width - 20)  # Sesuaikan sesuai kebutuhan

    def populate_arduino_ports(self):
        # Populate the QComboBox with port names from COM2 to COM7
        for i in range(2, 8):
            port_name = f'COM{i}'
            self.arduino_port_combo.addItem(port_name)

    def model_confidence_changed(self, value):
        scaled_value = value
        self.model_confidence_value_label.setText(f"{scaled_value:.1f}")
        self.update_label_position()

    def update_label_position(self):
        value = self.model_confidence_slider.value()
        slider_width = self.model_confidence_slider.width()
        label_width = self.model_confidence_value_label.width()

        # Menghitung posisi label agar berada di tengah slider
        pos = (slider_width - label_width) * (value / 100)
        self.model_confidence_value_label.setGeometry(int(pos), -20, label_width, 20)

    def update_frame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width, _ = frame.shape

        window_height = int(self.width() * 0.8)
        window_width = int(self.width() * 0.8)

        if window_height / frame_height < window_width / frame_width:
            scale_factor = window_height / frame_height
        else:
            scale_factor = window_width / frame_width

        new_height = int(frame_height * scale_factor)
        new_width = int(frame_width * scale_factor)

        frame = cv2.resize(frame, (new_width, new_height))

        bytes_per_line = 3 * new_width
        image = QImage(frame.data, new_width, new_height, bytes_per_line, QImage.Format.Format_RGB888)

        pixmap = QPixmap.fromImage(image)
        self.video_display.setPixmap(pixmap)
        self.video_display.setFixedHeight(new_height)

    def send_command(self, command):
        if self.ser is not None:
            if command in ['0', '1']:
                self.ser.write(command.encode())
                response = self.ser.readline().decode().strip()
                print(f"Arduino: {response}")
                if command == '1':
                    self.custom_message_box("Peringatan", "Sedang dalam Hazard Condition!")
            else:
                print("Masukkan perintah yang valid (0 atau 1).")
        else:
            print("Arduino tidak terdeteksi. Aplikasi tetap berjalan tanpa koneksi ke Arduino.")

    def button_click(self, command):
        self.send_command(command)

    def close_connection(self):
        if self.ser is not None:
            self.ser.close()
        self.root.destroy()

    def custom_message_box(self, title, message):
        custom_msg_box = QMessageBox()
        custom_msg_box.setIcon(QMessageBox.Icon.Warning)
        custom_msg_box.setWindowTitle(title)
        custom_msg_box.setText(message)
        custom_msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        custom_msg_box.exec()

    def arduino_connection(self):
        # Function to update the Arduino port when the selection changes
        selected_port = self.arduino_port_combo.currentText()
        print(f"Selected Arduino Port: {selected_port}")
        baud_rate = 9600

        try:
            self.ser = serial.Serial(selected_port, baud_rate)
            time.sleep(2)  
        except serial.SerialException:
            self.ser = None
            print("Arduino tidak terdeteksi. Aplikasi tetap berjalan tanpa koneksi ke Arduino.")

    def resizeEvent(self, event):
        self.update_video_frame_size()

    def update_video_frame_size(self):
        video_width = int(self.width() * 0.9)
        self.video_display.setFixedWidth(video_width)

    def populate_camera_list(self):
        self.camera_combo.clear()

        for i in range(10):
            capture = cv2.VideoCapture(i)
            if capture.isOpened():
                self.camera_combo.addItem(f"Camera {i}")
                capture.release()

    def camera_selection_changed(self, index):
        self.video_thread.terminate()
        selected_camera_index = index
        self.video_thread = VideoThread(selected_camera_index)
        self.video_thread.frame_update.connect(self.update_frame)
        self.video_thread.start()

        self.line_position = self.video_thread.frame_height // 2
    
    def load_machine_learning(self):
        # Implementasi fungsi untuk memuat model machine learning
        # Isi dengan kode yang diperlukan untuk memuat model machine learning
        pass

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.central_widget = VideoWindow()
        self.setCentralWidget(self.central_widget)
        self.setFixedSize(1270, 638)  # Menetapkan ukuran window
        self.setWindowTitle("Capstone C_05")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()