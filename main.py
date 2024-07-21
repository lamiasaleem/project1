from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy_garden.mapview import MapView, MapMarker
from kivymd.uix.label import MDLabel
from kivy.clock import Clock
import serial
import serial.tools.list_ports
import requests

kv = '''
BoxLayout:
    orientation: 'vertical'
    MapView:
        id: mapview
        lat: 0
        lon: 0
        zoom: 10
    MDLabel:
        id: location_label
        text: "LOCATION IS NOT FOUND"
        halign: "center"
'''

class GPSApp(MDApp):
    def build(self):
        self.root = Builder.load_string(kv)
        self.mapview = self.root.ids.mapview
        self.location_label = self.root.ids.location_label
        self.serial_port = None
        self.find_gps_device()
        Clock.schedule_interval(self.update_location, 1)
        return self.root

    def find_gps_device(self):
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            try:
                s = serial.Serial(port.device, baudrate=9600, timeout=1)
                # Read a line to test if this port is the GPS device
                line = s.readline().decode('ascii', errors='replace').strip()
                if line.startswith('$GNRMC') or line.startswith('$GPGGA'):
                    self.serial_port = s
                    print(f"GPS device found on {port.device}")
                    break
                s.close()
            except Exception as e:
                print(f"Error testing port {port.device}: {e}")

    def update_location(self, dt=None):
        if self.serial_port:
            try:
                line = self.serial_port.readline().decode('ascii', errors='replace').strip()
                print(f"Received line: {line}")
                if line.startswith('$GNRMC'):
                    data = line.split(',')
                    print(f"Parsed data: {data}")
                    if data[2] == 'A':  # A means data is valid
                        lat = self.convert_to_degrees(data[3], data[4])
                        lon = self.convert_to_degrees(data[5], data[6])
                        print(f"Latitude: {lat}, Longitude: {lon}")
                        self.mapview.lat = lat
                        self.mapview.lon = lon
                        self.add_marker(lat, lon)
                        self.update_address(lat, lon)
                    else:
                        print("Data is not valid")
            except Exception as e:
                print(f"Error: {e}")
        else:
            print("No GPS device connected")

    def convert_to_degrees(self, value, direction):
        degrees = float(value[:2])
        minutes = float(value[2:]) / 60
        coord = degrees + minutes
        if direction in ['S', 'W']:
            coord = -coord
        return coord

    def add_marker(self, lat, lon):
        self.mapview.add_marker(MapMarker(lat=lat, lon=lon))

    def update_address(self, lat, lon):
        try:
            response = requests.get(f'https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1')
            data = response.json()
            address = data.get('display_name', 'LOCATION NOT KNOWN')
            self.location_label.text = address
        except Exception as e:
            self.location_label.text = "ERROR"
            print(f"Error: {e}")

if __name__ == '__main__':
    GPSApp().run()
