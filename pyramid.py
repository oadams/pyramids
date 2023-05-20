"""
Generates climb histograms based on exported logbooks from thecrag.com.

Needs to be cleaned up. Tests and assertions need to be written because its possible the final plot misses some climbs.
"""

import argparse
from typing import Union

import pandas as pd  # type: ignore


# The complement of this set is what thecrag considers a 'successful' ascent.
THECRAG_NOT_ON = set(['Attempt', 'Hang dog', 'Retreat', 'Target',
                      'Top rope with rest', 'Second with rest', 'Working'])
# My standard for a clean free ascent rules out the following. Aid solos are
# not free and ticks, top ropes and seconds without any further qualification
# are assumed to have involved weighting the rope.
NOT_ON = THECRAG_NOT_ON.union({'Tick', 'Aid solo', 'Top rope', 'Second', 'Lead', 'Aid'})

COUNTRY_TO_CONTEXT = {
    'Austria': 'UIAA',
    'Bulgaria': 'UIAA',
    'Czech Republic': 'UIAA',
    'Denmark': 'UIAA',
    'Germany': 'UIAA',
    'Hungary': 'UIAA',
    'Montenegro': 'UIAA',
    'Slovakia': 'UIAA',
    'Ireland': 'British',
    'Jersey': 'British',
    'United Kingdom': 'British',
    'Kenya': 'British'
}

GYMS = ['Inner Melbourne - Hardrock CBD - Climbing routes']

CONTEXT_GRADE_TO_EWBANKS = {
    'UIAA': {
        '1-': 1,
        '1': 2,
        '1+': 3,
        '2-': 4,
        '2': 5,
        '2+': 7,
        '3-': 8,
        '3': 9,
        '3+': 10,
        '4-': 11,
        '4': 12,
        '4+': 13,
        '5-': 14,
        '5': 15,
        '5+': 16,
        '6-': 16,
        '6': 17,
        '6+': 18,
        '7-': 19,
        '7': 20,
        '7+': 21,
        '8-': 22,
        '8': 23,
        '8+': 25,
        '9-': 26,
        '9': 27,
        '9+': 28,
        '10-': 29,
        '10': 31,
        '10+': 32,
        '11-': 33,
        '11': 34,
        '11+': 35,
        '12-': 37,
        '12': 38,
        '12+': 39
    },
    'British': {
        '1a': 1,
        '1b': 2,
        '1c': 4,
        '2a': 5,
        '2b': 6,
        '2c': 7,
        '3a': 8,
        '3b': 10,
        '3c': 11,
        '4a': 12,
        '4b': 14,
        '4c': 16,
        '5a': 18,
        '5b': 20,
        '5c': 22,
        '6a': 24,
        '6b': 26,
        '6c': 29,
        '7a': 31,
        '7b': 34,
        '7c': 36,
    }
}

GRADE_MAP = {
    '3.0': 1,
    '4.0': 3,
    '5.0': 4,
    '5.1': 6,
    '5.2': 7,
    '5.3': 9,
    '5.4': 10,
    '5.5': 12,
    '5.6': 13,
    '5.7': 14,
    '5.8': 15,
    '5.9': 17,
    '5.10a': 18,
    '5.10b': 19,
    '5.10c': 20,
    '5.10d': 20,
    '5.11a': 21,
    '5.11b': 22,
    '5.11c': 23,
    '5.11d': 23,
    '5.12a': 24,
    '5.12b': 25,
    '5.12c': 26,
    '5.12d': 27,
    '5.13a': 28,
    '5.13b': 29,
    '5.13c': 30,
    '5.13d': 31,
    '5.14a': 32,
    '5.14b': 33,
    '5.14c': 34,
    '5.14d': 35,
    '5.15a': 36,
    '5.15b': 37,
    '5.15c': 38,
    '5.15d': 39,
    '1a': 1,
    '1a+': 1,
    '1b': 2,
    '1b+': 3,
    '1c': 4,
    '1c+': 4,
    '2a': 5,
    '2a+': 5,
    '2b': 6,
    '2b+': 7,
    '2c': 8,
    '2c+': 8,
    '3a': 9,
    '3a+': 10,
    '3b': 10,
    '3b+': 11,
    '3c': 11,
    '3c+': 12,
    '4a': 13,
    '4a+': 13,
    '4b': 14,
    '4b+': 14,
    '4c': 15,
    '4c+': 15,
    '5a': 16,
    '5a+': 16,
    '5b': 16,
    '5b+': 17,
    '5c': 17,
    '5c+': 18,
    '6a': 18,
    '6a+': 19,
    '6b': 20,
    '6b+': 21,
    '6c': 22,
    '6c+': 22,
    '7a': 23,
    '7a+': 24,
    '7b': 25,
    '7b+': 26,
    '7c': 27,
    '7c+': 28,
    '8a': 29,
    '8a+': 30,
    '8b': 31,
    '8b+': 32,
    '8c': 33,
    '8c+': 34,
    '9a': 35,
    '9a+': 36,
    '9b': 37,
    '9b+': 38,
    '9c': 39,
}


