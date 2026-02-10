import os
import datetime
from typing import List, Optional


def list_alarmlog_files(folder_path: str) -> List[str]:
    """Zwraca pliki z 'alarmlog' w nazwie i rozszerzeniem .csv/.txt."""
    if not os.path.isdir(folder_path):
        return []

    files: List[str] = []
    for filename in os.listdir(folder_path):
        lower = filename.lower()
        if ("alarmlog" in lower) and lower.endswith((".csv", ".txt")):
            files.append(filename)

    return sorted(files)


def find_today_alarmlog(folder_path: str) -> Optional[str]:
    """
    Znajduje plik alarmlog z dzisiejszą datą (YYYY-MM-DD_alarmlog...).
    Jeśli kilka, bierze najnowszy po mtime.
    Zwraca pełną ścieżkę lub None.
    """
    today_str = datetime.date.today().isoformat()
    candidates = []

    if not os.path.isdir(folder_path):
        return None

    for filename in os.listdir(folder_path):
        lower = filename.lower()
        if not ("alarmlog" in lower and lower.endswith((".csv", ".txt"))):
            continue
        if not lower.startswith(today_str.lower()):
            continue

        full_path = os.path.join(folder_path, filename)
        try:
            mtime = os.path.getmtime(full_path)
        except OSError:
            continue
        candidates.append((mtime, full_path))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][1]
