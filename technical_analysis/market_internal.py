#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import concurrent.futures
from datetime import datetime
import logging as logger
import pandas as pd

from technical_analysis import ta
import technical_analysis.column_names as ta_names

logger.basicConfig(level=logger.INFO, format='%(filename)s: %(message)s')


class MarketInternals:
    def breadth(self, df_list, lookback, from_date, to_date, fun):
        """ Calculate breadth using function for all tickers in df_list"""
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fun, df, lookback): df for df in df_list}

            for future in concurrent.futures.as_completed(futures):
                df = futures[future]
                try:
                    ticker = df['Ticker'][0]
                    res = future.result()
                    results[ticker] = res
                except Exception as exc:
                    print("Error: {0}".format(exc))

        logger.info("Processing results")
        t0 = datetime.now()

        res = MarketInternals.process_results(results, from_date, to_date,
                                              ta_names.pos_neg_columns_mapping(lookback, fun.__name__))
        logger.info("Done in {0}".format((datetime.now() - t0).total_seconds()))
        return res

    @staticmethod
    def process_results(results, from_date, to_date, columns):
        """
            results example:
            {
                'SPY':
                    {
                    'highs':['2016-12-04',2016-12-05',...]
                    'lows':['2016-11-05',2016-11-06',...]
                    },
                'AAPL':
                    {
                    'highs':['2016-12-04',2016-12-05',...]
                    'lows':['2016-11-05',2016-11-06',...]
                    }
            }
        """
        start = datetime.strptime(from_date, "%Y-%m-%d")
        end = datetime.strptime(to_date, "%Y-%m-%d")

        index = pd.date_range(start, end)  # make series from actual trading days?
        cols = [columns['pos'], columns['pos_pct'], columns['neg'], columns['neg_pct']]
        sum = pd.DataFrame(index=index, columns=cols).fillna(0.0)

        for key, value in results.items():
            for high_date in value['pos']:
                sum.set_value(high_date, columns['pos'], sum.get_value(high_date, columns['pos']) + 1)

                perc = float(sum.get_value(high_date, columns['pos'])) / float((len(results)))
                sum.set_value(high_date, columns['pos_pct'], perc * 100.0)

            for low_date in value['neg']:
                sum.set_value(low_date, columns['neg'], sum.get_value(low_date, columns['neg']) + 1)

                perc = float(sum.get_value(low_date, columns['neg'])) / float(len(results))
                sum.set_value(low_date, columns['neg_pct'], perc * 100.0)

        return sum

    # TODO: cache method?
    @staticmethod
    def hilo(df, lookback):
        ticker = df['Ticker'][0]
        highs = []
        lows = []
        results = {'pos': highs, 'neg': lows}

        t0 = datetime.now()
        for index, row in df.iterrows():
            if ta.highest(df[:index]['Close']) >= lookback:
                highs.append(row.name)
            if ta.lowest(df[:index]['Close']) >= lookback:
                lows.append(row.name)

        logger.info("{0} done in {1}".format(ticker, (datetime.now() - t0).total_seconds()))
        return results

    # TODO: cache method?
    @staticmethod
    def dma(df, lookback):
        ticker = df['Ticker'][0]

        above = []
        below = []
        results = {'pos': above, 'neg': below}

        t0 = datetime.now()
        for index, row in df.iterrows():
            if row['Close'] < row[ta_names.ma_name(lookback)]:
                below.append(row.name)
            else:
                above.append(row.name)
        logger.info("{0} done in {1}".format(ticker, (datetime.now() - t0).total_seconds()))
        return results
