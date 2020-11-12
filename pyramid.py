import pandas as pd
import plotnine as p9


# The complement of this set is what thecrag considers a 'successful' ascent.
THECRAG_NOT_ON = set(['Attempt', 'Hang dog', 'Retreat', 'Target',
                      'Top rope with rest', 'Second with rest', 'Working'])
# My standard for a clean free ascent rules out the following. Aid solos are
# not free and ticks, top ropes and seconds without any further qualification
# are assumed to have involved weighting the rope.
NOT_ON = THECRAG_NOT_ON.union({'Tick', 'Aid solo', 'Top rope', 'Second'})


def clean_free(ascent_type):
    return ascent_type not in NOT_ON


def is_ewbanks(ascent_grade):
    try:
        int(ascent_grade)
    except ValueError:
        return False
    else:
        return True


def prepare_df():
    df = pd.read_csv('OLIVERADAMS-logbook-2020-11-12.csv')

    # Get all clean free ascents (not weighting the rope)

    df = df[df['Ascent Type'].apply(clean_free)]

    # Temporarily: just removing duplicate routes so we can just plot a pyramid
    # for clean ascents
    df = df.drop_duplicates(['Route ID'])

    # Remove non-ewbanks graded stuff.
    df = df[df['Ascent Grade'].apply(is_ewbanks)]

    df['Ewbanks Grade'] = df['Ascent Grade'].apply(lambda x: int(x))

    # Remove repeats by taking the best ascent.

    # Break stats down by pitches for more fine-grained info.

    # Separate trad from sport and bouldering

    return df


df = prepare_df()
p9.ggplot(df) + p9.geom_bar(p9.aes(x='Grade'))
