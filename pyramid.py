"""
Generates climb histograms based on exported logbooks from thecrag.com.

Needs to be cleaned up. Tests and assertions need to be written because its possible the final plot misses some climbs.
"""

import argparse
import textwrap

import pandas as pd  # type: ignore


# The complement of this set is what thecrag considers a 'successful' ascent.
THECRAG_NOT_ON = set(['Attempt', 'Hang dog', 'Retreat', 'Target',
                      'Top rope with rest', 'Second with rest', 'Working'])
# My standard for a clean free ascent rules out the following. Aid solos are
# not free and ticks, top ropes and seconds without any further qualification
# are assumed to have involved weighting the rope.
NOT_ON = THECRAG_NOT_ON.union({'Tick', 'Aid solo', 'Top rope', 'Second'})

BATTLE_TO_TOP = set(['Hang dog', 'Top rope with rest', 'Second with rest', 'All free with rest',
                     'Tick'])


def clean_free(ascent_type: str) -> bool:
    """ Returns true if an ascent type is clean and free
        - Clean: The rope was not weighted (toproping is acceptable)
        - Free: Not aid climbing
    """
    return ascent_type not in NOT_ON


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


def convert_to_ewbanks(grade: str) -> int:
    """ Convert a grade to Ewbanks. Currently supports Yosemite Decimal System and French. """

    if is_ewbanks(grade):
        return int(grade)
    elif grade in GRADE_MAP:
        return GRADE_MAP[grade]
    else:
        raise ValueError(f'Cannot convert grade {grade} to Ewbanks. Code currently assumes only YDS or French.')


def grade_supported(grade: str) -> bool:
    try:
        convert_to_ewbanks(grade)
    except ValueError:
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


def prepare_df(df: pd.DataFrame, drop_duplicates=True) -> pd.DataFrame:
    """ The name of this function suggests it's not yet clear what I want it to do.
    """

    print("Number of ascents: {}".format(len(df)))

    # If the ascent gear style is unknown, then inherit the route gear style
    df.loc[df['Ascent Gear Style'].isna(), 'Ascent Gear Style'] = df.loc[df['Ascent Gear Style'].isna(), 'Route Gear Style']
    df.loc[df['Ascent Gear Style'] == 'Unknown', 'Ascent Gear Style'] = df.loc[df['Ascent Gear Style'] == 'Unknown', 'Route Gear Style']

    # If the Ascent Gear Type is Top rope or second, then change the Ascent type
    # to conform to the old format This is to account for the new ticking
    # interface on thecrag.
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Top rope with rest'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Clean'), 'Ascent Type'] = 'Top rope clean'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Top rope onsight'
    df.loc[(df['Ascent Gear Style'] == 'Top rope') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Top rope flash'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Hang dog'), 'Ascent Type'] = 'Second with rest'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Clean'), 'Ascent Type'] = 'Second clean'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Second onsight'
    df.loc[(df['Ascent Gear Style'] == 'Second') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Second flash'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Trad red point'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Trad onsight'
    df.loc[(df['Ascent Gear Style'] == 'Trad') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Trad flash'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Sport red point'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Sport onsight'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Sport flash'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Sport red point'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Sport onsight'
    df.loc[(df['Ascent Gear Style'] == 'Sport') & (df['Ascent Type'] == 'Flash'), 'Ascent Type'] = 'Sport flash'
    df.loc[(df['Ascent Gear Style'] == 'Free solo') & (df['Ascent Type'] == 'Red point'), 'Ascent Type'] = 'Solo'
    df.loc[(df['Ascent Gear Style'] == 'Free solo') & (df['Ascent Type'] == 'Onsight'), 'Ascent Type'] = 'Onsight solo'
    # TODO Handle other free solo subvariants.
    # TODO Handle 'Second'/'tick' etc.
    # TODO Look at this and sort out edge cases df[['Ascent Type', 'Ascent Gear Style']].drop_duplicates(). There might be some cases that are missing.
    # TODO Now that there is a second flash and second onsight possibility, This code should go through teh log history and flag second cleans as second flashes or onsights.
    # TODO I'm not including soloing here. Scrange's onsight solo of tullah's tease is not being rendered.

    # Here we impose an ordering on ascent types, sort by them and then remove
    # duplicate ascents so that only the best ascent of a given climb is used
    # in the pyramid.

    # TODO Use this commented ordering as an alternative ordering when a flag is set.
    """
    categories = ['Trad onsight', 'Trad flash', 'Sport onsight', 'Sport flash', 'Trad red point',  'Sport red point', 'Pink point', 'Second onsight', 'Second flash',
                  'Top rope onsight', 'Top rope flash', 'Second clean',
                  'Top rope clean', 'Roped Solo', 'Clean', 'Hang dog', 'Aid',
                  'Top rope with rest', 'Second with rest']
    """
    categories = ['Trad onsight', 'Onsight solo', 'Sport onsight', 'Second onsight', 'Top rope onsight',
                  'Trad flash', 'Sport flash', 'Second flash', 'Top rope flash',
                  'Trad red point', 'Solo', 'Sport red point', 'Pink point', 'Second clean', 'Top rope clean',
                  'Roped Solo', 'Clean', 'Aid', 'Hang dog',
                  'Second with rest', 'Top rope with rest', 'Attempt', 'Onsight', 'Flash', 'Top rope', 'Lead', 'Tick', 'All free with rest']
    print(categories)
    print(len(categories))
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)
    df = df.sort_values('Ascent Type')
    print("Number of ascents after handling categories: {}".format(len(df)))
    if drop_duplicates:
        df = df.drop_duplicates(['Route ID'])
    print("Number of ascents after dropping duplicates: {}".format(len(df)))

    # Just setting ascent grade to always be the route grade.
    df['Ascent Grade'] = df['Route Grade']
    # Strip R ratings.
    df['Ascent Grade'] = df['Ascent Grade'].apply(lambda x: x.strip(' R') if isinstance(x, str)
                                                  else x)
    # Remove non-Ewbanks/YSD graded stuff.
    df['Ewbanks Grade'] = df['Ascent Grade'].apply(lambda x: convert_to_ewbanks(x) if
                                                   grade_supported(x) else None)
    print('NA grades:')
    print(df[df['Ewbanks Grade'].isna()])
    df = df.dropna(subset=['Ewbanks Grade'])

    df['num'] = 1

    # TODO Break stats down by pitches for more fine-grained info. Currently
    # just using whole routes but I would prefer it if the output was per-pitch

    # TODO Separate trad from sport and bouldering

    df['Ascent Date'] = pd.to_datetime(df['Ascent Date'])
    df['Ascent Date'] = df['Ascent Date'].dt.strftime('%d/%m/%Y')
    df['Comment'] = df['Comment'].apply(lambda x: textwrap.fill(str(x)))


    # Update categories because dash will complain if we have categories with no values
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)

    print("Number of ascents at end of preprocessing {}".format(len(df)))

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
