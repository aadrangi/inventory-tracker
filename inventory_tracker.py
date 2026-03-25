#!/usr/bin/env python3
"""
Inventory Tracker - A desktop application for tracking inventory items
with status history, user information, and media attachments.
"""

import sys
import os
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel,
    QComboBox, QTextEdit, QDialog, QFormLayout, QFileDialog, QMessageBox,
    QHeaderView, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, QStringListModel
from PyQt6.QtGui import QPixmap

# Default timezone
DEFAULT_TIMEZONE = "America/Los_Angeles"


@dataclass
class InventoryItem:
    """Represents an inventory item"""
    id: Optional[int]
    name: str
    serial_number: str
    company_asset_number: str
    current_status: str
    location: str
    image_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'InventoryItem':
        return cls(
            id=row[0],
            name=row[1],
            serial_number=row[2],
            company_asset_number=row[3],
            current_status=row[4],
            location=row[5],
            image_path=row[6] if len(row) > 6 else None,
            created_at=row[7] if len(row) > 7 else None,
            updated_at=row[8] if len(row) > 8 else None
        )


@dataclass
class StatusLog:
    """Represents a status change log entry"""
    id: Optional[int]
    item_id: int
    person_name: str
    department: str
    previous_status: str
    new_status: str
    reason: str
    location: str
    comment: str
    timestamp: str
    timezone: str = "America/Los_Angeles"
    image_path: Optional[str] = None
    
    @classmethod
    def from_row(cls, row: Tuple) -> 'StatusLog':
        return cls(
            id=row[0],
            item_id=row[1],
            person_name=row[2],
            department=row[3],
            previous_status=row[4],
            new_status=row[5],
            reason=row[6],
            location=row[7],
            comment=row[8],
            image_path=row[9],
            timestamp=row[10],
            timezone=row[11] if len(row) > 11 else "America/Los_Angeles"
        )


STATUSES = ["In Inventory", "Checked Out", "Obsoleted", "Discarded"]

DB_PATH = os.path.join(os.path.expanduser("~"), ".inventory-tracker", "inventory.db")


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                serial_number TEXT NOT NULL,
                company_asset_number TEXT NOT NULL,
                current_status TEXT NOT NULL,
                location TEXT NOT NULL,
                image_path TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS status_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                person_name TEXT NOT NULL,
                department TEXT NOT NULL,
                previous_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                reason TEXT NOT NULL,
                location TEXT NOT NULL,
                comment TEXT,
                image_path TEXT,
                timestamp TEXT,
                timezone TEXT DEFAULT 'America/Los_Angeles',
                FOREIGN KEY (item_id) REFERENCES inventory_items (id)
            )
        ''')
        
        self.conn.commit()
    
    def add_item(self, item: InventoryItem, timezone: str = DEFAULT_TIMEZONE) -> int:
        """Add a new inventory item"""
        cursor = self.conn.cursor()
        now = datetime.now(ZoneInfo(timezone)).isoformat()
        cursor.execute('''
            INSERT INTO inventory_items 
            (name, serial_number, company_asset_number, current_status, location, image_path, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (item.name, item.serial_number, item.company_asset_number, 
              item.current_status, item.location, item.image_path, now, now))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_item(self, item: InventoryItem, timezone: str = DEFAULT_TIMEZONE):
        """Update an existing inventory item"""
        cursor = self.conn.cursor()
        now = datetime.now(ZoneInfo(timezone)).isoformat()
        cursor.execute('''
            UPDATE inventory_items 
            SET name = ?, serial_number = ?, company_asset_number = ?,
                current_status = ?, location = ?, image_path = ?,
                updated_at = ?
            WHERE id = ?
        ''', (item.name, item.serial_number, item.company_asset_number,
              item.current_status, item.location, item.image_path, now, item.id))
        self.conn.commit()
    
    def get_item(self, item_id: int) -> Optional[InventoryItem]:
        """Get an inventory item by ID"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory_items WHERE id = ?', (item_id,))
        row = cursor.fetchone()
        if row:
            return InventoryItem.from_row(row)
        return None
    
    def search_items(self, query: str) -> List[InventoryItem]:
        """Search items by name, serial number, or asset number"""
        cursor = self.conn.cursor()
        search_pattern = f"%{query}%"
        cursor.execute('''
            SELECT * FROM inventory_items 
            WHERE name LIKE ? OR serial_number LIKE ? OR company_asset_number LIKE ?
            ORDER BY updated_at DESC
        ''', (search_pattern, search_pattern, search_pattern))
        return [InventoryItem.from_row(row) for row in cursor.fetchall()]
    
    def get_last_n_items(self, n: int = 15) -> List[InventoryItem]:
        """Get the last N items by update time"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM inventory_items 
            ORDER BY updated_at DESC LIMIT ?
        ''', (n,))
        return [InventoryItem.from_row(row) for row in cursor.fetchall()]
    
    def get_all_items(self) -> List[InventoryItem]:
        """Get all inventory items"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM inventory_items ORDER BY updated_at DESC')
        return [InventoryItem.from_row(row) for row in cursor.fetchall()]
    
    def add_status_log(self, log: StatusLog, timezone: str = DEFAULT_TIMEZONE) -> int:
        """Add a status change log entry"""
        cursor = self.conn.cursor()
        now = datetime.now(ZoneInfo(timezone)).isoformat()
        cursor.execute('''
            INSERT INTO status_logs
            (item_id, person_name, department, previous_status, new_status,
             reason, location, comment, image_path, timestamp, timezone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (log.item_id, log.person_name, log.department, log.previous_status,
              log.new_status, log.reason, log.location, log.comment, log.image_path, now, timezone))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_item_history(self, item_id: int) -> List[StatusLog]:
        """Get the full history of status changes for an item"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM status_logs 
            WHERE item_id = ?
            ORDER BY timestamp DESC
        ''', (item_id,))
        return [StatusLog.from_row(row) for row in cursor.fetchall()]
    
    def delete_item(self, item_id: int):
        """Delete an inventory item"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM inventory_items WHERE id = ?', (item_id,))
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        self.conn.close()


