# Sorter Analyzer

Production-ready application for monitoring and analyzing alarm logs from sorting machines.

## Features

- **Real-time monitoring** - Live data updates from alarm log files
- **Historical analysis** - Analyze past alarm log files
- **Dual view modes** - Switch between table and chart visualizations
- **CSV export** - Export analysis results to CSV format
- **Shift-based analysis** - Separate data by work shifts (Shift 1: 6:07-14:15, Shift 2: 14:20-22:30)
- **Configurable** - Save and load custom settings
- **Scrollable interface** - Works on different screen sizes

## Screenshots

### Main Interface
Clean, professional interface with configurable parameters and real-time data display.

### Analysis Views
- **Table View**: Detailed tabular data with statistics cards
- **Chart View**: Visual representation with matplotlib charts

## Installation

### Requirements

```bash
pip install -r requirements.txt
```

Required packages:
- pandas >= 1.5.0
- matplotlib >= 3.5.0

### Files Structure

```
sorter-analyzer/
├── main.py              # Main application
├── config.py            # Configuration management
├── files_io.py          # File operations
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Usage

### Quick Start

1. Install dependencies:
```bash
pip install pandas matplotlib
```

2. Run the application:
```bash
python main.py
```

3. Configure:
   - Select folder containing alarm log files
   - Set error numbers to filter (comma-separated)
   - Choose analysis mode (historical or live monitoring)

4. Analyze:
   - Click "ANALIZUJ TERAZ" for immediate analysis
   - Or enable "Monitoring LIVE" for continuous updates

### Configuration

Settings are automatically saved to `sorter_config.txt`:

```
folder=D:\Optimus\GUI\Logging
nr_list=35,37,38,53,201
monitor_interval_sec=10
```

### Analysis Modes

**Historical Analysis (Analiza wstecz)**
- Select specific alarm log file from list
- One-time analysis on demand
- Best for reviewing past data

**Live Monitoring**
- Automatically tracks today's alarm log file
- Auto-refresh at configurable interval (default: 10s)
- Best for real-time production monitoring

### Query Types

**Shifts Mode (Zmiany)**
- Separate results by shift 1 and shift 2
- Compare shift performance
- Grouped bar charts

**Total Mode**
- Combined results from all shifts
- Overall statistics
- Horizontal bar charts

### Export

Click "Eksportuj do CSV" to save current results:
- Includes all columns from analysis
- UTF-8 encoding with BOM for Excel compatibility
- Semicolon delimiter

## File Format

Expected alarm log format (CSV with semicolon delimiter):

```
start;status;nr;alarm;duration
06:15:23;OK;35;Whisker;00:02:15
14:32:41;OK;37;Gap;00:00:45
```

Required columns:
- `start` - Time (HH:MM:SS)
- `status` - Status (filter: OK)
- `nr` - Error number (integer)
- `alarm` - Alarm description (text)
- `duration` - Duration (HH:MM:SS)

## Technical Details

### Data Processing

Uses Pandas for efficient data processing:
- CSV parsing with error handling
- Shift calculation based on time ranges
- Grouping and aggregation
- Duration conversion (HH:MM:SS to seconds)

### User Interface

Built with Tkinter:
- Responsive layout with scrollable left panel
- Card-based design
- Collapsible sidebar for smaller screens
- Real-time clock in footer

### Performance

- Fast analysis (< 1s for typical files)
- Efficient memory usage
- Suitable for files with 10,000+ rows
- Auto-refresh without blocking UI

## Compilation to EXE

To create standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name=SorterAnalyzer main.py
```

Include data files in spec:

```python
datas=[
    ('config.py', '.'),
    ('files_io.py', '.')
]
```

## Configuration Options

### Default Settings

Located in `config.py`:

```python
DEFAULT_FOLDER = r"D:\Optimus\GUI\Logging"
DEFAULT_NR_LIST = [35, 37, 38, 53, 201]
DEFAULT_MONITOR_INTERVAL_SEC = 10
```

### Shift Time Ranges

Defined in `main.py`:

```python
Shift 1: 06:07:00 to 14:15:00
Shift 2: 14:20:00 to 22:30:00
```

Modify `calculate_shift()` function to change ranges.

## Troubleshooting

### No files found
- Check folder path is correct
- Ensure files contain "alarmlog" in filename
- Verify files have .csv or .txt extension

### Analysis error
- Verify CSV format matches expected structure
- Check file encoding (should be UTF-8)
- Ensure semicolon delimiter

### Monitoring not starting
- Check "Monitoring LIVE" mode is selected
- Verify today's file exists in folder
- File must start with YYYY-MM-DD date format

### Export fails
- Ensure you have write permissions
- Close file if already open in Excel
- Check disk space

## Development

### Project Structure

```
main.py
├── SorterApp class
│   ├── __init__() - Initialize UI and state
│   ├── _build_ui() - Construct interface
│   ├── _build_controls() - Left panel controls
│   ├── _build_data_view() - Right panel display
│   ├── show_table() - Render table view
│   ├── show_charts() - Render chart view
│   ├── run_now() - Execute analysis
│   ├── toggle_monitoring() - Start/stop live mode
│   └── export_to_csv() - Export functionality
│
├── Helper functions
│   ├── analyze_data() - Main analysis logic
│   ├── calculate_shift() - Determine shift from time
│   ├── parse_duration_to_seconds() - Convert duration
│   └── format_seconds_to_duration() - Format time
│
config.py - Settings management
files_io.py - File operations
```

### Adding Features

To add new analysis types:

1. Modify `analyze_data()` function
2. Add new radio button in query settings
3. Update grouping logic
4. Adjust chart rendering

### Color Scheme

Light mode palette:

```python
bg = '#f0f2f5'           # Main background
bg_secondary = '#ffffff'  # Cards and headers
accent = '#0066ff'        # Primary actions
accent_secondary = '#ff3366'  # Secondary actions
success = '#00cc66'       # Success states
error = '#ff3366'         # Error states
text = '#1a1a1a'          # Primary text
text_secondary = '#666666' # Secondary text
```

## License

Internal use only. Not for distribution.

## Version History

### v3.0 (Current)
- Removed dark mode (light mode only)
- Added CSV export functionality
- Fixed groupby bug in Pandas aggregation
- Added scrollable left panel
- Improved checkbox visibility
- Cleaned up UI (removed emojis from production code)

### v2.1 (Bugfix)
- Fixed "cannot insert nr" error
- Added scrollbar for small screens
- Improved checkbox rendering
- Better canvas theme switching

### v2.0 (Premium Edition)
- Complete UI redesign
- Dark/Light mode toggle
- Integrated chart view
- Pandas backend
- Real-time statistics

### v1.0 (Original)
- Basic functionality
- SQLite backend
- Separate chart window

## Support

For issues or feature requests, contact development team.

## Acknowledgments

Built with:
- Python 3.8+
- Tkinter (GUI)
- Pandas (data processing)
- Matplotlib (visualization)
