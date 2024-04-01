""" A Dash app that creates a dynamic climb pyramid visualization. """

import base64
import datetime
import io
import textwrap

import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import plotly.express as px

import pandas as pd

from pyramid import prepare_df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define the layout that is present when the page is opened
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
    ),
    html.Table(
        html.Tr([
            html.Td(html.Div([
                html.B('Routes:'),
                dcc.RadioItems(['Unique', 'Duplicates', 'Angie Unique'], 'Unique', id='unique-radio')
            ]), style={"vertical-align": "top", 'width': '150px'}),
            html.Td(html.Div([
                html.B('Route Gear Style:'),
                dcc.RadioItems(['All', 'Trad', 'Sport'], 'All', id='route-gear-style'),
            ]), style={"vertical-align": "top", 'width': '150px'}),
            html.Td(html.Div([
                html.B('Ascent Style:'),
                dcc.RadioItems(['All', 'Lead', 'Second', 'Top rope'], 'All', id='ascent-gear-style'),
            ]), style={"vertical-align": "top", 'width': '150px'}),
            html.Td(html.Div([
                html.B('Free:'),
                dcc.RadioItems(['All', 'Free only'], 'All', id='free-ascent'),
            ]), style={"vertical-align": "top", 'width': '150px'}),
            html.Td(html.Div([
                html.B('Outside/Gym:'),
                dcc.RadioItems(['All', 'Outside', 'Gym'], 'Outside', id='gym'),
            ]), style={"vertical-align": "top", 'width': '150px'}),
        ], style={'border': '0px'}),
        style={'border': '0px'}),
    html.Br(),
    html.B('Date Range:'),
    html.Br(),
    dcc.DatePickerRange(
        id='date-range',
        min_date_allowed=datetime.date(1900, 1, 1),
        max_date_allowed=datetime.date(2099, 1, 1),
        initial_visible_month=datetime.date(2023, 1, 1),
    ),
    html.Button('Clear dates', id='clear-dates', n_clicks=0),
    dcc.Loading(
        html.Div(id='output-data-upload')
    ),
])

# A mapping from ascent types to colours
COLOR_MAP = {
    'Trad onsight': '#036611',
    'Onsight solo': '#036611',
    'Sport onsight': '#06b91f',
    'Second onsight': '#07db24',
    'Top rope onsight': '#06fc28',
    'Trad flash': '#FF6600',
    'Sport flash': '#FF9900',
    'Second flash': '#ffcc00',
    'Top rope flash': '#ffff00',
    'Trad red point': '#990000',
    'Solo': '#990000',
    'Sport red point': '#ff0000',
    'Red point': '#ff0000',
    'Ground up red point': '#ff1188',
    'Pink point': '#ff33cc',
    'Second clean': '#cc66ff',
    'Top rope clean': '#6666ff',
    'Roped Solo': '#3333cc',
    'Aid': '#000066',
    'Aid solo': '#000066',
    'Trad lead with rest': '#666666',
    'Sport lead with rest': '#666666',
    'Hang dog': '#666666',
    'Second with rest': '#999999',
    'Top rope with rest': '#999999',
    'All free with rest': '#999999',
    'Attempt': '#cccccc',
    'Trad attempt': '#cccccc',
    'Sport attempt': '#cccccc',
    'Second attempt': '#cccccc',
    'Top rope attempt': '#cccccc',
    'Retreat': '#cccccc',
    'Working': '#cccccc',
    'Clean': '#6666ff',
    'Tick': '#66cccc',
    #'Lead': '#66cccc',
    #'Second': '#66cccc',
    #'Top rope': '#66cccc',
}


