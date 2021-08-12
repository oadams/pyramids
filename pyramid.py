import argparse
import copy
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd # type: ignore
import plotnine as p9 # type: ignore


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
    else:
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
    else:
        return 'Sport'


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """ The name of this function suggests it's not yet clear what I want it to do.
    """

    # Get all clean free ascents (not weighting the rope)
    df = df[df['Ascent Type'].apply(lambda x: clean_free(x) or x in BATTLE_TO_TOP)]
    print("Number of clean ascents: {}".format(len(df)))

    df['Ascent Type'] = pd.Categorical(df['Ascent Type'], ['Onsight', 'Flash', 'Red point', 'Pink point', 'Clean', 'Top Rope onsight', 'Top rope flash', 'Second clean', 'Top rope clean', 'Roped Solo', 'Hang dog', 'Top rope with rest', 'Second with rest'])
    df = df.sort_values('Ascent Type')

    df = df.drop_duplicates(['Route ID'])

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

    #Groups = np.array([[7, 33, 17, 27],[6, 24, 22, 20],[14, 12, 5, 22], [3, 2, 1, 4], [5, 2, 2, 4]])
    #group_sum = np.array([0, 0])
    counts = dict()
    tick_types = ['trad_onsights', 'sport_onsights', 'trad_flashes', 'sport_flashes', 'trad_redpoints',
                  'sport_redpoints', 'pinkpoints', 'cleans', 'clean_seconds', 'clean_topropes',
                  'battle_to_top']
    for tick_type in tick_types:
        counts[tick_type] = np.zeros(24)
    for grade in range(1, 25):
        if grade == 18:
            print(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'])
        counts['trad_onsights'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Onsight'][df['Style'] == 'Trad'])
        counts['sport_onsights'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Onsight'][df['Style'] == 'Sport'])
        counts['trad_flashes'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Flash'][df['Style'] == 'Trad'])
        counts['sport_flashes'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Flash'][df['Style'] == 'Sport'])
        counts['trad_redpoints'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'][df['Style'] == 'Trad'])
        counts['sport_redpoints'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Red point'][df['Style'] == 'Sport'])
        counts['pinkpoints'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Pink point'])
        counts['cleans'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'] == 'Clean'])
        counts['clean_seconds'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'].isin(['Second clean'])])
        counts['clean_topropes'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'].isin(['Top Rope onsight', 'Top rope flash', 'Top rope clean', 'Roped Solo'])])
        counts['battle_to_top'][grade-1] = len(df[df['Ewbanks Grade'] == grade][df['Ascent Type'].isin(['Hang dog', 'Top rope with rest', 'Second with rest'])])

    fig = plt.figure(figsize=(15,10))
    ax = fig.add_subplot(1, 1, 1)
    major_ticks = np.arange(0, 26)
    ax.set_yticks(major_ticks)

    sum_ = copy.copy(counts['trad_onsights'])

    plt.barh(range(1, 25), counts['trad_onsights'], color='green', label='Trad onsight')
    plt.barh(range(1, 25), counts['sport_onsights'], left=sum_, color='#98ff98', label='Sport onsight')
    sum_ += counts['sport_onsights']
    plt.barh(range(1, 25), counts['trad_flashes'], left=sum_, color='#800020', label='Trad flash')
    sum_ += counts['trad_flashes']
    #plt.barh(range(1, 25), sport_flashes, left = trad_onsights + sport_onsights + trad_flashes, color='orange')
    plt.barh(range(1, 25), counts['trad_redpoints'], left=sum_, color='red', label='Trad redpoint')
    sum_ += counts['trad_redpoints']
    #plt.barh(range(1, 25), sport_redpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints, color='#FF00FF')
    plt.barh(range(1, 25), counts['pinkpoints'], left=sum_, color='pink', label='Pinkpoint (sport or trad)')
    sum_ += counts['pinkpoints']
    plt.barh(range(1, 25), counts['cleans'], left=sum_, color='xkcd:sky blue', label='Clean lead (yoyo, simulclimbing)')
    sum_ += counts['cleans']
    plt.barh(range(1, 25), counts['clean_seconds'], left=sum_, color='#FFA500', label='Clean second')
    sum_ += counts['clean_seconds']
    plt.barh(range(1, 25), counts['clean_topropes'], left=sum_, color='#FFFF00', label='Clean toprope')
    sum_ += counts['clean_topropes']
    plt.barh(range(1, 25), counts['battle_to_top'], left=sum_, color='gray', label='Battle to top (hangdog, second/toprope weighting rope)')

    _ = ax.legend(loc='center', bbox_to_anchor=(0.5, -0.10), shadow=False, ncol=2)

    # Insert an image
    import matplotlib.image as mpimg
    from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
    from scipy import ndimage
    photo = mpimg.imread('animation/photos/20210704_160700.jpg')
    photo = ndimage.rotate(photo, -90)
    imagebox = OffsetImage(photo, zoom=0.1)
    ab = AnnotationBbox(imagebox, (8, 7))
    ax.add_artist(ab)

    plt.show()


def create_animation(df):
    print(df.sort_values(['Ascent Date']))


parser = argparse.ArgumentParser()
parser.add_argument('csv', help='Your logbook from thecrag.com in CSV format.')

# How about we try doing all the IO here and make all our functions pure?
if __name__ == '__main__':
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    df = prepare_df(df)
    #plots = create_plots(df)
    #p9.save_as_pdf_pages(plots, filename='plot2.pdf')
    create_stack_chart(df)
    #create_animation(df)
