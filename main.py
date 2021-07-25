import requests
import win32event
import win32service
import os
import time
import socket
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from win32serviceutil import ServiceFramework, HandleCommandLine


observe_folder = "C:\\Users\\admin\\Desktop\\climatControl\\test"
api_url = ""


# Возвращает путь к файлу который был изменён последним в указанной папке
def get_modified_file(target_folder: str) -> str:

    latest_timestamp = 0
    latest_filename = ""
    _, _, filenames = next(os.walk(target_folder), (None, None, []))
    for file in filenames:
        file_timestamp = os.stat(target_folder + "\\" + file).st_mtime
        if latest_timestamp < file_timestamp:
            latest_timestamp = file_timestamp
            latest_filename = file
        continue
    return target_folder + "\\" + latest_filename


# Класс для обработки событий файлов
class FileEventHandler(FileSystemEventHandler):

    def __init__(self, url, directory):
        self.api_url = url
        self.observeDirectory = directory

    def on_modified(self, event):
        file = get_modified_file(self.observeDirectory)
        with open(file=file, mode="rb") as f:
            try:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                last_line = f.readline().decode()
                date, degree, hundredths, *_ = last_line.split(",")
                request_data = degree + '.' + hundredths[0:2]
                requests.post(f'http://172.16.0.91:8000/set_server_room_temp?value={request_data}')
            except ValueError:
                return


class UsbTemperService(ServiceFramework):
    _svc_name_ = "UsbTemperHandler"
    _svc_display_name_ = "UsbTemperHandler"
    _svc_description_ = "Служба для считывания данных из файла температурного датчика. Разработчик Туршиев Н.М."

    def __init__(self, args):
        ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.observer = Observer()
        socket.setdefaulttimeout(60)
        self.isRunning = True


    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        self.isRunning = True
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        self.main()


    def main(self):
        self.observer.schedule(FileEventHandler(api_url, observe_folder), path=observe_folder, recursive=False)
        self.observer.start()
        try:
            while self.isRunning:
                time.sleep(1)
        finally:
            self.observer.stop()

        self.observer.join()


    def stop(self):
        self.isRunning = False


if __name__ == '__main__':
    HandleCommandLine(UsbTemperService)
