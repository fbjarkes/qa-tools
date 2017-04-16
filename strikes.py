#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, WeekdayLocator, DayLocator, MONDAY
from matplotlib.finance import candlestick_ohlc

from technical_analysis import ta
import pandas as pd


from dataprovider.dataprovider import CachedDataProvider


BUCKET_SIZE = 0.5

def usage():
    print("./strikes.py --strike-size 0.5 --direction short --round up")


def find_nearest_strike(number,strike_size):
    n = int(number)
    while (n < number):
        n += strike_size
    return n

def find_nearest_itm_strike(number,strike_size):
    n = int(number)+1
    while (n > number):
        n -= strike_size
    return n

def calculate(diff):
    if diff < 0:
        s = find_nearest_itm_strike(diff, BUCKET_SIZE)
    else:
        s = find_nearest_strike(diff, BUCKET_SIZE)
    return s

def get_stats(data):
    neg = pos = avg = avg_ceiling = 0.0
    high_open_avg_bull = 0.0
    high_open_avg_bear = 0.0
    close_list = []
    stats = {}

    bull = []
    bear = []

    for index, row in data.iterrows():
        close_list.append(row['Close'])
        diff = float(row["Close"]) - float(row["Open"])
        ho_diff = float(row["High"]) - float(row["Open"])
        if diff <= 0.0:
            # Bear bar
            neg += 1
            high_open_avg_bear += ho_diff
            bear.append(ho_diff)
        else:
            # Bull bar
            avg += diff
            avg_ceiling += min(diff,1)
            pos += 1
            high_open_avg_bull += ho_diff
            bull.append(ho_diff)

    #tmp = pd.concat([pd.DataFrame(bull), pd.DataFrame(bear)], ignore_index=True, axis=1)

    tmp1 = pd.DataFrame({'bear':bear})
    print(tmp1.describe())

    stats['o2c'] = {
        "neg": neg, "pos":pos,
        "avg":avg/float(len(data)),
        "avg_ceil": avg_ceiling/float(len(data)),
        "ho_avg_bull": high_open_avg_bull/pos,
        "ho_avg_bear": high_open_avg_bear/neg
    }

    pos2 = 0
    neg2 = 0
    for i in range(0,len(close_list)-1):
        close_current_week = close_list[i+1]
        close_last_week = close_list[i]

        if float(close_current_week) - float(close_last_week) <= 0.0:
            neg2 += 1
        else:
            pos2 += 1

    stats['c2c'] = {"neg": neg2, "pos": pos2}
    print(stats)
    return stats


def calculate_bucket(data):
    itm_strikes = []
    otm_strikes = []
    o2c_strikes = []

    for week in data:
        closest_otm_strike = find_nearest_strike(week['Open'], BUCKET_SIZE)
        closest_itm_strike = find_nearest_itm_strike(week['Open'], BUCKET_SIZE)

        o2c_strikes.append(calculate(week['Close']-week['Open']))
        itm_strikes.append(calculate(week['Close'] - closest_itm_strike))
        otm_strikes.append(calculate(week['Close'] - closest_otm_strike))
        #print(itm_strikes)
        #print(otm_strikes)

    #df = pd.DataFrame(o2c_strikes)
    #df = pd.DataFrame(itm_strikes)

    df = pd.DataFrame({'o2c': o2c_strikes, 'itm': itm_strikes, 'otm': otm_strikes}, columns=['o2c','itm','otm'])
    print(df.describe())
    df.plot.hist(alpha=0.5,bins=250)
    plt.show()


    #plt.show(block=True)


