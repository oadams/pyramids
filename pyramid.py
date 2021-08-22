import argparse
import copy
from typing import List

import matplotlib.animation as animation
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


def get_ascent_counts(df: pd.DataFrame):
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
    return counts


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

    counts = get_ascent_counts(df)

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
    artists = []
    photo = mpimg.imread('animation/photos/20210704_160700.jpg')
    photo = ndimage.rotate(photo, -90)
    imagebox = OffsetImage(photo, zoom=0.1)
    ab = AnnotationBbox(imagebox, (8, 7))
    artists.append([ab])
    #photo = mpimg.imread('animation/photos/20210511_131111.jpg')
    #photo = ndimage.rotate(photo, -90)
    #imagebox = OffsetImage(photo, zoom=0.1)
    #ab = AnnotationBbox(imagebox, (8, 7))
    #artists.append([ab])
    #ax.add_artist(ab)
    #ax.imshow(photo)
    ax2 = fig.add_axes([0.3, 0.2, 0.7, 0.3])
    ims = []
    im = ax2.imshow(photo)
    ims.append([im])
    photo = mpimg.imread('animation/photos/20210511_131111.jpg')
    photo = ndimage.rotate(photo, -90)
    im = ax2.imshow(photo, animated=True)
    ims.append([im])
    print(ims)


    ani = animation.ArtistAnimation(fig, ims, interval=3050, blit=True)

    """
    def prep_anim(ab):
        def animate(frame_number):
            photo = mpimg.imread('animation/photos/20210511_131111.jpg')
            photo = ndimage.rotate(photo, -90)
            imagebox2 = OffsetImage(photo, zoom=0.1)
            ab.offsetbox = imagebox2
            #photo = mpimg.imread('animation/photos/20210511_131111.jpg')
            #imagebox.set_data(photo)
            #print(imagebox._data)
            #print('ok')
            #imagebox.draw()
            return ab
        return animate

    ani = animation.FuncAnimation(fig, prep_anim(ab), repeat=False, interval=2222, blit=True)
    """

    plt.show()