class ImagePreviewWidget(QWidget):
    """Widget to preview and manage images"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setText("No image")
        self.image_path: Optional[str] = None
        
        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        
        self.btn_select = QPushButton("Select Image")
        self.btn_clear = QPushButton("Clear Image")
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_select)
        btn_layout.addWidget(self.btn_clear)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.btn_select.clicked.connect(self._select_image)
        self.btn_clear.clicked.connect(self._clear_image)
    
    def _select_image(self):
        """Open file dialog to select an image"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.image_path = file_path
            self._display_image(file_path)
    
    def _clear_image(self):
        """Clear the current image"""
        self.image_path = None
        self.image_label.setText("No image")
    
    def _display_image(self, path: str):
        """Display the selected image"""
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.image_label.setText("Failed to load image")
            return
        scaled_pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, 
                                      Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
    
    def get_image_path(self) -> Optional[str]:
        """Get the selected image path"""
        return self.image_path


class StatusChangeDialog(QDialog):
    """Dialog for recording status changes"""
    
    def __init__(self, item: InventoryItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Change Status: {item.name}")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        info_label = QLabel(f"Current item: {item.name} (SN: {item.serial_number})")
        info_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(info_label)
        
        form = QFormLayout()
        self.person_name = QLineEdit()
        self.department = QLineEdit()
        
        form.addRow("Person Name:", self.person_name)
        form.addRow("Department:", self.department)
        layout.addLayout(form)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("Previous Status:"))
        self.prev_status = QLabel(item.current_status)
        status_layout.addWidget(self.prev_status)
        
        status_layout.addWidget(QLabel("New Status:"))
        self.new_status = QComboBox()
        self.new_status.addItems([s for s in STATUSES if s != item.current_status])
        status_layout.addWidget(self.new_status)
        
        layout.addLayout(status_layout)
        
        form2 = QFormLayout()
        self.reason = QLineEdit()
        self.location = QLineEdit()
        self.comment = QTextEdit()
        self.comment.setMaximumHeight(100)
        
        form2.addRow("Change Reason:", self.reason)
        form2.addRow("New Location:", self.location)
        form2.addRow("Comment:", self.comment)
        layout.addLayout(form2)
        
        self.image_widget = ImagePreviewWidget()
        layout.addWidget(self.image_widget)
        
        btn_layout = QHBoxLayout()
        self.btnSave = QPushButton("Save")
        self.btnClear = QPushButton("Clear All")
        self.btnCancel = QPushButton("Cancel")
        
        self.btnSave.setDefault(True)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btnClear)
        btn_layout.addWidget(self.btnSave)
        btn_layout.addWidget(self.btnCancel)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.btnSave.clicked.connect(self._save)
        self.btnClear.clicked.connect(self._clear)
        self.btnCancel.clicked.connect(self.reject)
    
    def _save(self):
        """Save the status change"""
        if not self.person_name.text():
            QMessageBox.warning(self, "Error", "Person name is required")
            return
        if not self.department.text():
            QMessageBox.warning(self, "Error", "Department is required")
            return
        if not self.reason.text():
            QMessageBox.warning(self, "Error", "Reason is required")
            return
        if not self.location.text():
            QMessageBox.warning(self, "Error", "Location is required")
            return
        
        self.accept()
    
    def _clear(self):
        """Clear all fields"""
        self.person_name.clear()
        self.department.clear()
        self.reason.clear()
        self.location.clear()
        self.comment.clear()
        self.image_widget._clear_image()
    
    def get_data(self) -> Dict[str, Any]:
        """Get the form data"""
        return {
            'person_name': self.person_name.text(),
            'department': self.department.text(),
            'previous_status': self.item.current_status,
            'new_status': self.new_status.currentText(),
            'reason': self.reason.text(),
            'location': self.location.text(),
            'comment': self.comment.toPlainText(),
            'image_path': self.image_widget.get_image_path()
        }


