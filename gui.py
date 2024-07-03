
from tkinter import messagebox, filedialog

from PyQt6.QtCore import Qt, QPoint, QLine, QRect
from PyQt6.QtGui import QPainter, QFont, QPen, QBrush, QImage
from PyQt6.QtWidgets import(
    QApplication,
    QWidget, QMainWindow, QDialog, QMessageBox,
    QDialogButtonBox,
    QLabel, QLineEdit, QPushButton, QCheckBox, QRadioButton,
    QGroupBox,
    QVBoxLayout, QHBoxLayout, QFormLayout
)


class gui:

    @staticmethod
    def get_csvfile()->str:
        csv_path = filedialog.askopenfilename(title='CSV Log', filetypes=[('CSV Format (*.csv)', '.csv'), ('All Files', '.*')])

        if csv_path:
            return csv_path
        else:
            print('No file imported.')
            return None
        

    @staticmethod
    def get_csvfiles()->list:
        csv_path = filedialog.askopenfilenames(title='CSV Logs', filetypes=[('CSV Format (*.csv)', '.csv'), ('All Files', '.*')])

        if csv_path:
            return csv_path
        else:
            print('No file imported.')
            return None
        
    
    @staticmethod
    def get_gpxfile()->str:
        gpx_path = filedialog.askopenfilename(title='GPX Log', filetypes=[('GPX Format (*.gpx)', '.gpx'), ('All Files', '.*')])

        if gpx_path:
            return gpx_path
        else:
            print('No file imported.')
            return None
    
    @staticmethod
    def get_gpxfile()->list:
        gpx_path = filedialog.askopenfilename(title='GPX Logs', filetypes=[('GPX Format (*.gpx)', '.gpx'), ('All Files', '.*')])

        if gpx_path:
            return gpx_path
        else:
            print('No file imported.')
            return None


class ImportDialog(QDialog):

    as_waypoint = False
    as_trackpoint = False


    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle('Import Options')
        self.setFixedSize(256, 400)

        dialog_layout = QVBoxLayout()

        self.check_as_waypoint = QCheckBox(text='As Waypoints')
        self.check_as_waypoint.setChecked(self.as_waypoint)

        self.check_as_trackpoints = QCheckBox(text='As Trackpoints')
        self.check_as_trackpoints.setChecked(self.as_trackpoint)

        dialog_layout.addWidget(self.check_as_waypoint)
        dialog_layout.addWidget(self.check_as_trackpoints)

        button_box = QDialogButtonBox(self)
        button_box.addButton(QDialogButtonBox.StandardButton.Ok)
        button_box.addButton(QDialogButtonBox.StandardButton.Cancel)

        dialog_layout.addWidget(button_box)

        self.setLayout(dialog_layout)


        self.check_as_waypoint.checkStateChanged.connect(self.on_toggle_as_waypoint)
        self.check_as_trackpoints.checkStateChanged.connect(self.on_toggle_as_trackpoint)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)


    def on_toggle_as_waypoint(self, event):
        self.as_waypoint = self.check_as_waypoint.checkState()



    def on_toggle_as_trackpoint(self, event):
        self.as_trackpoint = self.check_as_trackpoints.checkState()

    