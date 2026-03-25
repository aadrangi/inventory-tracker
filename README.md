# Inventory Tracker

A desktop application for tracking inventory items with full history and status management.

## Features

- **Interactive GUI** with item search functionality
- **Status Tracking** with the following statuses:
  - in inventory
  - checked out
  - obsoleted
  - discarded
- **Comprehensive Logging** for each status change:
  - Person's name
  - Department
  - Status change reason
  - Location
  - Date/time of change
  - Optional comments
  - Image attachments
- **Item Metadata**:
  - Serial number
  - Company Asset Number
  - Location
  - Item images
- **Reports** showing full history of status changes
- **Overview Tab** showing last 15 updated items
- **SQLite Database** for data persistence

## Installation

### Using pip (recommended)

```bash
pip install -r requirements.txt
python inventory_tracker.py
```

### Build as standalone binary

```bash
# Install PyInstaller
pip install pyinstaller

# Build binary
pyinstaller --onefile --windowed inventory_tracker.py
```

The executable will be in the `dist/` directory.

## Usage

1. Run the application:
   ```bash
   python inventory_tracker.py
   ```

2. **Add Items**: Click "Add Item" to create a new inventory entry
3. **Search**: Use the search bar to find items by name, serial number, or asset number
4. **Update Status**: Select an item and click "Update Status" to log a status change
5. **View Report**: Double-click an item or select and click "View Report" to see full history
6. **Delete**: Select an item and click "Delete" to remove it

## File Structure

```
inventory-tracker/
├── inventory_tracker.py    # Main application
├── requirements.txt        # Python dependencies
├── setup.py               # Package setup
└── inventory_tracker      # Executable script
```

## Database

The application uses SQLite and stores the database at:
- Linux/Mac: `~/.inventory-tracker/inventory.db`
- Windows: `%APPDATA%/.inventory-tracker/inventory.db`

## Requirements

- Python 3.10 or later
- PyQt6
- SQLite (included with Python)

## License

MIT