class ReportDialog(QDialog):
    """Dialog to show item history report"""
    
    def __init__(self, item: InventoryItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setWindowTitle(f"Report: {item.name}")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        info_layout = QHBoxLayout()
        info_label = QLabel(f"Item: {item.name} | Serial: {item.serial_number} | Asset: {item.company_asset_number}")
        info_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(info_label)
        info_layout.addWidget(QLabel(f"Current Status: {item.current_status}"))
        info_layout.addWidget(QLabel(f"Location: {item.location}"))
        layout.addLayout(info_layout)
        
        if item.image_path and os.path.exists(item.image_path):
            img_label = QLabel()
            pixmap = QPixmap(item.image_path)
            scaled_pixmap = pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            img_label.setPixmap(scaled_pixmap)
            layout.addWidget(img_label)
        
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Timestamp", "Person", "Department", "From", "To", "Reason", "Location", "Comment"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Make timestamp column wider
        table.setColumnWidth(0, 200)
        
        history = self.parent().database.get_item_history(item.id)
        table.setRowCount(len(history))
        
        for row, log in enumerate(history):
            # Format timestamp to military time (24-hour format)
            ts = log.timestamp
            try:
                if 'T' in str(ts):
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                else:
                    dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")  # Military time format
            except:
                pass
            table.setItem(row, 0, QTableWidgetItem(str(ts)))
            table.setItem(row, 1, QTableWidgetItem(log.person_name))
            table.setItem(row, 2, QTableWidgetItem(log.department))
            table.setItem(row, 3, QTableWidgetItem(log.previous_status))
            table.setItem(row, 4, QTableWidgetItem(log.new_status))
            table.setItem(row, 5, QTableWidgetItem(log.reason))
            table.setItem(row, 6, QTableWidgetItem(log.location))
            table.setItem(row, 7, QTableWidgetItem(log.comment))
        
        layout.addWidget(table)
        
        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inventory Tracker")
        self.setMinimumSize(1200, 800)
        
        self.database = DatabaseManager()
        
        self._setup_ui()
        self._refresh_items()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_items)
        self.timer.start(5000)
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, serial number, or asset number...")
        self.search_input.textChanged.connect(self._handle_search)
        
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._handle_search)
        
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addStretch()
        
        main_layout.addLayout(search_layout)
        
        tabs = QTabWidget()
        
        items_widget = QWidget()
        items_layout = QVBoxLayout()
        items_widget.setLayout(items_layout)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "Name", "Serial #", "Asset #", "Status", "Location", "Updated", "Image"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.items_table.itemDoubleClicked.connect(self._edit_item)
        
        items_layout.addWidget(self.items_table)
        
        item_btn_layout = QHBoxLayout()
        
        self.btnAddItem = QPushButton("Add Item")
        self.btnAddItem.clicked.connect(self._add_item)
        
        self.btnUpdateStatus = QPushButton("Update Status")
        self.btnUpdateStatus.clicked.connect(self._update_status)
        
        self.btnViewReport = QPushButton("View Report")
        self.btnViewReport.clicked.connect(self._view_report)
        
        self.btnDelete = QPushButton("Delete")
        self.btnDelete.clicked.connect(self._delete_item)
        
        item_btn_layout.addWidget(self.btnAddItem)
        item_btn_layout.addWidget(self.btnUpdateStatus)
        item_btn_layout.addWidget(self.btnViewReport)
        item_btn_layout.addWidget(self.btnDelete)
        
        items_layout.addLayout(item_btn_layout)
        
        tabs.addTab(items_widget, "Items")
        
        overview_widget = QWidget()
        overview_layout = QVBoxLayout()
        overview_widget.setLayout(overview_layout)
        
        self.overview_table = QTableWidget()
        self.overview_table.setColumnCount(7)
        self.overview_table.setHorizontalHeaderLabels([
            "Name", "Serial #", "Asset #", "Status", "Location", "Updated", "Image"
        ])
        self.overview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.overview_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.overview_table.itemDoubleClicked.connect(self._edit_item)
        
        overview_layout.addWidget(QLabel("Last 15 Updated Items:"))
        overview_layout.addWidget(self.overview_table)
        
        tabs.addTab(overview_widget, "Overview")
        
        main_layout.addWidget(tabs)
        
        self.statusBar().showMessage("Ready")
    
    def _handle_search(self):
        """Handle search input"""
        query = self.search_input.text().strip()
        if query:
            items = self.database.search_items(query)
        else:
            items = self.database.get_last_n_items(50)
        self._update_table(self.items_table, items)
    
    def _refresh_items(self):
        """Refresh the item tables"""
        query = self.search_input.text().strip()
        if query:
            items = self.database.search_items(query)
            self._update_table(self.items_table, items)
        else:
            items = self.database.get_last_n_items(50)
            self._update_table(self.items_table, items)
        
        self._update_table(self.overview_table, self.database.get_last_n_items(15))
    
    def _update_table(self, table: QTableWidget, items: List[InventoryItem]):
        """Update a table with items"""
        table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            table.setItem(row, 0, QTableWidgetItem(item.name))
            table.setItem(row, 1, QTableWidgetItem(item.serial_number))
            table.setItem(row, 2, QTableWidgetItem(item.company_asset_number))
            table.setItem(row, 3, QTableWidgetItem(item.current_status))
            table.setItem(row, 4, QTableWidgetItem(item.location))
            
            if item.updated_at:
                # Format timestamp to military time (24-hour format)
                ts = item.updated_at
                try:
                    if 'T' in str(ts):
                        dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                    else:
                        dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
                    ts = dt.strftime("%Y-%m-%d %H:%M:%S")  # Military time with seconds
                except:
                    pass
                table.setItem(row, 5, QTableWidgetItem(str(ts)))
            
            if item.image_path:
                img_item = QTableWidgetItem("📄")
                table.setItem(row, 6, img_item)
    
    def _add_item(self):
        """Add a new inventory item"""
        dialog = AddItemDialog(self)
        if dialog.exec():
            item_data = dialog.get_data()
            
            item = InventoryItem(
                id=None,
                name=item_data['name'],
                serial_number=item_data['serial_number'],
                company_asset_number=item_data['company_asset_number'],
                current_status="In inventory",
                location=item_data['location'],
                image_path=item_data['image_path']
            )
            
            item_id = self.database.add_item(item, DEFAULT_TIMEZONE)
            self._log_status_change(item_id, "System", "System", "In inventory", "In inventory", 
                                   "Item created", item_data['location'], "", item_data['image_path'], 
                                   DEFAULT_TIMEZONE)
            
            self._refresh_items()
            self.statusBar().showMessage(f"Added item: {item.name}")
    
    def _edit_item(self, item: QTableWidgetItem = None):
        """Edit an inventory item"""
        row = self.items_table.currentRow()
        if row < 0:
            return
        
        item_name = self.items_table.item(row, 0).text()
        items = self.database.get_all_items()
        item = next((i for i in items if i.name == item_name), None)
        if not item:
            return
        
        dialog = AddItemDialog(self, item)
        if dialog.exec():
            item_data = dialog.get_data()
            item.name = item_data['name']
            item.serial_number = item_data['serial_number']
            item.company_asset_number = item_data['company_asset_number']
            item.location = item_data['location']
            item.image_path = item_data['image_path']
            self.database.update_item(item)
            self._refresh_items()
            self.statusBar().showMessage(f"Updated item: {item.name}")
    
    def _update_status(self):
        """Update item status"""
        row = self.items_table.currentRow()
        if row < 0:
            return
        
        item_name = self.items_table.item(row, 0).text()
        items = self.database.get_all_items()
        item = next((i for i in items if i.name == item_name), None)
        if not item:
            return
        
        dialog = StatusChangeDialog(item, self)
        if dialog.exec():
            data = dialog.get_data()
            
            item.current_status = data['new_status']
            item.location = data['location']
            self.database.update_item(item, DEFAULT_TIMEZONE)
            
            log = StatusLog(
                id=None,
                item_id=item.id,
                person_name=data['person_name'],
                department=data['department'],
                previous_status=data['previous_status'],
                new_status=data['new_status'],
                reason=data['reason'],
                location=data['location'],
                comment=data['comment'],
                timestamp=datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).isoformat(),
                image_path=data['image_path']
            )
            
            self.database.add_status_log(log, DEFAULT_TIMEZONE)
            self._refresh_items()
            self.statusBar().showMessage(f"Status changed for {item.name}")
    
    def _view_report(self):
        """View item history report"""
        row = self.items_table.currentRow()
        if row < 0:
            return
        
        item_name = self.items_table.item(row, 0).text()
        items = self.database.get_all_items()
        item = next((i for i in items if i.name == item_name), None)
        if not item:
            return
        
        dialog = ReportDialog(item, self)
        dialog.exec()
    
    def _delete_item(self):
        """Delete an inventory item"""
        row = self.items_table.currentRow()
        if row < 0:
            return
        
        item_name = self.items_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Delete Item",
            f"Are you sure you want to delete '{item_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            items = self.database.get_all_items()
            item = next((i for i in items if i.name == item_name), None)
            if item:
                self.database.delete_item(item.id)
                self._refresh_items()
                self.statusBar().showMessage(f"Deleted item: {item_name}")
    
    def _log_status_change(self, item_id, person, dept, prev_status, new_status, reason, location, comment, image_path=None, timezone=None):
        """Internal method to log status changes"""
        if timezone is None:
            timezone = DEFAULT_TIMEZONE
        log = StatusLog(
            id=None,
            item_id=item_id,
            person_name=person,
            department=dept,
            previous_status=prev_status,
            new_status=new_status,
            reason=reason,
            location=location,
            comment=comment,
            timestamp=datetime.now(ZoneInfo(timezone)).isoformat(),
            image_path=image_path
        )
        self.database.add_status_log(log, timezone)
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.database.close()
        event.accept()


