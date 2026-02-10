import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from typing import List, Tuple


def export_html_report(columns: List[str], rows: List[tuple], output_path: str = None):
    """
    Eksportuje wyniki do interaktywnego raportu HTML z wykresami.
    
    Args:
        columns: nazwy kolumn
        rows: dane w postaci listy krotek
        output_path: ścieżka zapisu (domyślnie: folder sieciowy lub lokalny)
    """
    if output_path is None:
        # Możesz ustawić domyślny folder sieciowy
        output_path = f"alarm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    # Konwertuj dane na DataFrame
    df = pd.DataFrame(rows, columns=columns)
    
    # Przygotuj wykresy
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta http-equiv="refresh" content="300">  <!-- Auto-odświeżanie co 5 min -->
        <title>Raport Alarmów - Sorter</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
                border-bottom: 3px solid #4CAF50;
                padding-bottom: 10px;
            }}
            .timestamp {{
                color: #666;
                font-size: 14px;
                margin-bottom: 20px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 20px 0;
            }}
            th {{
                background-color: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}
            tr:hover {{
                background-color: #f5f5f5;
            }}
            .chart-container {{
                background-color: white;
                padding: 20px;
                margin: 20px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
        </style>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    </head>
    <body>
        <h1>📊 Raport Analiza Alarmów</h1>
        <div class="timestamp">
            Wygenerowano: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            <small>Strona automatycznie odświeża się co 5 minut</small>
        </div>
    """
    
    # Dodaj wykres słupkowy
    if 'shift' in df.columns and 'cnt' in df.columns:
        try:
            # Wykres dla zmian
            if df['shift'].dtype in ['int64', 'int32'] and set(df['shift'].unique()).issubset({1, 2}):
                fig = px.bar(
                    df,
                    x='alarm',
                    y='cnt',
                    color='shift',
                    barmode='group',
                    title='Liczba alarmów według typu i zmiany',
                    labels={'cnt': 'Liczba wystąpień', 'alarm': 'Typ alarmu', 'shift': 'Zmiana'}
                )
                html_content += '<div class="chart-container">'
                html_content += fig.to_html(include_plotlyjs=False, div_id="chart1")
                html_content += '</div>'
            
            # Wykres total
            else:
                fig = px.bar(
                    df,
                    x='alarm',
                    y='cnt',
                    title='Liczba alarmów według typu (total)',
                    labels={'cnt': 'Liczba wystąpień', 'alarm': 'Typ alarmu'}
                )
                fig.update_traces(marker_color='#4CAF50')
                html_content += '<div class="chart-container">'
                html_content += fig.to_html(include_plotlyjs=False, div_id="chart1")
                html_content += '</div>'
        except Exception as e:
            html_content += f'<p style="color: red;">Błąd generowania wykresu: {e}</p>'
    
    # Dodaj tabelę danych
    html_content += '<div class="chart-container">'
    html_content += '<h2>Szczegółowe dane</h2>'
    html_content += df.to_html(index=False, classes='data-table', border=0)
    html_content += '</div>'
    
    # Statystyki
    if 'cnt' in df.columns:
        total_alarms = df['cnt'].sum()
        html_content += f"""
        <div class="chart-container">
            <h2>Statystyki</h2>
            <p><strong>Całkowita liczba alarmów:</strong> {total_alarms}</p>
            <p><strong>Liczba unikalnych typów alarmów:</strong> {df['alarm'].nunique()}</p>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    # Zapisz plik
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path


def export_to_excel(columns: List[str], rows: List[tuple], output_path: str = None):
    """
    Eksportuje dane do pliku Excel z formatowaniem.
    """
    if output_path is None:
        output_path = f"alarm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    df = pd.DataFrame(rows, columns=columns)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Dane', index=False)
        
        # Formatowanie
        worksheet = writer.sheets['Dane']
        
        # Szerokość kolumn
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).map(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length
    
    return output_path


# Przykład użycia w main.py:
"""
# Po uruchomieniu analizy:
if results:
    # Export HTML do folderu sieciowego
    html_path = r'\\shared_server\reports\alarm_report.html'
    export_html_report(columns, rows, html_path)
    
    # Export Excel
    excel_path = r'\\shared_server\reports\alarm_report.xlsx'
    export_to_excel(columns, rows, excel_path)
    
    self.status_label.config(text=f"Raport zapisany: {html_path}")
"""