def test_get_stats():
    #df = pd.DataFrame({"Open": [], "High": [], "Low": [], "Close": []})

    df = pd.DataFrame(pd.DataFrame({"Open": 10.0, "High": 11.0, "Low": 9.0, "Close": 10.5}, index=[0])) # W1
    df = df.append(pd.DataFrame({"Open": 11.0, "High": 12.0, "Low": 10.0, "Close": 11.5}, index=[0])) # W2
    df = df.append(pd.DataFrame({"Open": 11.0, "High": 11.5, "Low": 9.0, "Close": 10.6}, index=[0]))  # W3

    n = len(df)
    stats = get_stats(df)

    assert stats['o2c']['neg'] == 1
    assert stats['o2c']['pos'] == 2
    assert stats['c2c']['pos'] == 1
    assert stats['c2c']['neg'] == 1

    # print("Weekly O2C:")
    # print("Neg: %d/%d = %f" % (stats['o2c']['neg'], n, stats['o2c']['neg'] / float(n)))
    # print("Pos: %d/%d = %f" % (stats['o2c']['pos'], n, stats['o2c']['pos'] / float(n)))
    #
    # print("Weekly C2C:")
    # print(
    #     "Neg: %d/%d = %f" % (stats['c2c']['neg'], n - 1, stats['c2c']['neg'] / float(n - 1)))
    # print(
    #     "Pos: %d/%d = %f" % (stats['c2c']['pos'], n - 1, stats['c2c']['pos'] / float(n - 1)))

def test_strikes():
    assert 22 == find_nearest_strike(21.6, 0.5)
    assert 21.5 == find_nearest_strike(21.4, 0.5)

    assert 21 == find_nearest_itm_strike(21.4, 0.5)
    assert 21.5 == find_nearest_itm_strike(21.9, 0.5)

    assert -0.5 == find_nearest_itm_strike(-0.1, 0.5)
    assert -0.5 == find_nearest_itm_strike(-0.5, 0.5)
    assert 0.5 == find_nearest_strike(0.1, 0.5)
    assert 1.5 == find_nearest_strike(1.1, 0.5)

def plot_data(datas):
    """
    plt.figure(1)
plt.subplot(2,2,1)
df.A.plot() #no need to specify for first axis
plt.subplot(2,2,2)
df.B.plot(ax=plt.gca())
plt.subplot(2,2,3)
df.C.plot(ax=plt.gca())
    """
    plt.figure(1)

    #fig, ax = plt.subplots()
    #fig.subplots_adjust(bottom=0.2)


    for i, data in enumerate(datas):
        plt.subplot(len(datas), 1, i+1)
        #print(i)
        data.plot()

    plt.show()


    # plt.show(block=True)
    # if data.index[-1] - data.index[0] < pd.Timedelta('730 days'):
    #     weekFormatter = DateFormatter('%b %d')  # e.g., Jan 12
    #     ax.xaxis.set_major_locator(mondays)
    #     ax.xaxis.set_minor_locator(alldays)
    # else:
    #     weekFormatter = DateFormatter('%b %d, %Y')
    # ax.xaxis.set_major_formatter(weekFormatter)
    #
    # ax.grid(True)
    #
    # # Create the candelstick chart
    # candlestick_ohlc(ax, list(
    #     zip(list(date2num(plotdat.index.tolist())), plotdat["Open"].tolist(), plotdat["High"].tolist(),
    #         plotdat["Low"].tolist(), plotdat["Close"].tolist())),
    #                  colorup="black", colordown="red", width=stick * .4)




def difference(data):
    return (data['Close'].shift(-1) - data['Close']).dropna()

def test_cumulative_diff():
    #2016 - 12 - 12 25.610001 26.870001 25.450001 26.000000
    #2016 - 12 - 19 24.150000 25.340000 23.740000 25.330000
    #2016 - 12 - 27 25.510000 25.790001 23.620001 24.110001

    df = pd.DataFrame(pd.DataFrame({"Open": 1, "High": 1, "Low": 1, "Close": 10.0}, index=[0]))  # W1
    df = df.append(pd.DataFrame({"Open": 1, "High": 1, "Low": 1, "Close": 9.0}, index=[0]))  # W2
    df = df.append(pd.DataFrame({"Open": 1, "High":1, "Low": 1, "Close": 8.0}, index=[0]))  # W3
    df = df.append(pd.DataFrame({"Open": 1, "High": 1, "Low": 1, "Close": 8.5}, index=[0]))  # W3

    # -1
    # -1
    # 0.5
    res = difference(df)
    assert res.iloc[0] == -1
    assert res.iloc[1] == -1
    assert res.iloc[2] == 0.5


    res = res.cumsum()
    assert res.iloc[1] == -2
    assert res.iloc[2] == -1.5


