import servicemanager
import win32event
import win32service
import os
import time
import socket
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from win32serviceutil import ServiceFramework, HandleCommandLine


# Возвращает путь к файлу который был изменён последним в указанной папке
def get_modified_file(target_folder: str, _logger: logging.Logger) -> str:

    latest_timestamp = 0
    latest_filename = ""
    _, _, filenames = next(os.walk(target_folder), (None, None, []))
    for file in filenames:
        file_timestamp = os.stat(target_folder + "\\" + file).st_mtime
        if latest_timestamp < file_timestamp:
            latest_timestamp = file_timestamp
            latest_filename = file
        continue

    _logger.debug(f"Файл с изменениями найден {latest_filename}")
    # print(f"Файл с изменениями найден {latest_filename}")

    return target_folder + "\\" + latest_filename


# Класс для обработки событий файлов
class FileEventHandler(FileSystemEventHandler):

    def __init__(self, api_url, directory, _logger):
        self.api_url = api_url
        self.observeDirectory = directory
        self.logger = _logger

    def on_modified(self, event):
        self.logger.debug(f"Сработал триггер on_modified событие {event}")
        print(f"Сработал триггер ----> событие {event}")
        print(get_modified_file(self.observeDirectory, self.logger))


class UsbTemperService(ServiceFramework):
    _svc_name_ = "UsbTemperHandler"
    _svc_display_name_ = "UsbTemperHandler"
    _svc_description_ = "Служба для считывания данных из файла температурного датчика. Разработчик Туршиев Н.М."

    def __init__(self, args):
        ServiceFramework.__init__(self, args)
        print("Начало конструктора класса сервиса")
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.observer = Observer()
        socket.setdefaulttimeout(60)
        self.isRunning = True
        logging.basicConfig(filename="C:\\Users\\admin\\Desktop\\climatControl\\log.txt",
                            filemode="a",
                            format="%(name)s - %(levelname)s - %(message)s",
                            datefmt="%H:%M:%S",
                            level=logging.INFO)
        self.logger = logging.getLogger("UsbTemperServiceLogger")
        print("Конец конструктора")


    def SvcStop(self):
        self.logger.debug("Получен сигнал остановки")
        print("Получен сигнал остановки")
        self.stop()
        self.logger.debug("Переменная isRunning переведена в состояние False")
        print("Переменная isRunning переведена в состояние False")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        self.logger.debug("Получен сигнал Запуска")
        print("Получен сигнал Запуска")
        self.isRunning = True
        self.logger.debug("Переменная isRunning переведена в состояние True")
        print("Переменная isRunning переведена в состояние True")
        # win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
        servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
                )
        self.main()


    def main(self):
        self.logger.debug("Начало исполнения функции main()")
        print("Начало исполнения функции main()")
        file_folder = "C:\\Users\\admin\\Desktop\\climatControl\\test"
        api_url = ""
        self.logger.debug("Конфигурирование Observer'а")
        print("Конфигурирование Observer'а")
        self.observer.schedule(FileEventHandler(api_url, file_folder, self.logger), path=file_folder, recursive=False)
        self.logger.debug("Observer успешно сконфигурирован")
        print("Observer успешно сконфигурирован")
        self.logger.debug("Запуск Observer'а")
        print("Запуск Observer'а")
        self.observer.start()
        self.logger.debug("Observer запущен")
        print("Observer запущен")
        try:
            while self.isRunning:
                time.sleep(1)
        finally:
            self.logger.debug("Попытка остановки Observer'а")
            print("Попытка остановки Observer'а")
            self.observer.stop()
            self.logger.debug("Observer остановлен")
            print("Observer остановлен")

        self.logger.debug("Начало ожидания завершения всех процессов")
        print("Начало ожидания завершения всех процессов")
        self.observer.join()
        self.logger.debug("Все процессы завершены")
        print("Все процессы завершены")


    def stop(self):
        self.isRunning = False


if __name__ == '__main__':
    HandleCommandLine(UsbTemperService)