def parse_contents(contents, filename, unique, route_gear_style, ascent_gear_style,
                   start_date, end_date, free, gym):
    """ Function that preprocesses the dataframe according to the various other options.  """
    _, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        # Assume that the user uploaded a CSV file
        df = pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
    except Exception as e: # TODO Make this exception less general.
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    df = prepare_df(df, unique=unique, route_gear_style=route_gear_style,
                    ascent_gear_style=ascent_gear_style, start_date=start_date,
                    end_date=end_date, free_only=(free == 'Free only'), gym=gym)

    df = df.drop(['Ascent Label', 'Ascent ID', 'Ascent Link', 'Ascent Grade', 'Route Gear Style',
                  'Ascent Height', 'Route Height', 'Country Link', 'Crag Link'], axis=1)

    # Line wrap the comment so that the mouseovers don't expand to fill the width of the page
    df['Comment'] = df['Comment'].apply(lambda x: '<br>'.join(textwrap.wrap(str(x))))

    # I tried making COLOR_MAP a defaultdict that backed off to #66cccc but for some reason the bar
    # chart did not use those values.
    color_map = {}
    for ascent_type in df['Ascent Type'].unique():
        if ascent_type in COLOR_MAP:
            color_map[ascent_type] = COLOR_MAP[ascent_type]
        else:
            color_map[ascent_type] = '#66cccc'

    # Handling hashtag downclimb
    df['Contains_Downclimb'] = df['Comment'].str.contains('#downclimb', case=False)
    df.loc[df['Contains_Downclimb'].isna(), 'Contains_Downclimb'] = False
    df['bar_text'] = ''
    df.loc[df['Contains_Downclimb'], 'bar_text'] = 'D'

    fig = px.bar(df, x='num', y='Ewbanks Grade', color='Ascent Type', orientation='h',
                 hover_data=['Country', 'Crag Name', 'Route Name', 'Ascent Date', 'Comment'],
                 color_discrete_map=color_map,
                 labels={'num': 'Number of Ascents'},
                 text='bar_text')
    fig.update_traces(textangle=0, textfont_size=10)
    fig.update_layout(uniformtext_minsize=12, uniformtext_mode='show')
    # The layout when you mouse over an ascent tile. `customdata` gives access to the bar chart's
    # hover_data.
    fig.update_traces(hovertemplate=('Ascent Date: %{customdata[3]}<br>'
                                     'Route Name: %{customdata[2]}<br>'
                                     'Crag Name: %{customdata[1]}<br>'
                                     'Country: %{customdata[0]}<br>'
                                     'Comment: %{customdata[4]}'))

    fig.update_layout(
        yaxis=dict(
            tickmode='linear',
            tick0=1,
            dtick=1,
        ),
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=5,
        )
    )

    config = {'displayModeBar': False,
              'editSelection': False,
              'editable': False,
              'scrollZoom': False,
              'showAxisDragHandles': False,}

    return html.Div([
        html.Br(),
        html.B(f'Number of climbs: {len(df)}', style={"color": "#555555"}),
        dcc.Graph(figure=fig, config=config)
    ])

@app.callback(Output('date-range', 'start_date'),
              Output('date-range', 'end_date'),
              Input('clear-dates', 'n_clicks'))
def clear_dates(_):
    """ When the clear date button is clicked, feed None dates into the date picker to reset it. """
    return None, None


@app.callback(Output('output-data-upload', 'children'),
              Output('upload-data', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              Input('unique-radio', 'value'),
              Input('route-gear-style', 'value'),
              Input('ascent-gear-style', 'value'),
              Input('date-range', 'start_date'),
              Input('date-range', 'end_date'),
              Input('free-ascent', 'value'),
              Input('gym', 'value'))
def update_output(content, name, unique, route_gear_style,
                  ascent_gear_style, start_date, end_date, free, gym):
    """ Any time the radio buttons or upload component is changed, handle it and return components
    to render. """
    children = []
    if content is not None:
        children.append(
            parse_contents(content, name, unique,
                           route_gear_style, ascent_gear_style,
                           start_date,
                           end_date, free, gym)
        )


    upload_children=html.Div([
        'Drag and Drop or ',
        html.A('Select'),
        (f' your CSV logbook from thecrag.com: {name}' if name is not None else
         ' your CSV logbook from thecrag.com')
    ]),
    return children, upload_children

if __name__ == '__main__':
    app.run_server(debug=True)
