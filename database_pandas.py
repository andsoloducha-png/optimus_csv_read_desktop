import pandas as pd
import os
from typing import List, Tuple


def load_file_to_dataframe(file_path: str) -> pd.DataFrame:
    """Wczytuje plik alarmlog do DataFrame."""
    df = pd.read_csv(
        file_path,
        sep=';',
        names=['start', 'status', 'nr', 'alarm', 'duration'],
        encoding='utf-8'
    )
    
    # Dodaj kolumnę data z nazwy pliku
    filename = os.path.basename(file_path)
    df['data'] = filename.split('_')[0]
    
    # Konwertuj nr na int
    df['nr'] = pd.to_numeric(df['nr'], errors='coerce')
    
    return df


def calculate_shift(time_str: str) -> int:
    """Oblicza zmianę na podstawie czasu."""
    if pd.isna(time_str):
        return None
    
    if '06:07:00' <= time_str <= '14:15:00':
        return 1
    elif '14:20:00' <= time_str <= '22:30:00':
        return 2
    return None


def parse_duration_to_seconds(duration_str: str) -> float:
    """Konwertuje duration (HH:MM:SS) na sekundy."""
    try:
        h, m, s = duration_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0


def format_seconds_to_duration(seconds: float) -> str:
    """Formatuje sekundy z powrotem na HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def run_query_shifts(df: pd.DataFrame, nr_list: List[int]) -> Tuple[List[str], List[tuple]]:
    """
    Zapytanie dla zmian (1 i 2).
    Zwraca: columns, rows
    """
    # Filtruj dane
    filtered = df[
        (df['status'] == 'OK') &
        (df['nr'].isin(nr_list))
    ].copy()
    
    # Dodaj shift
    filtered['shift'] = filtered['start'].apply(calculate_shift)
    filtered = filtered[filtered['shift'].notna()]
    
    # Parsuj duration na sekundy
    filtered['dur_sec'] = filtered['duration'].apply(parse_duration_to_seconds)
    
    # Wyciągnij pierwsze słowo z alarmu
    filtered['alarm_first'] = filtered['alarm'].str.split().str[0]
    
    # Grupuj
    grouped = filtered.groupby(['shift', 'status', 'nr']).agg({
        'alarm_first': 'first',
        'nr': 'count',  # cnt
        'dur_sec': 'sum'
    }).reset_index()
    
    grouped.columns = ['shift', 'status', 'nr', 'alarm', 'cnt', 'dur_sec']
    
    # Formatuj duration
    grouped['duration_fixed'] = grouped['dur_sec'].apply(format_seconds_to_duration)
    grouped = grouped.drop('dur_sec', axis=1)
    
    # Sortuj
    grouped = grouped.sort_values('shift')
    
    # Konwertuj shift na int
    grouped['shift'] = grouped['shift'].astype(int)
    
    columns = list(grouped.columns)
    rows = [tuple(row) for row in grouped.values]
    
    return columns, rows


def run_query_total(df: pd.DataFrame, nr_list: List[int]) -> Tuple[List[str], List[tuple]]:
    """
    Zapytanie total (bez podziału na zmiany).
    Zwraca: columns, rows
    """
    # Filtruj dane
    filtered = df[
        (df['status'] == 'OK') &
        (df['nr'].isin(nr_list))
    ].copy()
    
    # Sprawdź czy w zakresie godzin
    filtered['shift'] = filtered['start'].apply(calculate_shift)
    filtered = filtered[filtered['shift'].notna()]
    
    # Dodaj kolumnę 'total'
    filtered['shift'] = 'total'
    
    # Parsuj duration
    filtered['dur_sec'] = filtered['duration'].apply(parse_duration_to_seconds)
    
    # Pierwsze słowo alarmu
    filtered['alarm_first'] = filtered['alarm'].str.split().str[0]
    
    # Grupuj
    grouped = filtered.groupby(['shift', 'status', 'nr']).agg({
        'alarm_first': 'first',
        'nr': 'count',
        'dur_sec': 'sum'
    }).reset_index()
    
    grouped.columns = ['shift', 'status', 'nr', 'alarm', 'cnt', 'dur_sec']
    
    # Formatuj duration
    grouped['duration_fixed'] = grouped['dur_sec'].apply(format_seconds_to_duration)
    grouped = grouped.drop('dur_sec', axis=1)
    
    # Sortuj według cnt DESC
    grouped = grouped.sort_values('cnt', ascending=False)
    
    columns = list(grouped.columns)
    rows = [tuple(row) for row in grouped.values]
    
    return columns, rows


def run_query(query_mode: str, nr_list: List[int], file_path: str) -> Tuple[List[str], List[tuple]]:
    """
    Główna funkcja - zamiennik dla database.run_query().
    
    Args:
        query_mode: 'shifts' lub 'total'
        nr_list: lista numerów do filtrowania
        file_path: ścieżka do pliku alarmlog
    
    Returns:
        (columns, rows) - kolumny i wiersze wyników
    """
    if not nr_list:
        raise ValueError("nr_list jest puste.")
    
    # Wczytaj dane
    df = load_file_to_dataframe(file_path)
    
    # Uruchom odpowiednie zapytanie
    if query_mode == 'total':
        return run_query_total(df, nr_list)
    else:
        return run_query_shifts(df, nr_list)
