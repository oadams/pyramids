import argparse
from typing import List

import pandas as pd # type: ignore
import plotnine as p9 # type: ignore


# The complement of this set is what thecrag considers a 'successful' ascent.
THECRAG_NOT_ON = set(['Attempt', 'Hang dog', 'Retreat', 'Target',
                      'Top rope with rest', 'Second with rest', 'Working'])
# My standard for a clean free ascent rules out the following. Aid solos are
# not free and ticks, top ropes and seconds without any further qualification
# are assumed to have involved weighting the rope.
NOT_ON = THECRAG_NOT_ON.union({'Tick', 'Aid solo', 'Top rope', 'Second'})


def clean_free(ascent_type: str) -> bool:
    """ Returns true if an ascent type is clean and free
        - Clean: The rope was not weighted (toproping is acceptable)
        - Free: Not aid climbing
    """
    return ascent_type not in NOT_ON


def is_ysd(ascent_grade: str) -> bool:
    """ Indicates whether a grade formatted in Yosemite Decimal System. """
    if ascent_grade.startswith('5.'):
        return True
    else:
        return False

def ysd2ewbanks(grade: str) -> int:
    """ Convert a grade from Yosemite Decimal System to Ewbanks. """

    if grade == '5.5': return 12
    elif grade == '5.6': return 13
    elif grade == '5.7': return 14
    elif grade == '5.8': return 15
    elif grade == '5.9': return 17
    elif grade == '5.10a': return 18
    elif grade == '5.10b': return 19
    elif grade == '5.10c': return 20
    else:
        raise ValueError("Haven't accouned for YSD grade {}".format(grade))


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
    return is_ewbanks(ascent_grade) or is_ysd(ascent_grade)


def classify_style(crag_path: str) -> str:
    if 'Arapiles' in crag_path: return 'Trad'
    elif 'Bad Moon Rising Wall' in crag_path: return 'Trad'
    elif 'Taipan Wall' in crag_path: return 'Trad'
    elif 'The Green Wall' in crag_path: return 'Trad'
    elif 'Mt Stapylton Amphitheatre - Central Buttress' in crag_path: return 'Trad'
    elif 'Summerday Valley' in crag_path: return 'Trad'
    else:
        return 'Sport'


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """ The name of this function suggests it's not yet clear what I want it to do.
    """

    # Get all clean free ascents (not weighting the rope)
    df = df[df['Ascent Type'].apply(clean_free)]
    print("Number of clean ascents: {}".format(len(df)))

    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], ['Onsight', 'Flash', 'Red point', 'Pink point', 'Clean', 'Top Rope onsight', 'Top rope flash', 'Second clean', 'Top rope clean', 'Roped Solo'])

    df = df.sort_values('Ascent Type')

    # Temporarily: just removing duplicate routes so we can just plot a pyramid
    # for clean ascents. When we want to plot different ascent types with
    # different colours, this will break down because it might not choose the
    # best ascent type (e.g. it might prune out a flash in favour of a
    # red-point. # TODO handle choosing the best ascent type
    df = df.drop_duplicates(['Route ID'])
    # TODO Remove repeats by taking the best ascent.

    df['Style'] = df['Crag Path'].apply(lambda x: classify_style(x))

    # Remove non-Ewbanks/YSD graded stuff.
    df = df[df['Ascent Grade'].apply(is_ewbanks_or_ysd)]
    print("Number of unique clean ascents: {}".format(len(df)))
    # TODO Convert remaining grades to Ewbanks
    df['Ewbanks Grade'] = df['Ascent Grade'].apply(lambda x: ysd2ewbanks(x) if is_ysd(x) else x)
    df['Ewbanks Grade'] = df['Ewbanks Grade'].apply(lambda x: int(x))

    # TODO Break stats down by pitches for more fine-grained info. Currently
    # just using whole routes but I would prefer it if the output was per-pitch

    # TODO Separate trad from sport and bouldering

    return df


def create_plots(df: pd.DataFrame) -> List[p9.ggplot]:
    plots = [p9.ggplot(df) + p9.geom_bar(p9.aes(x='Ewbanks Grade'))]
    return plots


def create_stack_chart(df: pd.DataFrame):
    """
    import numpy as np
    import pandas as pd
    from pandas import Series, DataFrame
    import matplotlib.pyplot as plt

    data1 = [23,85, 72, 43, 52]
    data2 = [42, 35, 21, 16, 9]
    plt.bar(range(len(data1)), data1)
    plt.bar(range(len(data2)), data2, bottom=data1)
    plt.show()
    """

    import matplotlib.pyplot as plt
    import numpy as np

    #Groups = np.array([[7, 33, 17, 27],[6, 24, 22, 20],[14, 12, 5, 22], [3, 2, 1, 4], [5, 2, 2, 4]])
    #group_sum = np.array([0, 0])
    trad_onsights = np.zeros(24)
    sport_onsights = np.zeros(24)
    trad_flashes = np.zeros(24)
    sport_flashes = np.zeros(24)
    trad_redpoints = np.zeros(24)
    sport_redpoints = np.zeros(24)
    pinkpoints = np.zeros(24)
    cleans = np.zeros(24)
    clean_topropes = np.zeros(24)
    for grade in range(1, 25):
        if grade == 18:
            print(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'])
        trad_onsights[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Onsight'][df['Style'] == 'Trad'])
        sport_onsights[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Onsight'][df['Style'] == 'Sport'])
        trad_flashes[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Flash'][df['Style'] == 'Trad'])
        sport_flashes[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Flash'][df['Style'] == 'Sport'])
        # TODO need to remove non-unique redbpoints.
        trad_redpoints[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'][df['Style'] == 'Trad'])
        sport_redpoints[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'][df['Style'] == 'Sport'])
        pinkpoints[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Pink point'])
        cleans[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Clean'])
        clean_topropes[grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'].isin(['Top Rope onsight', 'Top rope flash', 'Top rope clean', 'Roped Solo', 'Second clean'])])


    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    major_ticks = np.arange(0, 26)
    ax.set_yticks(major_ticks)

    print(trad_onsights)
    print(trad_redpoints)
    print(cleans)
    print(clean_topropes)
    plt.barh(range(1, 25), trad_onsights, color='green')
    plt.barh(range(1, 25), sport_onsights, left = trad_onsights, color='#98ff98')
    plt.barh(range(1, 25), trad_flashes, left = trad_onsights + sport_onsights, color='orange')
    #plt.barh(range(1, 25), sport_flashes, left = trad_onsights + sport_onsights + trad_flashes, color='orange')
    plt.barh(range(1, 25), trad_redpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes, color='red')
    #plt.barh(range(1, 25), sport_redpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints, color='#FF00FF')
    plt.barh(range(1, 25), pinkpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints + sport_redpoints, color='pink')
    plt.barh(range(1, 25), cleans, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints + sport_redpoints + pinkpoints, color='xkcd:sky blue')
    plt.barh(range(1, 25), clean_topropes, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints + sport_redpoints + pinkpoints + cleans, color='gray')
    print(trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints + sport_redpoints + pinkpoints)

    plt.show()


parser = argparse.ArgumentParser()
parser.add_argument('csv', help='Your logbook from thecrag.com in CSV format.')

# How about we try doing all the IO here and make all our functions pure?
if __name__ == '__main__':
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    df = prepare_df(df)
    print(set(df['Ascent Type']))
    plots = create_plots(df)
    p9.save_as_pdf_pages(plots, filename='plot2.pdf')
    create_stack_chart(df)