if __name__ == '__main__':
    """
    Specific qa_tools for VXX

    Observations:
        1. Friday close to next fridays close seems a little bit better than O2C (61% instead of 60% wins)
        2. Average loss is probably closer to 0,3 ($30) and not always max loss
        3. It seems like edge is far less for selling nearest ITM.
           The mean of all ITM strikes is 0,26 vs -0.27 for nearest OTM, i.e. nearest ITM option is more likely to close ITM than OTM!
        4. Using trendfiler, e.g. 50DMA slope, 200DMA, etc. increases edge slightly
        5. The average "tail" i.e. high-open is:
            - bull bars: avg=?, median=?
            - bear bars: avg=?, median=?

    """

    #test_strikes()
    #test_get_stats()
    #test_cumulative_diff()

    #buckets = calculate_bucket([{"open":21.6,"close":21.5},{"open":22.1, "close":21.8}, {"open":25, "close":24.8}, {"open":25, "close":27.5}]
    #data = get_data("/Users/fbjarkes/Dropbox/tickdata_weekly/NYSF_VXX.txt")

    provider = CachedDataProvider()
    data = provider.get_data("VXX","2010-01-01","2016-12-31",timeframe="week", provider='yahoo')
    spy_daily = provider.get_data("SPY", "2010-01-01", "2016-12-31", provider='yahoo')
    spy_daily = ta.add_ma(spy_daily, 200)
    spy_daily = ta.add_ma_slope(spy_daily, 200)
    spy_daily = ta.add_ma_slope(spy_daily, 50)

    #spy_daily.plot()
    #plt.show()

    converted = []
    filtered = pd.DataFrame()
    for index, row in data.iterrows():
        #print(index," Open=",row['Open'], " Close=",row["Close"])
        #print("index=",index.isoformat())
        if spy_daily.loc[index][ta.ma_slope_name(200)] <= 0:
            #print(row.name.date().__str__())
            pass
        else:
            converted.append({"Open":float(row["Open"]), "Close": float(row["Close"])})
            filtered = filtered.append(row)
            #print("%s: %f to %f => O2C=%f" % (index.isoformat(),row["Open"],row["Close"],(row["Close"]-row["Open"])))

    # TODO: Fix this:
    stats = get_stats(data)
    print("Original:")
    print("Weekly O2C:")
    print("Neg: %d/%d = %f" % (stats['o2c']['neg'], len(data), stats['o2c']['neg']/float(len(data))))
    print("Pos: %d/%d = %f" % (stats['o2c']['pos'], len(data), stats['o2c']['pos']/float(len(data))))
    print("Avg: %f" % (stats['o2c']['avg']))
    print("Avg positive (max $1): %f" % (stats['o2c']['avg_ceil'])) # This assumes an OTM strike is sold from official VXX opening price
    print("High-Open bull avg: %f" % (stats['o2c']['ho_avg_bull']))
    print("High-Open bear avg: %f" % (stats['o2c']['ho_avg_bear']))
    print("")
    print("Weekly C2C:")
    print("Neg: %d/%d = %f" % (stats['c2c']['neg'], len(data)-1, stats['c2c']['neg'] / float(len(data)-1)))
    print("Pos: %d/%d = %f" % (stats['c2c']['pos'], len(data)-1, stats['c2c']['pos'] / float(len(data)-1)))
    print("")
    print("")
    print("Filtered:")
    stats = get_stats(filtered)
    print("Weekly O2C:")
    print("Neg: %d/%d = %f" % (stats['o2c']['neg'], len(converted), stats['o2c']['neg'] / float(len(converted))))
    print("Pos: %d/%d = %f" % (stats['o2c']['pos'], len(converted), stats['o2c']['pos'] / float(len(converted))))
    print("Avg: %f" % (stats['o2c']['avg']))
    print("Avg positive (max $1): %f" % (stats['o2c']['avg_ceil']))  # This assumes an OTM strike is sold from official VXX opening price
    print("")
    print("Weekly C2C:")
    print("Neg: %d/%d = %f" % (stats['c2c']['neg'], len(converted) - 1, stats['c2c']['neg'] / float(len(converted) - 1)))
    print("Pos: %d/%d = %f" % (stats['c2c']['pos'], len(converted) - 1, stats['c2c']['pos'] / float(len(converted) - 1)))
    # calculate_bucket(converted)

    #diff = difference(data)
    #plot_data([diff, diff.cumsum(), spy['Close']])

