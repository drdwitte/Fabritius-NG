TITLE = 'Hensor Workbench'
SUBTITLE = 'an AI-powered CMS'
BUTTON_LABELS = ['SEARCH', 'DETAIL', 'LABEL', 'CHAT', 'INSIGHTS']
LOGIN_LABEL = 'LOGIN'
BROWN = '#8b4513'

OPERATORS = {
    'Metadata Filter': {
        'icon': 'filter_alt',
        'description': 'Filter artworks by metadata attributes',
        'params': {
            'source': {
                'type': 'multiselect',
                'label': 'Source Collection',
                'description': 'Filter by collection source (FILTER IN operation)',
                'default': [],
                'options': []  # To be populated from disk
            },
            'artist': {
                'type': 'text',
                'label': 'Artist Name',
                'description': 'Full or partial artist name',
                'default': ''
            },
            'title': {
                'type': 'text',
                'label': 'Work Title',
                'description': 'Full or partial work title',
                'default': ''
            },
            'year_range': {
                'type': 'range',
                'label': 'Year Range',
                'description': 'Filter by year period',
                'default': [None, None],
                'min': 1000,
                'max': 2100
            },
            'inventory_number': {
                'type': 'text',
                'label': 'Inventory Number',
                'description': 'Full or partial inventory number',
                'default': ''
            }
        }
    },
    'Semantic Search': {
        'icon': 'search',
        'description': 'Text-based semantic search using AI',
        'params': {
            'query_text': {
                'type': 'textarea',
                'label': 'Search Text',
                'description': 'Enter text to search for (required)',
                'default': '',
                'required': True
            },
            'result_mode': {
                'type': 'select',
                'label': 'Result Selection Mode',
                'description': 'Choose how to filter results (required)',
                'options': ['top_n', 'last_n', 'similarity_range'],
                'option_labels': {
                    'top_n': 'Top N Results',
                    'last_n': 'Last N Results',
                    'similarity_range': 'Similarity Range'
                },
                'default': 'top_n',
                'required': True
            },
            'n_results': {
                'type': 'number',
                'label': 'Number of Results',
                'description': 'Number of results to return',
                'default': 10,
                'min': 1,
                'max': 1000,
                'conditional': ['top_n', 'last_n']  # Show for these modes
            },
            'similarity_min': {
                'type': 'number',
                'label': 'Minimum Similarity',
                'description': 'Minimum similarity threshold (0-1)',
                'default': 0.0,
                'min': 0.0,
                'max': 1.0,
                'step': 0.01,
                'conditional': ['similarity_range']
            },
            'similarity_max': {
                'type': 'number',
                'label': 'Maximum Similarity',
                'description': 'Maximum similarity threshold (0-1)',
                'default': 1.0,
                'min': 0.0,
                'max': 1.0,
                'step': 0.01,
                'conditional': ['similarity_range']
            }
        }
    },
    'Similarity Search': {
        'icon': 'library_books',
        'description': 'Find visually similar artworks',
        'params': {
            'query_image': {
                'type': 'image',
                'label': 'Query Image',
                'description': 'Upload an image to search for similar artworks (required)',
                'default': None,
                'required': True
            },
            'result_mode': {
                'type': 'select',
                'label': 'Result Selection Mode',
                'description': 'Choose how to filter results (required)',
                'options': ['top_n', 'last_n', 'similarity_range'],
                'option_labels': {
                    'top_n': 'Top N Results',
                    'last_n': 'Last N Results',
                    'similarity_range': 'Similarity Range'
                },
                'default': 'top_n',
                'required': True
            },
            'n_results': {
                'type': 'number',
                'label': 'Number of Results',
                'description': 'Number of results to return',
                'default': 10,
                'min': 1,
                'max': 1000,
                'conditional': ['top_n', 'last_n']
            },
            'similarity_min': {
                'type': 'number',
                'label': 'Minimum Similarity',
                'description': 'Minimum similarity threshold (0-1)',
                'default': 0.0,
                'min': 0.0,
                'max': 1.0,
                'step': 0.01,
                'conditional': ['similarity_range']
            },
            'similarity_max': {
                'type': 'number',
                'label': 'Maximum Similarity',
                'description': 'Maximum similarity threshold (0-1)',
                'default': 1.0,
                'min': 0.0,
                'max': 1.0,
                'step': 0.01,
                'conditional': ['similarity_range']
            }
        }
    },
    'Color Filter': {
        'icon': 'palette',
        'description': 'Filter artworks by color attributes',
    },
    'Pose Search': {
        'icon': 'accessibility_new',
        'description': 'Find artworks with similar human poses',
    },
    'Sketch Search': {
        'icon': 'brush',
        'description': 'Search by drawing or uploading a sketch',
    },
}