class AddItemDialog(QDialog):
    """Dialog for adding/editing inventory items"""
    
    def __init__(self, parent=None, item: Optional[InventoryItem] = None):
        super().__init__(parent)
        self.item = item
        title = "Edit Item" if item else "Add Item"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        self.name_input = QLineEdit(item.name if item else "")
        self.serial_input = QLineEdit(item.serial_number if item else "")
        self.asset_input = QLineEdit(item.company_asset_number if item else "")
        self.location_input = QLineEdit(item.location if item else "")
        
        form.addRow("Item Name:", self.name_input)
        form.addRow("Serial Number:", self.serial_input)
        form.addRow("Company Asset #:", self.asset_input)
        form.addRow("Location:", self.location_input)
        
        layout.addLayout(form)
        
        self.image_widget = ImagePreviewWidget()
        if item and item.image_path:
            self.image_widget._display_image(item.image_path)
            self.image_widget.image_path = item.image_path
        layout.addWidget(self.image_widget)
        
        btn_layout = QHBoxLayout()
        self.btnSave = QPushButton("Save" if item else "Add")
        self.btnCancel = QPushButton("Cancel")
        
        self.btnSave.setDefault(True)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnSave)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        self.btnSave.clicked.connect(self._save)
        self.btnCancel.clicked.connect(self.reject)
    
    def _save(self):
        """Save the item"""
        if not self.name_input.text():
            QMessageBox.warning(self, "Error", "Item name is required")
            return
        if not self.serial_input.text():
            QMessageBox.warning(self, "Error", "Serial number is required")
            return
        if not self.asset_input.text():
            QMessageBox.warning(self, "Error", "Company asset number is required")
            return
        if not self.location_input.text():
            QMessageBox.warning(self, "Error", "Location is required")
            return
        
        self.accept()
    
    def get_data(self) -> Dict[str, str]:
        """Get the form data"""
        return {
            'name': self.name_input.text(),
            'serial_number': self.serial_input.text(),
            'company_asset_number': self.asset_input.text(),
            'location': self.location_input.text(),
            'image_path': self.image_widget.get_image_path()
        }


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
