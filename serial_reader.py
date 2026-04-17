import time
import threading
import queue
from dataclasses import dataclass

try:
    import serial
    from serial.tools import list_ports
except Exception:
    serial = None
    list_ports = None


@dataclass
class SerialConfig:
    port: str
    baud: int
    timeout_s: float = 1.0


class SerialReader:
    def __init__(self, cfg: SerialConfig):
        self.cfg = cfg
        self._q = queue.Queue()
        self._stop_evt = threading.Event()
        self.ser = None
        self.thread = None

    def start(self):
        if serial is None:
            raise RuntimeError("pyserial is not installed.")
        self.ser = serial.Serial(self.cfg.port, self.cfg.baud, timeout=self.cfg.timeout_s)
        time.sleep(1.5)
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        while not self._stop_evt.is_set():
            try:
                raw = self.ser.readline()
                if not raw:
                    continue
                line = raw.decode(errors="ignore").strip()
                if line:
                    self._q.put(line)
            except Exception:
                break

    def get_lines(self, max_lines: int = 500):
        lines = []
        for _ in range(max_lines):
            if self._q.empty():
                break
            lines.append(self._q.get())
        return lines

    def stop(self):
        self._stop_evt.set()
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass


def get_available_ports():
    if serial and list_ports:
        return [p.device for p in list_ports.comports()]
    return []