def create_story(df: pd.DataFrame):

    #df = df[df['Ascent Type'] == 'Onsight'][df['Style'] == 'Trad'].sort_values('Ascent Date')
    df = df.sort_values('Ascent Date')

    fig = plt.figure(figsize=(14,9))
    ax = fig.add_subplot(1, 1, 1)
    major_ticks = np.arange(0, 26)
    ax.set_yticks(major_ticks)
    ax.set_xticks(major_ticks)
    ax.set_xlim(left=0, right=20)
    ax.set_ylim(bottom=0, top=20)
    ax.set_ylabel('Grade')
    ax.set_xlabel('Count')


    #counts = get_ascent_counts(df.iloc[:3])
    counts = get_ascent_counts(df.iloc[:0])
    sum_ = copy.copy(counts['trad_onsights'])
    trad_onsights_barh = plt.barh(range(1, 25), counts['trad_onsights'], color='green', label='Trad onsight')
    sport_onsights_barh = plt.barh(range(1, 25), counts['sport_onsights'], left=sum_, color='#98ff98', label='Sport onsight')
    sum_ += counts['sport_onsights']
    trad_flashes_barh = plt.barh(range(1, 25), counts['trad_flashes'], left=sum_, color='#800020', label='Trad flash')
    sum_ += counts['trad_flashes']
    #plt.barh(range(1, 25), sport_flashes, left = trad_onsights + sport_onsights + trad_flashes, color='orange')
    trad_redpoints_barh = plt.barh(range(1, 25), counts['trad_redpoints'], left=sum_, color='red', label='Trad redpoint')
    sum_ += counts['trad_redpoints']
    #plt.barh(range(1, 25), sport_redpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints, color='#FF00FF')
    pinkpoints_barh = plt.barh(range(1, 25), counts['pinkpoints'], left=sum_, color='pink', label='Pinkpoint (sport or trad)')
    sum_ += counts['pinkpoints']
    cleans_barh = plt.barh(range(1, 25), counts['cleans'], left=sum_, color='xkcd:sky blue', label='Clean lead (yoyo, simulclimbing)')
    sum_ += counts['cleans']
    clean_seconds_barh = plt.barh(range(1, 25), counts['clean_seconds'], left=sum_, color='#FFA500', label='Clean second')
    sum_ += counts['clean_seconds']
    clean_topropes_barh = plt.barh(range(1, 25), counts['clean_topropes'], left=sum_, color='#FFFF00', label='Clean toprope')
    sum_ += counts['clean_topropes']
    battle_to_top_barh = plt.barh(range(1, 25), counts['battle_to_top'], left=sum_, color='gray', label='Battle to top (hangdog, second/toprope weighting rope)')

    import matplotlib.image as mpimg
    from matplotlib.offsetbox import TextArea, DrawingArea, OffsetImage, AnnotationBbox
    from scipy import ndimage
    artists = []
    photo = mpimg.imread('animation/photos/20210704_160700.jpg')
    photo = ndimage.rotate(photo, -90)
    imagebox = OffsetImage(photo, zoom=0.1)
    ab = AnnotationBbox(imagebox, (8, 7))
    photo_map = {
        'Start': mpimg.imread('animation/photos/20210509_092007.jpg'),
        'Cloaca': ndimage.rotate(mpimg.imread('animation/photos/20210511_131111.jpg'), -90),
        'ScarIet Sage': mpimg.imread('animation/photos/scarlet_sage.png'),
        'Diapason': ndimage.rotate(mpimg.imread('animation/photos/20210511_155128.jpg'), -90),
        'Diapason2': mpimg.imread('animation/photos/20210511_155129.jpg'),
        'Tiptoe Ridge': ndimage.rotate(mpimg.imread('animation/photos/20210512_090702.jpg'), -90),
        'Piccolo': ndimage.rotate(mpimg.imread('animation/photos/20210513_113415.jpg'), -90),
        'Piccolo2': mpimg.imread('animation/photos/20210513_113643.jpg'),
        'Mantle': ndimage.rotate(mpimg.imread('animation/photos/20210704_133931.jpg'), -90),
        'Mantle2': mpimg.imread('animation/photos/20210704_160639(0).jpg'),
        'Mantle3': mpimg.imread('animation/photos/20210704_160700.jpg')
    }
    df['photo'] = df.apply(lambda x: photo_map[x['Ascent Label']] if x['Ascent Label'] in photo_map else None, axis=1)

    """
    artists.append([ab])
    #photo = mpimg.imread('animation/photos/20210511_131111.jpg')
    #photo = ndimage.rotate(photo, -90)
    #imagebox = OffsetImage(photo, zoom=0.1)
    #ab = AnnotationBbox(imagebox, (8, 7))
    #artists.append([ab])
    #ax.add_artist(ab)
    #ax.imshow(photo)
    ax2 = fig.add_axes([0.3, 0.2, 0.7, 0.3])
    ims = []
    im = ax2.imshow(photo)
    ims.append([im])
    photo = mpimg.imread('animation/photos/20210511_131111.jpg')
    photo = ndimage.rotate(photo, -90)
    im = ax2.imshow(photo, animated=True)
    ims.append([im])
    print(ims)




    ani = animation.ArtistAnimation(fig, ims, interval=1000, blit=True)
    """

    #width, height = photo.shape[0], photo.shape[1]
    #ax2 = fig.add_axes([0.4, 0.4, 0.00010*width, 0.00010*height])
    #ax2.tick_params(left=False,
    #                bottom=False)
    #ax2.set(xticklabels=[], yticklabels=[])
    #ax2.imshow(photo, aspect='auto')

    photo = photo_map['Start']
    width, height = photo.shape[0], photo.shape[1]
    ax3 = fig.add_axes([0.4, 0.2, 0.00016*height, 0.00016*width])
    ax3.tick_params(left=False,
                    bottom=False)
    ax3.set(xticklabels=[], yticklabels=[])
    ax3.axis('off')
    ax3.imshow(photo)

    _ = ax.legend([clean_seconds_barh, clean_topropes_barh, battle_to_top_barh], ['clean seconds', 'clean topropes', 'weighted rope'], loc='center', bbox_to_anchor=(0.5, -0.10), shadow=False, ncol=3)

    def prepare_animation(trad_onsights_barh):
        def animate(frame_number):
            photo = df.iloc[frame_number-1].photo
            if photo is not None:
                width, height = photo.shape[0], photo.shape[1]
                ax3.imshow(photo)
            print(frame_number)
            counts = get_ascent_counts(df.iloc[:frame_number])
            print(counts)
            trad_onsights_barh_new = ax.barh(range(1, 25), counts['trad_onsights'], color='green', label='Trad onsight')
            trad_onsights_barh.patches = trad_onsights_barh_new.patches
            sum_ = copy.copy(counts['trad_onsights'])
            sport_onsights_barh_new = ax.barh(range(1, 25), counts['sport_onsights'], left=sum_, color='#98ff98', label='Sport onsight')
            sport_onsights_barh.patches = sport_onsights_barh_new.patches
            sum_ += counts['sport_onsights']
            trad_flashes_barh_new = ax.barh(range(1, 25), counts['trad_flashes'], left=sum_, color='#800020', label='Trad flash')
            trad_flashes_barh.patches = trad_flashes_barh_new.patches
            sum_ += counts['trad_flashes']
            #ax.barh_new(range(1, 25), sport_flashes, left = trad_onsights + sport_onsights + trad_flashes, color='orange')
            trad_redpoints_barh_new = ax.barh(range(1, 25), counts['trad_redpoints'], left=sum_, color='red', label='Trad redpoint')
            trad_redpoints_barh.patches = trad_redpoints_barh_new.patches
            sum_ += counts['trad_redpoints']
            #ax.barh_new(range(1, 25), sport_redpoints, left = trad_onsights + sport_onsights + trad_flashes + sport_flashes + trad_redpoints, color='#FF00FF')
            pinkpoints_barh_new = ax.barh(range(1, 25), counts['pinkpoints'], left=sum_, color='pink', label='Pinkpoint (sport or trad)')
            pinkpoints_barh.patches = pinkpoints_barh_new.patches
            sum_ += counts['pinkpoints']
            cleans_barh_new = ax.barh(range(1, 25), counts['cleans'], left=sum_, color='xkcd:sky blue', label='Clean lead (yoyo, simulclimbing)')
            cleans_barh.patches = cleans_barh_new.patches
            sum_ += counts['cleans']
            clean_seconds_barh_new = ax.barh(range(1, 25), counts['clean_seconds'], left=sum_, color='#FFA500', label='Clean second')
            clean_seconds_barh.patches = clean_seconds_barh_new.patches
            sum_ += counts['clean_seconds']
            clean_topropes_barh_new = ax.barh(range(1, 25), counts['clean_topropes'], left=sum_, color='#FFFF00', label='Clean toprope')
            clean_topropes_barh.patches = clean_topropes_barh_new.patches
            sum_ += counts['clean_topropes']
            battle_to_top_barh_new = ax.barh(range(1, 25), counts['battle_to_top'], left=sum_, color='gray', label='Battle to top (hangdog, second/toprope weighting rope)')
            battle_to_top_barh.patches = battle_to_top_barh_new.patches
            if frame_number > 0:
                ax.set_title(f'{df.iloc[frame_number-1]["Ascent Label"]}', fontsize=40)

        return animate

    ani = animation.FuncAnimation(fig, prepare_animation(trad_onsights_barh), len(df)+1, repeat=False, interval=2500)

    tag = ani.to_html5_video()
    with open('tag.html', 'w') as f:
        print(tag, file=f)

    plt.show()


parser = argparse.ArgumentParser()
parser.add_argument('csv', help='Your logbook from thecrag.com in CSV format.')

# How about we try doing all the IO here and make all our functions pure?
if __name__ == '__main__':
    args = parser.parse_args()
    df = pd.read_csv(args.csv)
    df = prepare_df(df)
    #plots = create_plots(df)
    #p9.save_as_pdf_pages(plots, filename='plot2.pdf')
    #create_stack_chart(df)
    create_story(df)
