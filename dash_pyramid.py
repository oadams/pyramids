import base64
import datetime
import io
import textwrap

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html, dash_table
import plotly.express as px

import pandas as pd

from pyramid import prepare_df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select'),
            ' your CSV logbook from thecrag.com'
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.B('Routes:'),
    dcc.RadioItems(['Unique', 'Duplicates'], 'Unique', id='unique-radio'),
    html.Br(),
    html.B('Route Gear Style:'),
    dcc.RadioItems(['All', 'Trad', 'Sport'], 'All', id='route-gear-style'),
    html.Br(),
    html.B('Ascent Style:'),
    dcc.RadioItems(['All', 'Trad', 'Sport', 'Second', 'Top rope'], 'All', id='ascent-gear-style'),
    html.Br(),
    html.B('Date range:'),
    html.Br(),
    dcc.DatePickerRange(
        id='date-range',
        min_date_allowed=datetime.date(1900, 1, 1),
        max_date_allowed=datetime.date(2099, 1, 1),
        initial_visible_month=datetime.date(2023, 1, 1),
    ),
    dcc.Loading(
        html.Div(id='output-data-upload')
    ),
])

COLOR_MAP = {
    "Trad onsight": "#036611",
    "Onsight solo": "#036611",
    "Sport onsight": "#06b91f",
    "Second onsight": "#07db24",
    "Top rope onsight": "#06fc28",
    "Trad flash": "#FF6600",
    "Sport flash": "#FF9900",
    "Second flash": "#ffcc00",
    "Top rope flash": "#ffff00",
    "Trad red point": "#990000",
    "Solo": "#990000",
    "Sport red point": "#ff0000",
    "Red point": "#ff0000",
    "Ground up red point": "#ff1188",
    "Pink point": "#ff33cc",
    "Second clean": "#cc66ff",
    "Top rope clean": "#6666ff",
    "Roped Solo": "#3333cc",
    "Aid": "#000066",
    "Aid solo": "#000066",
    "Trad lead with rest": "#666666",
    "Sport lead with rest": "#666666",
    "Hang dog": "#666666",
    "Second with rest": "#999999",
    "Top rope with rest": "#999999",
    "All free with rest": "#999999",
    "Attempt": "#cccccc",
    "Trad attempt": "#cccccc",
    "Sport attempt": "#cccccc",
    "Second attempt": "#cccccc",
    "Top rope attempt": "#cccccc",
    "Retreat": "#cccccc",
    "Working": "#cccccc",
    "Clean": "#6666ff",
    "Tick": "#66cccc",
}

def parse_contents(contents, filename, date, unique, route_gear_style, ascent_gear_style,
                   start_date, end_date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        # Assume that the user uploaded a CSV file
        df = pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    df = prepare_df(df, unique=unique, route_gear_style=route_gear_style, ascent_gear_style=ascent_gear_style, start_date=start_date,
                    end_date=end_date)

    df = df.drop(['Ascent Label', 'Ascent ID', 'Ascent Link', 'Ascent Grade', 'Route Gear Style', 'Ascent Height', 'Route Height', 'Country Link', 'Crag Link'], axis=1)

    df['Comment'] = df['Comment'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x))))

    color_map = {}
    for ascent_type in df['Ascent Type'].unique():
        if ascent_type in COLOR_MAP:
            color_map[ascent_type] = COLOR_MAP[ascent_type]
        else:
            color_map[ascent_type] = "#66cccc"
    fig = px.bar(df, x='num', y='Ewbanks Grade', color='Ascent Type', orientation='h',
                 hover_data=['Country', 'Crag Name', "Route Name", 'Ascent Date', "Comment"],
                 color_discrete_map=color_map,
            labels = {'num': 'Number of ascents'},
    )

    fig.update_traces(hovertemplate=('Ascent Date: %{customdata[3]}<br>'
                                     'Route Name: %{customdata[2]}<br>'
                                     'Crag Name: %{customdata[1]}<br>'
                                     'Country: %{customdata[0]}<br>'
                                     'Comment: %{customdata[4]}'))

    fig.update_layout(
        yaxis = dict(
            tickmode = 'linear',
            tick0 = 1,
            dtick = 1,
        ),
        xaxis = dict(
            tickmode = 'linear',
            tick0 = 0,
            dtick = 5,
        )
    )

    config = {'displayModeBar': False,
              'editSelection': False,
              'editable': False,
              'scrollZoom': False,
              'showAxisDragHandles': False,}

    return html.Div([
        html.H5(filename),
        #dcc.RadioItems(['Unique', 'Duplicates'], 'Unique'),
        #dash_table.DataTable(data=df.to_dict('records'), page_size=10),
        dcc.Graph(figure=fig, config=config)
    ])

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'),
              Input('unique-radio', 'value'),
              Input('route-gear-style', 'value'),
              Input('ascent-gear-style', 'value'),
              Input('date-range', 'start_date'),
              Input('date-range', 'end_date'))
def update_output(list_of_contents, list_of_names, list_of_dates, unique, route_gear_style, ascent_gear_style,
                  start_date, end_date):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d, unique, route_gear_style, ascent_gear_style, start_date,
                           end_date) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run_server(debug=True)