def convert_to_ewbanks(grade: str, country: str) -> int:
    """ Convert a grade to Ewbanks. The idea is to support Ewbanks, YDS, French, British and UIAA.

    No gradings in Ewbanks, YDS, and French lead to ambiguities about the grading system used.
    However, British grades can look like French grades and UIAA grades can look like Ewbanks
    grades. The strategy we employ is to use the country to determine if a British or UIAA grade
    context should be used. Otherwise, we just handle it as Ewbanks, YDS, or French.

    There are two main limitations of this approach:
        - Climbs reported using other grading systems will either get dropped or cause the system to
          misgrade them if they are visually indistinct from, say, the French grades.
        - Climbs that are graded in a way inconsistent with their grade context may be incorrectly
          mapped. For example, there are sport climbs in the UK graded with the French system.
          However in the CSV logbook the grade system is not shown, although it is shown on thecrag
          UI. If we use the grade context we would assume the climb is a British graded climb. Such
          is life, the only way around this is either to scrape every climb on thecrag, or for
          thecrag to specify the grading system in the logbook CSV.
    """

    if country in COUNTRY_TO_CONTEXT:
        context = COUNTRY_TO_CONTEXT[country]
        # Here we split into components to remove things like British adverbial.
        for component in grade.split():
            if component in CONTEXT_GRADE_TO_EWBANKS[context]:
                return CONTEXT_GRADE_TO_EWBANKS[context][component]
        # If we get here and we couldn't convert it, then maybe it's in French... so we back off
        # to code below.

    # We split into components to handle stuff like aid grades, R ratings and X ratings.
    for component in grade.split():
        if is_ewbanks(component):
            return int(component)
        elif component in GRADE_MAP: # Handle French and YDS
            return GRADE_MAP[component]
    raise ValueError(f'Cannot convert grade {grade} to Ewbanks. Code currently supports French '
                     'YDS, British and UIAA')


def grade_supported(grade: str, country: str) -> bool:
    try:
        convert_to_ewbanks(grade, country)
    except (ValueError, AttributeError):
        return False

    return True


def is_ewbanks(ascent_grade: str) -> bool:
    """ If a grade can be converted to an integer, then it must be in the
    Ewbanks system, or at least not French or YDS.

    The check as it stands might think some UIAA climbs are Ewbanks. To make this more robust
    location information should be used as well.
    """
    try:
        int(ascent_grade)
    except ValueError:
        return False
    else:
        return True


