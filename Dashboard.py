# Import necessary libraries
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import dash_leaflet as dl
import plotly.express as px
import pandas as pd

# Import your CRUD module
from animal_shelter import AnimalShelter

# MongoDB Atlas connection details
uri = "mongodb+srv://zoo:animalzoo@animalzoo.jwsifbd.mongodb.net/?retryWrites=true&w=majority&appName=animalzoo"
db_name = "animalzoo"  # Replace with your actual database name
collection_name = "animals"  # Replace with your actual collection name

# Initialize the AnimalShelter object with the correct URI
shelter = AnimalShelter(uri, db_name, collection_name)

# Read all data from the MongoDB collection
df = pd.DataFrame.from_records(shelter.read({}))

# Drop the '_id' column if it exists
if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)

# Initialize Dash app
app = Dash(__name__)

# Dashboard Layout / View
app.layout = html.Div([
    html.Div([
         html.Img(src='/assets/grazioso.png', style={'width': '150px', 'height': 'auto'}),
        html.Center(html.B(html.H1('SNHU CS-340 Dashboard')))
    ], style={'textAlign': 'center'}),
    html.Hr(),
    html.Div([
        html.Label('Select Animal Type:'),
        dcc.Dropdown(
            id='animal-type-dropdown',
            options=[{'label': animal, 'value': animal} for animal in df['animal_type'].unique()],
            value=None,
            placeholder='Select an animal type',
            style={'width': '50%'}
        ),
        html.Br(),
        html.Label('Select Animal Age:'),
        dcc.RadioItems(
            id='animal-age-radio',
            options=[
                {'label': 'Young', 'value': 'young'},
                {'label': 'Adult', 'value': 'adult'},
                {'label': 'Senior', 'value': 'senior'}
            ],
            value=None,
            labelStyle={'display': 'inline-block'}
        ),
    ]),
    html.Br(),
    dash_table.DataTable(
        id='datatable-id',
        columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in df.columns
        ],
        data=df.to_dict('records'),
        filter_action='native',
        sort_action='native',
        page_size=10,
        style_table={'overflowX': 'auto'},
        style_cell={
            'height': 'auto',
            'minWidth': '150px', 'maxWidth': '200px',
            'whiteSpace': 'normal'
        },
        row_selectable='single',
    ),
    html.Br(),
    html.Hr(),
    html.Div([
        dcc.Graph(id='animal-type-pie-chart'),
        dcc.Graph(id='outcome-pie-chart')
    ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'}),
    html.Hr(),
    html.Div(
        id='map-id',
        className='col s12 m6',
    )
])

# Interaction Between Components / Controller
@app.callback(
    Output('datatable-id', 'style_data_conditional'),
    [Input('datatable-id', 'selected_columns')]
)
def update_styles(selected_columns):
    if selected_columns is None:
        return []
    return [{
        'if': {'column_id': i},
        'background_color': '#D2F3FF'
    } for i in selected_columns]

@app.callback(
    Output('datatable-id', 'data'),
    [Input('animal-type-dropdown', 'value'),
     Input('animal-age-radio', 'value')]
)
def update_table(selected_animal, selected_age):
    query = {}
    
    if selected_animal:
        query['animal_type'] = selected_animal
    
    if selected_age:
        if selected_age == 'young':
            query['age_upon_outcome_in_weeks'] = {'$lt': 52}
        elif selected_age == 'adult':
            query['age_upon_outcome_in_weeks'] = {'$gte': 52, '$lt': 312}
        elif selected_age == 'senior':
            query['age_upon_outcome_in_weeks'] = {'$gte': 312}
    
    filtered_df = pd.DataFrame.from_records(shelter.read(query))
    
    if '_id' in filtered_df.columns:
        filtered_df.drop(columns=['_id'], inplace=True)
    
    return filtered_df.to_dict('records')

@app.callback(
    Output('map-id', "children"),
    [Input('datatable-id', "derived_virtual_data"),
     Input('datatable-id', "derived_virtual_selected_rows")]
)
def update_map(viewData, index):
    if viewData is None or len(viewData) == 0:
        return [html.P("No data available to display.")]
    
    dff = pd.DataFrame(viewData)
    
    if dff.empty:
        return [html.P("No data available to display.")]

    if index is None or len(index) == 0:
        row = 0
    else:
        row = index[0]

    # Define the latitude and longitude column names
    latitude_col = 'location_lat'  
    longitude_col = 'location_long'  

    # Check if latitude and longitude columns are present
    if latitude_col not in dff.columns or longitude_col not in dff.columns:
        return [html.P("Location data not available for the selected row.")]

    # Check if the selected row has valid latitude and longitude values
    if pd.isna(dff[latitude_col].iloc[row]) or pd.isna(dff[longitude_col].iloc[row]):
        return [html.P("Location data not available for the selected row.")]

    return [
        dl.Map(style={'width': '1000px', 'height': '500px'},
               center=[dff[latitude_col].iloc[row], dff[longitude_col].iloc[row]], zoom=10, children=[
            dl.TileLayer(id="base-layer-id"),
            dl.Marker(position=[dff[latitude_col].iloc[row], dff[longitude_col].iloc[row]],
                      children=[
                          dl.Tooltip(dff.iloc[row]['name']),  # Display animal name as tooltip
                          dl.Popup([
                              html.H1(dff.iloc[row]['name']),  # Display animal name in popup
                              html.P(f"Breed: {dff.iloc[row]['breed']}"),  # Display breed in popup
                              html.P(f"Age: {dff.iloc[row]['age_upon_outcome']}")  # Display age in popup
                          ])
                      ])
        ])
    ]

@app.callback(
    Output('animal-type-pie-chart', 'figure'),
    [Input('datatable-id', 'data')]
)
def update_animal_type_pie(data):
    if not data:
        return {}

    dff = pd.DataFrame(data)
    fig = px.pie(dff, names='animal_type', title='Animal Type Distribution')
    return fig

@app.callback(
    Output('outcome-pie-chart', 'figure'),
    [Input('datatable-id', 'data')]
)
def update_outcome_pie(data):
    if not data:
        return {}

    dff = pd.DataFrame(data)
    fig = px.pie(dff, names='outcome_type', title='Outcome Type Distribution')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
