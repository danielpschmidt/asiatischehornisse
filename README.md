# Asian Hornet (Vespa velutina) Tracking Application

A web application for tracking and visualizing Asian hornet (Vespa velutina) sightings and related data in Switzerland. This application provides interactive visualizations and filtering capabilities to analyze the spread and patterns of Asian hornet occurrences.

## Features

- Interactive data visualization with Plotly
- Filter data by date range, canton, and sighting type
- Temporal analysis with different time units (day, week, month, year)
- Geographic data visualization
- Caching mechanism for improved performance

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Homebrew (for macOS/Linux)
- GEOS library

## Installation

1. **Clone the repository**
   ```bash
   git clone [your-repository-url]
   cd asiatischehornisse
   ```

2. **Set up a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install GEOS (macOS with Homebrew)**
   ```bash
   brew install geos
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   Or use the setup script (macOS/Linux):
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

## Running the Application

1. Start the Flask development server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://localhost:5001
   ```

## Usage

1. **Dashboard Overview**
   - The main dashboard shows an overview of the data
   - Use the filters to narrow down the data:
     - Date range selector
     - Canton selection
     - Sighting type filters

2. **Visualizations**
   - Interactive charts showing trends over time
   - Geographic distribution maps
   - Data tables with detailed information

3. **Exporting Data**
   - Export filtered data as CSV or JSON
   - Save visualizations as PNG or PDF

## Project Structure

```
asiatischehornisse/
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── setup.sh           # Setup script for macOS/Linux
├── templates/         # HTML templates
└── asianhornet/       # Data and additional modules
```

## Data Sources

The application uses data from various sources to track Asian hornet sightings. The data is automatically fetched and processed by the application.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

N/A

## Contact

For questions or feedback, please contact [me(at)dpschmidt.ch]
