import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from tests.test_data_generator import TestDataGenerator
import psutil
import time

class TestDataVisualizer:
    def __init__(self):
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self.setup_layout()
        self.setup_callbacks()
        self.metrics_history = {
            'cpu_usage': [],
            'memory_usage': [],
            'error_rates': [],
            'upload_times': [],
            'search_times': [],
            'batch_times': [],
            'timestamps': []
        }
    
    def setup_layout(self):
        self.app.layout = dbc.Container([
            html.H1("Safe Remote Backup Test Data Visualization", className="text-center my-4"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Test Data Overview"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(id='file-type-distribution'),
                                    dcc.Graph(id='file-size-distribution')
                                ]),
                                dbc.Col([
                                    dcc.Graph(id='metadata-tags'),
                                    dcc.Graph(id='file-creation-timeline')
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Performance Metrics"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(id='upload-performance'),
                                    dcc.Graph(id='search-performance')
                                ]),
                                dbc.Col([
                                    dcc.Graph(id='batch-operations-performance'),
                                    dcc.Graph(id='response-time-trend')
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("System Load"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(id='system-metrics'),
                                    dcc.Graph(id='error-rates')
                                ]),
                                dbc.Col([
                                    dcc.Graph(id='resource-usage'),
                                    dcc.Graph(id='network-io')
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Test Coverage"),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dcc.Graph(id='coverage-by-module'),
                                    dcc.Graph(id='coverage-trend')
                                ])
                            ])
                        ])
                    ])
                ])
            ]),
            
            dcc.Interval(
                id='interval-component',
                interval=5*1000,  # in milliseconds
                n_intervals=0
            )
        ])
    
    def collect_system_metrics(self):
        """Collect real-time system metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()
        
        timestamp = datetime.now()
        
        self.metrics_history['cpu_usage'].append(cpu_percent)
        self.metrics_history['memory_usage'].append(memory.percent)
        self.metrics_history['timestamps'].append(timestamp)
        
        # Keep only last 100 data points
        max_points = 100
        for key in self.metrics_history:
            if len(self.metrics_history[key]) > max_points:
                self.metrics_history[key] = self.metrics_history[key][-max_points:]
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'disk_percent': disk.percent,
            'net_bytes_sent': net_io.bytes_sent,
            'net_bytes_recv': net_io.bytes_recv,
            'timestamp': timestamp
        }
    
    def setup_callbacks(self):
        @self.app.callback(
            [dash.Output('file-type-distribution', 'figure'),
             dash.Output('file-size-distribution', 'figure'),
             dash.Output('metadata-tags', 'figure'),
             dash.Output('file-creation-timeline', 'figure')],
            [dash.Input('interval-component', 'n_intervals')]
        )
        def update_overview_graphs(n):
            # Generate test data
            generator = TestDataGenerator()
            files = generator.generate_file_set(count=100)
            
            # Create file type distribution
            file_types = [os.path.splitext(f['path'])[1] for f in files]
            type_fig = px.pie(
                values=pd.Series(file_types).value_counts().values,
                names=pd.Series(file_types).value_counts().index,
                title="File Type Distribution"
            )
            
            # Create file size distribution
            file_sizes = [os.path.getsize(f['path']) for f in files]
            size_fig = px.histogram(
                x=file_sizes,
                title="File Size Distribution",
                labels={'x': 'File Size (bytes)', 'y': 'Count'}
            )
            
            # Create metadata tags visualization
            all_tags = []
            for f in files:
                all_tags.extend(f['metadata']['tags'])
            tag_fig = px.bar(
                x=pd.Series(all_tags).value_counts().index,
                y=pd.Series(all_tags).value_counts().values,
                title="Metadata Tags Distribution"
            )
            
            # Create file creation timeline
            creation_dates = [datetime.fromisoformat(f['metadata']['created_at']) for f in files]
            timeline_fig = px.scatter(
                x=creation_dates,
                y=[1] * len(creation_dates),
                title="File Creation Timeline"
            )
            
            return type_fig, size_fig, tag_fig, timeline_fig
        
        @self.app.callback(
            [dash.Output('upload-performance', 'figure'),
             dash.Output('search-performance', 'figure'),
             dash.Output('batch-operations-performance', 'figure'),
             dash.Output('response-time-trend', 'figure')],
            [dash.Input('interval-component', 'n_intervals')]
        )
        def update_performance_graphs(n):
            # Simulate performance data
            upload_times = [0.5, 0.7, 0.6, 0.8, 0.4, 0.9, 0.5, 0.6, 0.7, 0.8]
            search_times = [0.1, 0.15, 0.12, 0.18, 0.14, 0.16, 0.13, 0.17, 0.15, 0.11]
            batch_times = [1.2, 1.5, 1.3, 1.6, 1.4, 1.7, 1.3, 1.5, 1.6, 1.4]
            
            # Add new data points
            self.metrics_history['upload_times'].append(upload_times[-1])
            self.metrics_history['search_times'].append(search_times[-1])
            self.metrics_history['batch_times'].append(batch_times[-1])
            
            upload_fig = px.line(
                y=self.metrics_history['upload_times'],
                title="Upload Performance Over Time",
                labels={'y': 'Time (seconds)'}
            )
            
            search_fig = px.line(
                y=self.metrics_history['search_times'],
                title="Search Performance Over Time",
                labels={'y': 'Time (seconds)'}
            )
            
            batch_fig = px.line(
                y=self.metrics_history['batch_times'],
                title="Batch Operations Performance Over Time",
                labels={'y': 'Time (seconds)'}
            )
            
            # Response time trend
            response_trend = px.line(
                y=[sum(times) for times in zip(
                    self.metrics_history['upload_times'],
                    self.metrics_history['search_times'],
                    self.metrics_history['batch_times']
                )],
                title="Overall Response Time Trend",
                labels={'y': 'Time (seconds)'}
            )
            
            return upload_fig, search_fig, batch_fig, response_trend
        
        @self.app.callback(
            [dash.Output('system-metrics', 'figure'),
             dash.Output('error-rates', 'figure'),
             dash.Output('resource-usage', 'figure'),
             dash.Output('network-io', 'figure')],
            [dash.Input('interval-component', 'n_intervals')]
        )
        def update_system_graphs(n):
            # Collect real-time metrics
            metrics = self.collect_system_metrics()
            
            # System metrics
            metrics_fig = go.Figure()
            metrics_fig.add_trace(go.Scatter(
                y=self.metrics_history['cpu_usage'],
                name='CPU Usage (%)'
            ))
            metrics_fig.add_trace(go.Scatter(
                y=self.metrics_history['memory_usage'],
                name='Memory Usage (%)'
            ))
            metrics_fig.update_layout(title="System Resource Usage")
            
            # Error rates
            error_fig = px.line(
                y=self.metrics_history['error_rates'],
                title="Error Rates Over Time",
                labels={'y': 'Error Rate (%)'}
            )
            
            # Resource usage
            resource_fig = go.Figure()
            resource_fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=metrics['disk_percent'],
                title={'text': "Disk Usage"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ))
            
            # Network I/O
            net_fig = go.Figure()
            net_fig.add_trace(go.Scatter(
                y=[metrics['net_bytes_sent']],
                name='Bytes Sent'
            ))
            net_fig.add_trace(go.Scatter(
                y=[metrics['net_bytes_recv']],
                name='Bytes Received'
            ))
            net_fig.update_layout(title="Network I/O")
            
            return metrics_fig, error_fig, resource_fig, net_fig
        
        @self.app.callback(
            [dash.Output('coverage-by-module', 'figure'),
             dash.Output('coverage-trend', 'figure')],
            [dash.Input('interval-component', 'n_intervals')]
        )
        def update_coverage_graphs(n):
            # Simulate coverage data
            modules = ['app', 'auth', 'files', 'admin', 'utils']
            coverage = [85, 92, 88, 95, 90]
            
            # Coverage by module
            module_fig = px.bar(
                x=modules,
                y=coverage,
                title="Coverage by Module",
                labels={'y': 'Coverage (%)'}
            )
            
            # Coverage trend
            trend_fig = px.line(
                y=[85, 87, 89, 91, 90],
                title="Coverage Trend Over Time",
                labels={'y': 'Coverage (%)'}
            )
            
            return module_fig, trend_fig
    
    def run(self, debug=True, port=8050):
        self.app.run_server(debug=debug, port=port)

if __name__ == '__main__':
    visualizer = TestDataVisualizer()
    visualizer.run() 