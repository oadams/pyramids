""" Generates climb histograms based on exported logbooks from thecrag.com. 

Needs to be cleaned up. Tests and assertions need to be written because its possible the final plot misses some climbs.
"""

import argparse
import copy

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # type: ignore


# The complement of this set is what thecrag considers a 'successful' ascent.
THECRAG_NOT_ON = set(['Attempt', 'Hang dog', 'Retreat', 'Target',
                      'Top rope with rest', 'Second with rest', 'Working'])
# My standard for a clean free ascent rules out the following. Aid solos are
# not free and ticks, top ropes and seconds without any further qualification
# are assumed to have involved weighting the rope.
NOT_ON = THECRAG_NOT_ON.union({'Tick', 'Aid solo', 'Top rope', 'Second'})

BATTLE_TO_TOP = set(['Hang dog', 'Top rope with rest', 'Second with rest'])


def clean_free(ascent_type: str) -> bool:
    """ Returns true if an ascent type is clean and free
        - Clean: The rope was not weighted (toproping is acceptable)
        - Free: Not aid climbing
    """
    return ascent_type not in NOT_ON


def is_ysd(ascent_grade: str) -> bool:
    """ Indicates whether a grade formatted in Yosemite Decimal System. """
    if str(ascent_grade).startswith('5.'):
        return True
    return False


def ysd2ewbanks(grade: str) -> int:
    """ Convert a grade from Yosemite Decimal System to Ewbanks. """

    if grade == '5.5':
        return 12
    elif grade == '5.6':
        return 13
    elif grade == '5.7':
        return 14
    elif grade == '5.8':
        return 15
    elif grade == '5.9':
        return 17
    elif grade == '5.10a':
        return 18
    elif grade == '5.10b':
        return 19
    elif grade == '5.10c':
        return 20
    elif grade == '5.10d':
        return 20
    elif grade == '5.11a':
        return 21
    elif grade == '5.11b':
        return 22
    elif grade == '5.11c':
        return 23
    elif grade == '5.11d':
        return 23
    elif grade == '5.12a':
        return 24
    else:
        return ysd2ewbanks(grade.split()[0])
        raise ValueError("Haven't accounted for YSD grade {}".format(grade))


def is_ewbanks(ascent_grade: str) -> bool:
    """ If a grade can be converted to an integer, then it must be in the
    Ewbanks system, or at least not French or YDS."""
    try:
        int(ascent_grade)
    except ValueError:
        return False
    else:
        return True


def is_ewbanks_or_ysd(ascent_grade: str) -> bool:
    """ True if the grade type is formatted as Ewbanks or Yosemite Decimal,
    False otherwise.
    """
    return is_ewbanks(ascent_grade) or is_ysd(ascent_grade)


def classify_style(crag_path: str) -> str:
    """ 
    # TODO this has changed with the new tick interface on thecrag.
    
    Logbooks downloaded from thecrag.com don't include the style of the
    route as an attribute of the ascent. Instead the route must be referenced
    to determine the ascent type. So what we do here is use a heuristic based
    on climbing areas to determine what is sport and what is trad. However,
    this is not going to be completely accurate.
    """

    if 'Arapiles' in crag_path:
        return 'Trad'
    elif 'Bad Moon Rising Wall' in crag_path:
        return 'Trad'
    elif 'Taipan Wall' in crag_path:
        return 'Trad'
    elif 'The Green Wall' in crag_path:
        return 'Trad'
    elif 'Mt Stapylton Amphitheatre - Central Buttress' in crag_path:
        return 'Trad'
    elif 'Summerday Valley' in crag_path:
        return 'Trad'
    elif 'Yosemite' in crag_path:
        return 'Trad'
    else:
        return 'Sport'


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """ The name of this function suggests it's not yet clear what I want it to do.
    """

    df = df[df['Ascent Type'].apply(lambda x: clean_free(x)
                                    or x in BATTLE_TO_TOP)]
    print("Number of clean ascents: {}".format(len(df)))

    # Filter out my gym climbs
    df = df[df['Crag Path'] != 'Inner Melbourne - Hardrock CBD - Climbing routes']

    # If the ascent gear style is unknown, then inherit the route gear style
    df.loc[df['Ascent Gear Style'].isna(), 'Ascent Gear Style'] = df.loc[df['Ascent Gear Style'].isna(), 'Route Gear Style']

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
                  'Second with rest', 'Top rope with rest', 'Attempt']
    print(categories)
    print(len(categories))
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)
    df = df.sort_values('Ascent Type')
    df = df.drop_duplicates(['Route ID'])
    # Update categories because dash will complain if we have categories with no values
    categories = [category for category in categories if category in df['Ascent Type'].unique()]
    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], categories)

    # Just setting ascent grade to always be the route grade.
    df['Ascent Grade'] = df['Route Grade']
    # Strip R ratings. Currently this needs to happen before check for Ewbanks.
    df['Ascent Grade'] = df['Ascent Grade'].apply(lambda x: x.strip(' R') if isinstance(x, str)
                                                  else x)
    # Remove non-Ewbanks/YSD graded stuff.
    df = df[df['Ascent Grade'].apply(is_ewbanks_or_ysd)]
    print("Number of unique ascents: {}".format(len(df)))
    # TODO Convert remaining grades to Ewbanks
    df['Ewbanks Grade'] = df['Ascent Grade'].apply(lambda x: ysd2ewbanks(x)
                                                   if is_ysd(x) else x)
    df['Ewbanks Grade'] = df['Ewbanks Grade'].apply(lambda x: int(x))

    df['num'] = 1

    # TODO Break stats down by pitches for more fine-grained info. Currently
    # just using whole routes but I would prefer it if the output was per-pitch

    # TODO Separate trad from sport and bouldering

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
