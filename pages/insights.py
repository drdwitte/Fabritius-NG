from nicegui import ui, app
from ui_components.header import render_header
from backend.supabase_client import SupabaseClient
from loguru import logger
import routes
import uuid
from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta


# Module-level storage for insights controllers
_insights_controllers = {}


class InsightsPageController:
    """Controller for insights/analytics dashboard."""
    
    def __init__(self):
        # Database client
        self.db = SupabaseClient()
        
        # Sample data - replace with real database queries
        self.data = self._load_sample_data()
        
        # UI references for dynamic updates
        self.chart_containers = {}
        
        # Filter state for charts
        self.tag_activity_period = 'day'
        self.llm_stats_period = 'day'
        self.selected_user = 'Dieter'
        
        # Tag search state
        self.tag_search_input = None
        self.tag_search_results = []
        
        # Tag distribution state
        self.tag_dist_page = 1
        self.tag_dist_page_size = 100
        self.tag_dist_data = None
        self.selected_tag_for_detail = None
    
    def _load_sample_data(self) -> Dict:
        """Load sample operational data - replace with real queries."""
        return {
            'artworks_by_century': {
                '15th': 245,
                '16th': 412,
                '17th': 1876,
                '18th': 634,
                '19th': 2341,
                '20th': 3892,
                '21st': 156
            },
            'validation_status': {
                'AI-Generated': 4523,
                'AI-Reviewed': 2341,
                'Human-Validated': 1876,
                'Expert-Approved': 812
            },
            'top_artists': {
                'Peter Paul Rubens': 234,
                'Pieter Bruegel': 156,
                'Anthony van Dyck': 143,
                'Jacob Jordaens': 98,
                'René Magritte': 87,
                'James Ensor': 76,
                'Rogier van der Weyden': 65,
                'Hieronymus Bosch': 54
            },
            'monthly_validations': {
                'Jan': 234,
                'Feb': 345,
                'Mar': 423,
                'Apr': 567,
                'May': 654,
                'Jun': 723,
                'Jul': 612,
                'Aug': 534,
                'Sep': 678,
                'Oct': 789,
                'Nov': 823,
                'Dec': 756
            },
            'searches_per_algorithm': {
                'Text Embeddings': 1234,
                'Image Embeddings': 876,
                'Multimodal': 543,
                'Metadata Filter': 2341
            },
            'daily_activity': [
                {'date': '2026-02-03', 'searches': 45, 'validations': 23},
                {'date': '2026-02-04', 'searches': 56, 'validations': 31},
                {'date': '2026-02-05', 'searches': 43, 'validations': 28},
                {'date': '2026-02-06', 'searches': 67, 'validations': 35},
                {'date': '2026-02-07', 'searches': 89, 'validations': 42},
                {'date': '2026-02-08', 'searches': 78, 'validations': 38},
                {'date': '2026-02-09', 'searches': 92, 'validations': 45},
            ]
        }
    
    def render_dashboard(self):
        """Render the insights dashboard with interactive Plotly charts."""
        
        # Page title
        with ui.row().classes('w-full items-center justify-between mb-6'):
            ui.label('Operational Insights').classes('text-3xl font-bold')
            
            ui.button(
                icon='refresh',
                on_click=self._refresh_data
            ).props('flat').classes('text-blue-600')
        
        # KPI Cards row
        with ui.row().classes('w-full gap-4 mb-6'):
            total_artworks = self.db.get_total_artworks()
            unique_tags = self.db.get_unique_tags_count()
            assigned_tags = self.db.get_assigned_tags_count()
            
            self._render_kpi_card('Total Artworks', f'{total_artworks:,}', 'collections', 'blue')
            self._render_kpi_card('Unique Tags', f'{unique_tags:,}', 'label', 'green')
            self._render_kpi_card('Assigned Tags', f'{assigned_tags:,}', 'local_offer', 'purple')
        
        # ====================
        # TAG OPERATIONS
        # ====================
        
        # Row 1: Tag activity + Tag distribution
        with ui.row().classes('w-full gap-4 mb-6 items-stretch'):
            # Tag activity over time (Interactive bar chart)
            with ui.card().classes('flex-1 p-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Tag Activity').classes('text-xl font-semibold')
                    
                    # Period selector
                    ui.select(
                        options=['day', 'week', 'month'],
                        value=self.tag_activity_period,
                        on_change=lambda e: self._update_tag_activity_period(e.value)
                    ).classes('w-32').props('dense')
                
                ui.label('Hover for details | Created, Deleted, Promoted, Demoted').classes('text-xs text-gray-500 mb-2')
                
                # Get tag activity data
                activity_data = self.db.get_tag_activity(period=self.tag_activity_period, days=30)
                dates = [d['date'] for d in activity_data]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    name='Created',
                    x=dates,
                    y=[d['created'] for d in activity_data],
                    marker_color='#10b981',
                    hovertemplate='<b>Created</b><br>%{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.add_trace(go.Bar(
                    name='Promoted',
                    x=dates,
                    y=[d['promoted'] for d in activity_data],
                    marker_color='#3b82f6',
                    hovertemplate='<b>Promoted</b><br>%{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.add_trace(go.Bar(
                    name='Demoted',
                    x=dates,
                    y=[d['demoted'] for d in activity_data],
                    marker_color='#f59e0b',
                    hovertemplate='<b>Demoted</b><br>%{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.add_trace(go.Bar(
                    name='Deleted',
                    x=dates,
                    y=[d['deleted'] for d in activity_data],
                    marker_color='#ef4444',
                    hovertemplate='<b>Deleted</b><br>%{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.update_layout(
                    height=400,
                    margin=dict(l=40, r=20, t=20, b=80),
                    xaxis_title='Time Period',
                    yaxis_title='Number of Tags',
                    hovermode='x unified',
                    barmode='group',
                    legend=dict(orientation='h', y=1.15),
                    xaxis_tickangle=-45
                )
                
                self.chart_containers['tag_activity_chart'] = ui.plotly(fig).classes('w-full')
            
            # Tag distribution histogram with pagination
            with ui.card().classes('flex-1 p-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Tag Distribution').classes('text-xl font-semibold')
                
                ui.label('Click on a bar to view artworks with that tag').classes('text-xs text-gray-500 mb-2')
                
                # Load initial tag distribution
                self.tag_dist_data = self.db.get_tag_distribution(page=self.tag_dist_page, page_size=self.tag_dist_page_size)
                
                # Pagination controls
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.button(
                        icon='chevron_left',
                        on_click=self._prev_tag_page
                    ).props('flat').bind_enabled_from(self, 'tag_dist_page', lambda p: p > 1)
                    
                    ui.label().bind_text_from(
                        self,
                        'tag_dist_page',
                        backward=lambda p: f'Page {p} of {self.tag_dist_data["total_pages"]} ({self.tag_dist_data["total_tags"]} total tags)'
                    ).classes('text-xs')
                    
                    ui.button(
                        icon='chevron_right',
                        on_click=self._next_tag_page
                    ).props('flat').bind_enabled_from(
                        self,
                        'tag_dist_page',
                        lambda p: p < self.tag_dist_data['total_pages']
                    )
                
                # Histogram
                with ui.column().classes('w-full') as self.chart_containers['tag_dist_chart_container']:
                    self._render_tag_distribution_chart()
        
        # ====================
        # TAG DETAIL VIEW
        # ====================
        
        # Row 2: Tag search table (full width)
        with ui.row().classes('w-full gap-4 mb-6'):
            with ui.card().classes('w-full p-4'):
                ui.label('Artworks by Tag').classes('text-xl font-semibold mb-4')
                
                # Search input
                with ui.row().classes('w-full gap-2 mb-4'):
                    self.tag_search_input = ui.input(
                        label='Search for tag',
                        placeholder='Enter tag name...'
                    ).classes('flex-1')
                    
                    ui.button(
                        'Search',
                        icon='search',
                        on_click=self._search_tags
                    ).props('color=primary')
                
                # Results table
                with ui.column().classes('w-full') as self.chart_containers['tag_table_container']:
                    if self.tag_search_results:
                        self._render_tag_table()
                    else:
                        ui.label('Enter a tag name to search for artworks').classes('text-gray-500 italic')
        
        # ====================
        # USER ACTIVITY
        # ====================
        
        # Row 3: User contributions + Daily activity
        with ui.row().classes('w-full gap-4 mb-6 items-stretch'):
            # User contributions (GitHub-style calendar)
            with ui.card().classes('flex-1 p-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('User Contributions (Last 90 Days)').classes('text-xl font-semibold')
                    
                    # User selector
                    ui.select(
                        options=['Dieter', 'Lies', 'Karine', 'Lara', 'Wouter', 'Roxanne'],
                        value=self.selected_user,
                        on_change=lambda e: self._update_selected_user(e.value)
                    ).classes('w-40').props('dense')
                
                ui.label('Calendar heatmap: darker green = more activity').classes('text-xs text-gray-500 mb-2')
                
                # Get user contribution data for selected user
                all_contributions = self.db.get_user_contributions(days=90)
                user_data = all_contributions.get(self.selected_user, [])
                
                # Create calendar heatmap
                from datetime import datetime
                
                # Convert to calendar grid
                dates_dt = [datetime.strptime(d['date'], '%Y-%m-%d') for d in user_data]
                
                min_week = min(d.isocalendar()[1] for d in dates_dt)
                max_week = max(d.isocalendar()[1] for d in dates_dt)
                n_weeks = max_week - min_week + 1
                
                # Initialize matrix
                matrix = [[None for _ in range(n_weeks)] for _ in range(7)]
                hover_text = [['' for _ in range(n_weeks)] for _ in range(7)]
                
                # Fill matrix
                for d in user_data:
                    date_obj = datetime.strptime(d['date'], '%Y-%m-%d')
                    week_idx = date_obj.isocalendar()[1] - min_week
                    day_idx = date_obj.weekday()
                    matrix[day_idx][week_idx] = d['count']
                    hover_text[day_idx][week_idx] = f"{d['date']}<br>Changes: {d['count']}"
                
                fig = go.Figure()
                fig.add_trace(
                    go.Heatmap(
                        z=matrix,
                        text=hover_text,
                        hovertemplate='%{text}<extra></extra>',
                        colorscale='Greens',
                        showscale=True,
                        colorbar=dict(title='Activity'),
                        xgap=2,
                        ygap=2,
                        zmin=0,
                        zmax=40,
                        hoverinfo='text'
                    )
                )
                
                fig.update_xaxes(showticklabels=False, showgrid=False, zeroline=False)
                fig.update_yaxes(
                    tickmode='array',
                    tickvals=[0, 1, 2, 3, 4, 5, 6],
                    ticktext=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    showgrid=False,
                    zeroline=False
                )
                
                fig.update_layout(
                    height=350,
                    margin=dict(l=60, r=20, t=20, b=20),
                    plot_bgcolor='#f9fafb'
                )
                
                self.chart_containers['contributions_chart'] = ui.plotly(fig).classes('w-full')
            
            # Daily activity (Multi-line with zoom/pan)
            with ui.card().classes('flex-1 p-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('Daily Activity (Last 7 Days)').classes('text-xl font-semibold')
                
                ui.label('Zoom: drag box | Pan: drag | Reset: double-click').classes('text-xs text-gray-500 mb-2')
                
                dates = [d['date'] for d in self.data['daily_activity']]
                searches = [d['searches'] for d in self.data['daily_activity']]
                validations = [d['validations'] for d in self.data['daily_activity']]
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=searches,
                    name='Searches',
                    mode='lines+markers',
                    line=dict(color='#3b82f6', width=3),
                    hovertemplate='<b>Searches</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=validations,
                    name='Validations',
                    mode='lines+markers',
                    line=dict(color='#10b981', width=3),
                    hovertemplate='<b>Validations</b><br>Date: %{x}<br>Count: %{y}<extra></extra>'
                ))
                fig.update_layout(
                    height=350,
                    margin=dict(l=40, r=20, t=20, b=40),
                    xaxis_title='Date',
                    yaxis_title='Count',
                    hovermode='x unified',
                    legend=dict(orientation='h', y=1.1)
                )
                
                self.chart_containers['activity_chart'] = ui.plotly(fig).classes('w-full')
        
        # ====================
        # TECHNICAL OPERATIONS
        # ====================
        
        # Row 4: LLM Usage Statistics (smaller, bottom section)
        with ui.row().classes('w-full gap-4 mb-6'):
            # LLM Usage Statistics (2 narrow charts stacked)
            with ui.card().classes('w-full p-4'):
                with ui.row().classes('w-full items-center justify-between mb-2'):
                    ui.label('LLM Usage Statistics').classes('text-xl font-semibold')
                    
                    # Period selector
                    ui.select(
                        options=['day', 'week', 'month'],
                        value=self.llm_stats_period,
                        on_change=lambda e: self._update_llm_stats_period(e.value)
                    ).classes('w-32').props('dense')
                
                ui.label('OpenAI API calls and token consumption').classes('text-xs text-gray-500 mb-2')
                
                # Get LLM statistics data
                llm_data = self.db.get_llm_statistics(period=self.llm_stats_period, days=30)
                dates = [d['date'] for d in llm_data]
                
                # API Calls chart (top)
                fig_calls = go.Figure()
                fig_calls.add_trace(go.Bar(
                    x=dates,
                    y=[d['api_calls'] for d in llm_data],
                    marker_color='#3b82f6',
                    hovertemplate='<b>API Calls</b><br>%{x}<br>Count: %{y}<extra></extra>',
                    name='API Calls'
                ))
                fig_calls.update_layout(
                    height=140,
                    margin=dict(l=40, r=20, t=5, b=40),
                    xaxis_title='',
                    yaxis_title='API Calls',
                    showlegend=False,
                    xaxis_tickangle=-45
                )
                ui.plotly(fig_calls).classes('w-full')
                
                # Token Usage chart (bottom)
                fig_tokens = go.Figure()
                fig_tokens.add_trace(go.Bar(
                    x=dates,
                    y=[d['tokens_used'] for d in llm_data],
                    marker_color='#10b981',
                    hovertemplate='<b>Tokens</b><br>%{x}<br>Count: %{y:,.0f}<extra></extra>',
                    name='Tokens'
                ))
                fig_tokens.update_layout(
                    height=140,
                    margin=dict(l=40, r=20, t=5, b=40),
                    xaxis_title='',
                    yaxis_title='Tokens',
                    showlegend=False,
                    xaxis_tickangle=-45
                )
                ui.plotly(fig_tokens).classes('w-full')
    
    def _update_tag_activity_period(self, period: str):
        """Update tag activity chart when period changes."""
        self.tag_activity_period = period
        ui.notify(f'Tag activity period: {period}', type='info')
        # TODO: Rebuild tag activity chart with new period
    
    def _update_llm_stats_period(self, period: str):
        """Update LLM statistics chart when period changes."""
        self.llm_stats_period = period
        ui.notify(f'LLM stats period: {period}', type='info')
        # TODO: Rebuild LLM stats chart with new period
    
    def _update_selected_user(self, user: str):
        """Update user contributions chart when user selection changes."""
        self.selected_user = user
        ui.notify(f'Showing contributions for: {user}', type='info')
        # TODO: Rebuild contributions chart for selected user
    
    def _search_tags(self):
        """Search for artworks by tag name."""
        query = self.tag_search_input.value
        if not query or len(query) < 2:
            ui.notify('Please enter at least 2 characters', type='warning')
            return
        
        # Search database
        self.tag_search_results = self.db.search_artworks_by_tag(query, limit=10)
        ui.notify(f'Found {len(self.tag_search_results)} artworks with tag "{query}"', type='positive')
        
        # Refresh table container
        self.chart_containers['tag_table_container'].clear()
        with self.chart_containers['tag_table_container']:
            self._render_tag_table()
    
    def _render_tag_table(self):
        """Render the tag search results table."""
        if not self.tag_search_results:
            ui.label('No results found').classes('text-gray-500 italic')
            return
        
        # Extract data for Plotly table
        header_values = ['Inventory Nr', 'Artist', 'Title', 'Tag', 'Level', 'Confidence']
        cell_values = [
            [r['inventarisnummer'] for r in self.tag_search_results],
            [r['beschrijving_kunstenaar'] for r in self.tag_search_results],
            [r['beschrijving_titel'] for r in self.tag_search_results],
            [r['tag_name'] for r in self.tag_search_results],
            [r['tag_level'] for r in self.tag_search_results],
            [r['confidence'] for r in self.tag_search_results]
        ]
        
        # Create Plotly table
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=header_values,
                fill_color='#3b82f6',
                font=dict(color='white', size=13),
                align='left',
                height=35
            ),
            cells=dict(
                values=cell_values,
                fill_color=[['white', '#f9fafb'] * 5],  # Alternating row colors
                align=['left', 'left', 'left', 'left', 'center', 'center'],
                font=dict(size=12),
                height=30
            )
        )])
        
        fig.update_layout(
            height=400,
            margin=dict(l=0, r=0, t=0, b=0)
        )
        
        ui.plotly(fig).classes('w-full')
    
    def _render_tag_distribution_chart(self):
        """Render the tag distribution histogram."""
        if not self.tag_dist_data:
            return
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=self.tag_dist_data['tags'],
            y=self.tag_dist_data['counts'],
            marker_color='#8b5cf6',
            hovertemplate='<b>%{x}</b><br>Occurrences: %{y}<br>Click to view artworks<extra></extra>',
            customdata=self.tag_dist_data['tags']
        ))
        
        fig.update_layout(
            height=350,
            margin=dict(l=40, r=20, t=20, b=100),
            xaxis_title='Tags',
            yaxis_title='Number of Occurrences',
            xaxis_tickangle=-45,
            xaxis={'tickmode': 'linear'},
            hovermode='closest'
        )
        
        # Add click event to load artworks for clicked tag
        fig.update_traces(
            marker=dict(
                line=dict(width=1, color='white')
            )
        )
        
        plotly_chart = ui.plotly(fig).classes('w-full')
        plotly_chart.on('plotly_click', self._on_tag_bar_click)
    
    def _on_tag_bar_click(self, event):
        """Handle click on tag distribution bar."""
        if event and 'points' in event.args[0]:
            point = event.args[0]['points'][0]
            tag_name = point.get('x', '')
            
            if tag_name:
                self.selected_tag_for_detail = tag_name
                # Load artworks for this tag
                self.tag_search_results = self.db.search_artworks_by_tag(tag_name, limit=10)
                ui.notify(f'Showing artworks for tag: {tag_name}', type='info')
                
                # Scroll to table and update
                self.chart_containers['tag_table_container'].clear()
                with self.chart_containers['tag_table_container']:
                    self._render_tag_table()
    
    def _prev_tag_page(self):
        """Navigate to previous page of tag distribution."""
        if self.tag_dist_page > 1:
            self.tag_dist_page -= 1
            self.tag_dist_data = self.db.get_tag_distribution(page=self.tag_dist_page, page_size=self.tag_dist_page_size)
            
            # Refresh chart
            self.chart_containers['tag_dist_chart_container'].clear()
            with self.chart_containers['tag_dist_chart_container']:
                self._render_tag_distribution_chart()
    
    def _next_tag_page(self):
        """Navigate to next page of tag distribution."""
        if self.tag_dist_page < self.tag_dist_data['total_pages']:
            self.tag_dist_page += 1
            self.tag_dist_data = self.db.get_tag_distribution(page=self.tag_dist_page, page_size=self.tag_dist_page_size)
            
            # Refresh chart
            self.chart_containers['tag_dist_chart_container'].clear()
            with self.chart_containers['tag_dist_chart_container']:
                self._render_tag_distribution_chart()
    
    def _on_year_change(self, year: str):
        """Handle year filter change - deprecated."""
        pass
    
    def _on_status_change(self, status: str):
        """Handle status filter change - deprecated."""
        pass
    
    def _update_algorithm_chart(self, chart_type: str):
        """Update algorithm chart - deprecated."""
        pass
    
    def _render_kpi_card(self, title: str, value: str, icon: str, color: str):
        """Render a KPI card with icon, title, and value."""
        color_map = {
            'blue': 'bg-blue-50 text-blue-600',
            'green': 'bg-green-50 text-green-600',
            'orange': 'bg-orange-50 text-orange-600',
            'purple': 'bg-purple-50 text-purple-600'
        }
        
        with ui.card().classes(f'flex-1 p-4 {color_map.get(color, "bg-gray-50")}'):
            with ui.row().classes('w-full items-center gap-3'):
                ui.icon(icon).classes(f'text-4xl')
                with ui.column().classes('gap-0'):
                    ui.label(title).classes('text-sm font-medium opacity-80')
                    ui.label(value).classes('text-2xl font-bold')
    
    def _refresh_data(self):
        """Refresh dashboard data - placeholder for real implementation."""
        ui.notify('Dashboard data refreshed', type='positive')
        # TODO: Reload data from database and update charts


@ui.page(routes.ROUTE_INSIGHTS)
def page() -> None:
    """Analytics and insights page."""
    logger.info("Loading Insights page")
    
    # Get or create unique tab ID from browser storage
    if 'tab_id' not in app.storage.browser:
        app.storage.browser['tab_id'] = str(uuid.uuid4())
    
    tab_id = app.storage.browser['tab_id']
    
    # Get or create controller for this tab
    if tab_id not in _insights_controllers:
        logger.info(f"Creating new InsightsPageController for tab {tab_id[:8]}")
        _insights_controllers[tab_id] = InsightsPageController()
    else:
        logger.info(f"Reusing InsightsPageController for tab {tab_id[:8]}")
    
    controller = _insights_controllers[tab_id]
    
    render_header()
    controller.render_dashboard()