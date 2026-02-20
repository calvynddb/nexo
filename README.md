# EduManage SIS - Project Structure

A professional Student Information System (SIS) Academy Management Dashboard built with CustomTkinter.

## Project Files

### Core Application Files
- **`main.py`** - Entry point for the application. Initializes the app, loads data, and manages frame switching.
- **`config.py`** - Configuration and constants (colors, fonts, file paths, etc.)
- **`data.py`** - CSV data handling (load, save, initialize files)

### UI Components & Modules
- **`components.py`** - Reusable UI components:
  - `DepthCard` - Styled frame component
  - `SmartSearchEntry` - Entry with dropdown suggestions
  - `setup_treeview_style()` - Table styling

- **`auth.py`** - Authentication module:
  - `LoginFrame` - Login page with registration support

- **`dashboard.py`** - Main dashboard:
  - `DashboardFrame` - Dashboard layout with sidebar, topbar, and content area
  - Navigation, search, settings, notifications

- **`views.py`** - Data management views:
  - `StudentsView` - Student management
  - `ProgramsView` - Program management with charts
  - `CollegesView` - College directory management

### Data Files
- `colleges.csv` - College data
- `programs.csv` - Program data
- `students.csv` - Student data

## Running the Application

```bash
# Make sure you have the required packages installed
pip install customtkinter

# Optional (for charts in ProgramsView)
pip install matplotlib numpy

# Run the application
python main.py
```

## Default Login Credentials
- **Username:** `admin`
- **Password:** `admin`

## Architecture

The application follows a modular structure:

1. **Separation of Concerns** - Each module handles a specific responsibility
2. **Reusable Components** - Common UI elements in `components.py`
3. **Centralized Configuration** - All constants in `config.py`
4. **Data Layer Abstraction** - CSV operations in `data.py`
5. **View-Controller Pattern** - Views handle UI, controller manages navigation

## Features

- ✅ Student management (add, edit, delete)
- ✅ Program management with enrollment stats
- ✅ College directory management
- ✅ Real-time search and filtering
- ✅ Notifications and settings
- ✅ Professional dark theme UI
- ✅ CSV data persistence
- ✅ Admin login system

## To Run
```
python main.py
```
