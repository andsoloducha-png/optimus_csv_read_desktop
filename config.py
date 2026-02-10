import os
import sys
from typing import List, Tuple

DEFAULT_FOLDER = r"D:\Optimus\GUI\Logging"
DEFAULT_NR_LIST = [35, 37, 38, 53, 201]
DEFAULT_MONITOR_INTERVAL_SEC = 10


def get_settings_path(filename: str = "sorter_config.txt") -> str:
    """
    Plik konfiguracyjny obok .py / .exe:
    - dla EXE: obok pliku .exe
    - dla .py: obok skryptu main.py
    """
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def load_settings() -> Tuple[str, List[int], int]:
    """
    Wczytuje ustawienia z sorter_config.txt.
    Obsługuje:
    1) stary format: 1 linia = folder
    2) nowy format key=value:
       folder=...
       nr_list=35,37,38,53,201
       monitor_interval_sec=10
    """
    folder = DEFAULT_FOLDER
    nr_list = DEFAULT_NR_LIST.copy()
    monitor_interval = DEFAULT_MONITOR_INTERVAL_SEC

    path = get_settings_path()

    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except (FileNotFoundError, OSError):
        return folder, nr_list, monitor_interval

    if any("=" in line for line in lines):
        for line in lines:
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().lower()
            value = value.strip()

            if key == "folder" and value:
                folder = value

            elif key == "nr_list" and value:
                parsed: List[int] = []
                for part in value.replace(";", ",").split(","):
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        parsed.append(int(part))
                    except ValueError:
                        pass
                if parsed:
                    nr_list = parsed

            elif key == "monitor_interval_sec" and value:
                try:
                    sec = int(value)
                    if sec > 0:
                        monitor_interval = sec
                except ValueError:
                    pass
    else:
        # stary format
        folder = lines[0]

    return folder, nr_list, monitor_interval


def save_settings(folder: str, nr_list: List[int], monitor_interval_sec: int) -> None:
    """
    Zapis ustawień w formacie key=value.
    Jeśli nie da się zapisać (uprawnienia), ignorujemy.
    """
    path = get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"folder={folder}\n")
            f.write("nr_list=" + ",".join(str(n) for n in nr_list) + "\n")
            f.write(f"monitor_interval_sec={monitor_interval_sec}\n")
    except OSError:
        pass
