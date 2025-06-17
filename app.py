from flask import Flask, render_template, request, jsonify
import json
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.utils
from dateutil.parser import parse
import requests
import time
from functools import wraps

# Simple cache with TTL
class TTLCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key):
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            del self.cache[key]
        return None
    
    def set(self, key, value):
        self.cache[key] = (value, time.time())

# Create a cache instance with 1 hour TTL
cache = TTLCache(ttl=3600)

app = Flask(__name__)

def fetch_data():
    # Check cache first
    cached_data = cache.get('velutina_data')
    if cached_data is not None:
        return cached_data
        
    # If not in cache, fetch from URL
    url = 'https://smapshot-beta.heig-vd.ch/velutina_data/data_from_velu_public.json'
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Store in cache
    cache.set('velutina_data', data)
    return data

# Load and prepare data
def get_processed_data():
    try:
        data = fetch_data()
        df = pd.json_normalize(data['features'])
        
        # Convert timestamp to datetime
        df['date'] = pd.to_datetime(df['properties.date'], unit='ms')
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day'] = df['date'].dt.day
        
        # Extract unique values for filters
        unique_types = sorted(list(set(
            [item for sublist in df['properties.type'].dropna().str.split(',').tolist() 
             for item in sublist if item.strip() != '']
        )))
        unique_cantons = sorted(df['properties.canton'].dropna().unique())
        min_date = (df['date'].min() - timedelta(days=1)).strftime('%Y-%m-%d')
        max_date = (df['date'].max() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        return df, unique_types, unique_cantons, min_date, max_date
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        # Return empty data with default values if there's an error
        return pd.DataFrame(), [], [], '2020-01-01', datetime.now().strftime('%Y-%m-%d')

# Get initial data
df, unique_types, unique_cantons, min_date, max_date = get_processed_data()

def filter_data(selected_types=None, date_range=None, time_unit='day', canton=None, show_months=False):
    filtered_df = df.copy()
    
    # Filter by type
    if selected_types and 'all' not in selected_types:
        mask = filtered_df['properties.type'].apply(
            lambda x: any(t in (x or '').split(',') for t in selected_types)
        )
        filtered_df = filtered_df[mask]
    
    # Filter by canton
    if canton and 'all' not in canton:
        filtered_df = filtered_df[filtered_df['properties.canton'].isin(canton)]
    
    # Filter by date range
    if date_range and len(date_range) == 2:
        start_date = parse(date_range[0])
        end_date = parse(date_range[1])
        filtered_df = filtered_df[
            (filtered_df['date'] >= start_date) & 
            (filtered_df['date'] <= end_date)
        ]
    
    # Group by time unit
    if time_unit == 'day':
        grouped = filtered_df.groupby(['year', 'month', 'day']).size()
        # Ensure all values are integers
        dates = [f"{int(y)}-{int(m):02d}-{int(d):02d}" for y, m, d in grouped.index]
        labels = dates
    elif time_unit == 'month':
        grouped = filtered_df.groupby(['year', 'month']).size()
        # Convert year and month to integers to handle float values
        dates = [f"{int(y)}-{int(m):02d}-01" for y, m in grouped.index]  # Always use first day for proper sorting
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Always show month names with year for January
        labels = []
        for y, m in grouped.index:
            month_idx = int(m) - 1  # Convert to int and adjust for 0-based index
            if show_months or int(m) == 1:  # Always show year for January or if show_months is True
                labels.append(f"{month_names[month_idx]} {int(y)}")
            else:
                labels.append(month_names[month_idx])
    else:  # year
        grouped = filtered_df.groupby(['year']).size()
        # Convert year to integer to handle float values
        dates = [f"{int(y)}-01-01" for y in grouped.index]  # First day of year for proper sorting
        labels = [str(int(y)) for y in grouped.index]
    
    # Sort by date
    sorted_data = sorted(zip(dates, labels, grouped.tolist()))
    if sorted_data:
        dates, labels, counts = zip(*sorted_data)
    else:
        dates, labels, counts = [], [], []
    
    return {
        'dates': dates,
        'labels': list(labels) if labels else [],
        'counts': list(counts) if counts else [],
        'total': len(filtered_df)
    }

@app.route('/')
def index():
    # Refresh data on each page load to ensure we have the latest
    global df, unique_types, unique_cantons, min_date, max_date
    df, unique_types, unique_cantons, min_date, max_date = get_processed_data()
    
    return render_template('index.html', 
                         unique_types=unique_types, 
                         unique_cantons=unique_cantons,
                         min_date=min_date,
                         max_date=max_date)

@app.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    data = request.get_json()
    
    selected_types = data.get('types', [])
    date_range = data.get('dateRange', [])
    time_unit = data.get('timeUnit', 'day')
    canton = data.get('canton', [])
    show_months = data.get('showMonths', False)
    
    result = filter_data(selected_types, date_range, time_unit, canton, show_months)
    
    # Convert any numpy arrays to Python lists for JSON serialization
    x_data = result['labels'] if 'labels' in result else result['dates']
    if hasattr(x_data, 'tolist'):  # Check if it's a numpy array
        x_data = x_data.tolist()
    if hasattr(result['counts'], 'tolist'):  # Check if counts is a numpy array
        counts = result['counts'].tolist()
    else:
        counts = result['counts']
    
    # Create Plotly chart with vertical bars
    fig = px.bar(
        x=x_data,
        y=counts,
        labels={'x': 'Date', 'y': 'Number of Sightings'},
        title='Asian Hornet Sightings Over Time'
    )
    
    # Customize layout
    fig.update_layout(
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=150),  # More bottom margin for x-axis labels
        height=500,  # Initial height, will be adjusted by JavaScript
        xaxis_title='',
        yaxis_title='Number of Sightings',
        xaxis={
            'tickmode': 'array',
            'tickvals': list(range(len(x_data))),
            'ticktext': x_data,
            'tickangle': -45,
            'tickfont': {'size': 10},
            'automargin': True
        },
        yaxis={
            'automargin': True,
            'tickformat': 'd',  # No decimal places for counts
            'gridcolor': 'rgba(0,0,0,0.05)'
        },
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        bargap=0.1  # Gap between bars
    )
    
    # Update bar appearance
    fig.update_traces(
        marker_color='#1f77b4',
        marker_line_color='rgb(8,48,107)',
        marker_line_width=1,
        opacity=0.8,
        width=0.8  # Bar width
    )
    
    # Convert the figure to a dict and ensure all values are JSON serializable
    chart_dict = fig.to_dict()
    
    # Ensure all numpy types are converted to native Python types
    def convert_numpy(obj):
        if hasattr(obj, 'tolist'):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: convert_numpy(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_numpy(item) for item in obj]
        return obj
    
    chart_dict = convert_numpy(chart_dict)
    
    return jsonify({
        'chart': chart_dict,
        'total_sightings': int(result['total'])  # Ensure total is a native Python int
    })

if __name__ == '__main__':
    app.run(debug=True, port=5001)
