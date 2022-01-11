import altair as alt
import numpy as np
import pandas as pd
from scipy import stats
from altair_saver import save
alt.renderers.enable('altair_viewer')


df = pd.read_excel(r'..\data\IsabellaWAT_DataPrep.xlsx',
                   usecols = 'B:H',
                   skiprows = 2,
                   sheet_name = 'DateToJulForecastErr 1976-2020'
                  ).dropna()

df = df.set_index('Year')
df = df.stack()
df.index.names = ['year','month']
df.name = 'volume'
df = df.reset_index()

charts_z = []
charts_yeo =[]
charts_bar = []


for name, group in df.groupby('month'):

    c = alt.Chart(group).transform_joinaggregate(
        total = 'count(volume)'
    ).transform_calculate(
        pct = '1/datum.total'
    ).mark_bar().encode(
        x = alt.X('volume:Q', bin=True),
        y = alt.Y('sum(pct):Q', axis = alt.Axis(format = '%'))
    ).properties(title = name)
    charts_bar.append(c)


    group.loc[:, 'boxcox'], lam = stats.boxcox(group.volume)

    c = alt.Chart(group).transform_joinaggregate(
        total = 'count(boxcox)'
    ).transform_calculate(
        pct = '1/datum.total'
    ).mark_bar().encode(
        x = alt.X('boxcox:Q', bin=True),
        y = alt.Y('sum(pct):Q', axis = alt.Axis(format = '%'))
    ).properties(title = name)
    charts_yeo.append(c)

    group.loc[:,'z_score'] = (group.boxcox- group.boxcox.mean())/group.boxcox.std()

    c = alt.Chart(group).transform_density(density = 'z_score', 
                                        # groupby = ['month'],
                                        as_=['z_score', 'density'],
                                        extent= [-4,4],
                                        bandwidth=0.3
                                        ).mark_area().encode(
    x = 'z_score:Q',
    y = 'density:Q',
    # color = alt.Color('month:N', scale = alt.Scale(domain = ['Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'], range = ['blue','green','red','black','magenta','cyan']))

    ).properties(title = name)
    charts_z.append(c)


b = (charts_yeo[1] | charts_yeo[4] | charts_yeo[0]) & (charts_yeo[5] | charts_yeo[3] | charts_yeo[2])
save(b, r'..\Figures\volume_normalized_boxcox_bar.png', method = 'selenium', scale_factor = 3)

d = (charts_z[1] | charts_z[4] | charts_z[0]) & (charts_z[5] | charts_z[3] | charts_z[2])
save(d, r'..\Figures\volume_normalized_boxcox_density.png', method = 'selenium', scale_factor = 3)

e = (charts_bar[1] | charts_bar[4] | charts_bar[0]) & (charts_bar[5] | charts_bar[3] | charts_bar[2])
save(e, r'..\Figures\volume_normalized_error_bar.png', method = 'selenium', scale_factor = 3)


import matplotlib.pyplot as plt

for name, group in df.groupby('month'):


    group.loc[:, 'boxcox'] = stats.boxcox(group.volume)[0]

    fig = plt.figure()
    fig.suptitle(name)
    ax1 = fig.add_subplot(211)
    x = stats.loggamma.rvs(5, size=500) + 5
    prob = stats.probplot(group.volume, dist=stats.norm, plot=ax1)
    ax1.set_xlabel('')
    ax1.set_title('Probplot against normal distribution')

    ax2 = fig.add_subplot(212)
    xt, lmbda = stats.yeojohnson(x)
    prob = stats.probplot(group.boxcox, dist=stats.norm, plot=ax2)
    ax2.set_title('Probplot after Yeo-Johnson transformation')
    plt.subplots_adjust(top=0.88,
                        bottom=0.11,
                        left=0.13,
                        right=0.9,
                        hspace=0.305,
                        wspace=0.2)
    
    plt.savefig(rf'..\Figures\{name}_volume_boxcox_probplot.png', dpi=600)
    plt.close()


a = {}
b = {}
c = {}

for name, group in df.groupby('month'):

    group.loc[:, 'boxcox'], lam = stats.boxcox(group.volume)

    a.update({name:lam})
    b.update({name:[
                    stats.kurtosis(group.boxcox), 
                    stats.skew(group.boxcox),
                    group.boxcox.var(),
                    group.boxcox.mean(),
                    stats.kurtosis(group.volume), 
                    stats.skew(group.volume),
                    group.volume.var(),
                    group.volume.mean()                    
                    ]})

idx = pd.MultiIndex.from_product([['boxcox','Date2Volume'],['kurtosios','skew','variance','mean']], names = ['dataset','statistic'])

stats = pd.DataFrame.from_dict(b, orient='index', columns = idx)

print(stats.to_markdown())