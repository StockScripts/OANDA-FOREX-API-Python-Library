from oanda_api import OandaAPI
from configparser import ConfigParser
from TradeJournal.trade import Trade
from Pattern.counter import Counter

from utils import *
import pdb
import pandas as pd
import datetime
import re

class TradeBot(object):
    '''
    This class represents an automatic Trading bot

    Class variables
    ---------------
    start: datetime, Required
           Datetime that this Bot will start operating. i.e. 20-03-2017 08:20:00s
    end: datetime, Required
         Datetime that this Bot will end operating. i.e. 20-03-2020 08:20:00s
    pair: str, Required
          Currency pair used in the trade. i.e. AUD_USD
    timeframe: str, Required
               Timeframe used for the trade. Possible values are: D,H12,H10,H8,H4
    settingf : str, Optional
               Path to *.ini file with settings
    '''
    def __init__(self, start, end, pair, timeframe, settingf, settings=None):
        self.start = start
        self.end = end
        self.pair = pair
        self.timeframe = timeframe
        self.settingf = settingf
        if self.settingf is not None:
            # parse settings file (in .ini file)
            parser = ConfigParser()
            parser.read(settingf)
            self.settings = parser
        else:
            self.settings = settings


    def run(self):
        '''
        This function will run the Bot from start to end
        one candle at a time
        '''
        oanda = OandaAPI(instrument=self.pair,
                         granularity=self.timeframe,
                         settingf=self.settingf)
        delta = None
        nhours = None
        if self.timeframe == "D":
            nhours = 24
            delta = datetime.timedelta(hours=24)
        else:
            p1 = re.compile('^H')
            m1 = p1.match(self.timeframe)
            if m1:
                nhours = int(self.timeframe.replace('H', ''))
                delta = datetime.timedelta(hours=int(nhours))

        startO = pd.datetime.strptime(self.start, '%Y-%m-%d %H:%M:%S')
        endO = pd.datetime.strptime(self.end, '%Y-%m-%d %H:%M:%S')

        while startO <= endO:
            oanda.run(start=startO.isoformat(),
                      count=1)

            candle_list = oanda.fetch_candleset()
            startO = startO+delta

    def __calc_diff(self, df_loc):

        prev_price = None
        prev_row = None
        prev_ix = None
        tog_seen = False
        for index, row in df_loc.iterrows():
            if prev_price is None:
                prev_price = float(row['price'])
                prev_row = row
                prev_ix = index
            else:
                diff = round(float(row['price']) - prev_price, 4)
                if diff < 3 * increment_price:
                    # if diff <= 0.035:
                    tog_seen = True
                    if row['bounces'] <= prev_row['bounces'] and row['tot_scores'] < prev_row['tot_scores']:
                        # remove current row
                        df_loc.drop(index, inplace=True)
                    elif row['bounces'] >= prev_row['bounces'] and row['tot_scores'] > prev_row['tot_scores']:
                        # remove previous row
                        df_loc.drop(prev_ix, inplace=True)
                        prev_price = float(row['price'])
                        prev_row = row
                        prev_ix = index
                    elif row['bounces'] <= prev_row['bounces'] and row['tot_scores'] > prev_row['tot_scores']:
                        # remove previous row as scores in current takes precedence
                        df_loc.drop(prev_ix, inplace=True)
                        prev_price = float(row['price'])
                        prev_row = row
                        prev_ix = index
                    elif row['bounces'] >= prev_row['bounces'] and row['tot_scores'] < prev_row['tot_scores']:
                        # remove current row as scores in current takes precedence
                        df_loc.drop(index, inplace=True)
                    elif row['bounces'] == prev_row['bounces'] and row['tot_scores'] == prev_row['tot_scores']:
                        # exactly same quality for row and prev_row
                        # remove current arbitrarily
                        df_loc.drop(index, inplace=True)
                else:
                    prev_price = float(row['price'])
                    prev_row = row
                    prev_ix = index
        return df_loc, tog_seen

    def calc_SR(self):
        '''
        Function to calculate S/R lines
        :return:
        '''

        if self.settings.getboolean('general', 'debug') is True:
            print("[DEBUG] Running calc_SR")

        ll, ul = self.settings.get('tradebot', self.pair).split(",")

        prices = []
        bounces = []  # contains the number of pivots per price level
        score_per_bounce = []
        tot_scores = []
        # the increment of price in number of pips is double the hr_extension
        prev_p = None
        p = float(ll)
        while p <= float(ul):
            if self.settings.getboolean('general', 'debug') is True:
                print("Processing S/R at {0}".format(round(p, 4)))
                # each of 'p' will become a S/R that will be tested for bounces
                # set entry to price+30pips
            entry = add_pips2price(self.pair, p, 30)
            # set S/L to price-30pips
            SL = substract_pips2price(self.pair, p, 30)
            pdb.set_trace()
            t = Trade(
                id='{0}.detect_sr.{1}'.format(self.pair, round(p, 5)),
                start=self.start,
                pair=self.pair,
                timeframe='D',
                type='short',
                entry=entry,
                SR=p,
                SL=SL,
                RR=1.5,
                strat='counter_b1',
                settingf=self.settingf)

            c = Counter(
                trade=t,
                init_feats=True,
                settingf=self.settingf
            )

            ratio = None
            if len(c.pivots.plist) == 0:
                ratio = 0
                mean_pivot = 0
            else:
                mean_pivot = round(c.score_pivot, 2)

            prices.append(round(p, 5))
            bounces.append(len(c.pivots.plist))
            tot_scores.append(c.total_score)
            score_per_bounce.append(mean_pivot)
            p = add_pips2price(args.instrument, p, 60)
            if prev_p is None:
                prev_p = p
            else:
                increment_price = round(p - prev_p, 5)
                prev_p = p

        data = {'price': prices,
                'bounces': bounces,
                'scores': score_per_bounce,
                'tot_scores': tot_scores}

        df = pd.DataFrame(data=data)
        ### establishing bounces threshold as the args.th quantile
        # selecting only rows with at least one pivot and tot_score>0, so threshold selection considers only these rows
        # and selection is not biased when range of prices is wide
        dfgt1 = df.loc[(df['bounces'] > 0)]
        dfgt2 = df.loc[(df['tot_scores'] > 0)]
        bounce_th = dfgt1.bounces.quantile(self.settings.getfloat('tradebot', 'th'))
        score_th = dfgt2.tot_scores.quantile(self.settings.getfloat('tradebot', 'th'))
        if self.settings.getboolean('general', 'debug') is True:
            print("[DEBUG] Selected number of pivot threshold: {0}".format(bounce_th))
            print("[DEBUG] Selected tot score threshold: {0}".format(score_th))

        # selecting records over threshold
        dfsel = df.loc[(df['bounces'] > bounce_th) | (df['tot_scores'] > score_th)]