def reconcile_old_ticks_with_new_ticks(df: pd.DataFrame) -> pd.DataFrame:
    """ Handle discrepancy between old ticking interface and new ticking interface on thecrag."""

    # If the Ascent Gear Type is Top rope or second, then change the Ascent type
    # to conform to the old format This is to account for the new ticking
    # interface on thecrag.
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Top rope with rest'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Clean'), 'Ascent Type'] = 'Top rope clean'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Top rope onsight'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Top rope flash'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Attempt'), 'Ascent Type'] = 'Top rope attempt'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Second with rest'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Clean'), 'Ascent Type'] = 'Second clean'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Second onsight'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Second flash'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Attempt'), 'Ascent Type'] = 'Second attempt'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Trad red point'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Trad onsight'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Trad flash'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Trad lead with rest'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Attempt'), 'Ascent Type'] = 'Trad attempt'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Sport red point'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Sport onsight'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Sport flash'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Sport red point'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Attempt'), 'Ascent Type'] = 'Sport attempt'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Sport lead with rest'
    df.loc[(df['Ascent Gear Style'] == 'Free solo') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Solo'
    df.loc[(df['Ascent Gear Style'] == 'Free solo') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Onsight solo'
    return df


def prepare_df(df: pd.DataFrame, unique: str = 'Unique', route_gear_style: str = 'All',
               ascent_gear_style: str = 'All',
               start_date: Union[str, None] = None, end_date: Union[str, None] = None,
               country: Union[str, None] = None, free_only: bool = False, gym: str = 'Outside') -> pd.DataFrame:
    """ Prepares a dataframe for consumption by the dash app.  """

    # Do all our filtering first before any subsequent processing
    if free_only:
        df = df[~df['Ascent Type'].isin(NOT_ON)]

    df = df[df['Route Gear Style'] != 'Boulder']

    if country is not None:
        df = df[df['Country'] == country]

    df['Ascent Date'] = pd.to_datetime(df['Ascent Date'])
    if start_date is not None:
        start_date = pd.to_datetime(start_date, utc=True)
        df = df[df['Ascent Date'] >= start_date]
    if end_date is not None:
        end_date = pd.to_datetime(end_date, utc=True)
        df = df[df['Ascent Date'] <= end_date]

    if route_gear_style != 'All':
        df = df[df['Route Gear Style'] == route_gear_style]

    # Drop targets, marks and hits, which are all non-climbs.
    df = df[df['Ascent Type'] != 'Target']
    df = df[df['Ascent Type'] != 'Mark']
    df = df[df['Ascent Type'] != 'Hit']

    # If the ascent gear style is unknown, then inherit the route gear style
    df.loc[df['Ascent Gear Style'].isna(), 'Ascent Gear Style'] = df.loc[df['Ascent Gear Style'].isna(), 'Route Gear Style']
    df.loc[df['Ascent Gear Style'] == 'Unknown', 'Ascent Gear Style'] = df.loc[df['Ascent Gear Style'] == 'Unknown', 'Route Gear Style']

    df = reconcile_old_ticks_with_new_ticks(df)

    if ascent_gear_style == 'Lead':
        df = df[df['Ascent Type'].isin(['Trad onsight', 'Onsight solo', 'Trad flash', 'Trad red point', 'Solo', 'Trad lead with rest', 'Trad attempt', 'Sport onsight', 'Sport flash', 'Sport red point', 'Pink point', 'Sport lead with rest', 'Sport attempt'])]
    elif ascent_gear_style == 'Second':
        df = df[df['Ascent Type'].isin(['Second onsight', 'Second flash', 'Second clean', 'Second with rest', 'Second', 'Second attempt'])]
    elif ascent_gear_style == 'Top rope':
        df = df[df['Ascent Type'].isin(['Top rope onsight', 'Top rope flash', 'Top rope clean', 'Top rope with rest', 'Top rope', 'Top rope attempt'])]

    # Now do actual manipulations of the dataframe
    df['Ascent Date'] = df['Ascent Date'].dt.strftime('%d/%m/%Y')

    # Here we impose an ordering on ascent types, sort by them and then remove
    # duplicate ascents so that only the best ascent of a given climb is used
    # in the pyramid.
    categories = ['Trad onsight', 'Onsight solo', 'Sport onsight', 'Second onsight', 'Top rope onsight',
                  'Trad flash', 'Sport flash', 'Second flash', 'Top rope flash',
                  'Trad red point', 'Solo', 'Sport red point', 'Red point', 'Ground up red point',
                  'Pink point', 'Second clean', 'Top rope clean',
                  'Roped Solo', 'Clean', 'Aid', 'Aid solo', 'Trad lead with rest',
                  'Sport lead with rest', 'Hang dog', 'Second with rest', 'Top rope with rest',
                  'Trad attempt', 'Sport attempt', 'Second attempt', 'Top rope attempt', 'Attempt',
                  'Retreat', 'Working', 'Onsight', 'Flash', 'Top rope', 'Lead', 'Tick',
                  'All free with rest']
    # Set the dataframe's categories to be the set of ascent types found in the dataframe and
    # maintain the same ordering as this predefined list of categories. Any other ascent types not
    # defined by the ordering are tacked on to the end.
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    for category in df['Ascent Type'].unique():
        if category not in categories:
            categories.append(category)
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)
    df = df.sort_values('Ascent Type')
    # We drop duplicates after doing the ordering so that the best form of the ascent is retained
    if unique == 'Unique':
        df = df.drop_duplicates(['Route ID'])

    # Just setting ascent grade to always be the route grade.
    df['Ascent Grade'] = df['Route Grade']

    # Handle grade conversion
    df['Ewbanks Grade'] = df[['Ascent Grade', 'Country']].apply(lambda x:
                                                                convert_to_ewbanks(x['Ascent Grade'],
                                                                                   x['Country']) if
                                                                grade_supported(x['Ascent Grade'],
                                                                                x['Country']) else None, axis=1)
    print('NA grades:')
    print(df[df['Ewbanks Grade'].isna()][['Route Name', 'Ascent Grade']])
    df = df.dropna(subset=['Ewbanks Grade'])

    # This is used to determine the bar tile width in the bar chart. Every ascent tile should be
    # equal width, so we set this uniformly to 1.
    df['num'] = 1

    df['Gym'] = df['Crag Path'].isin(GYMS)
    if gym == 'Gym':
        df = df[df['Gym']]
    elif gym == 'Outside':
        df = df[~df['Gym']]

    # Update categories because dash will complain if we have categories with no values
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)

    return df


parser = argparse.ArgumentParser()
parser.add_argument('csv', help='Your logbook from thecrag.com in CSV format.')

# How about we try doing all the IO here and make all our functions pure?
if __name__ == '__main__':
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    breakpoint()
    df = prepare_df(df)
    breakpoint()
