import pdb
from zigzag import *
from utils import *

class PivotList(object):
    '''
    Class that represents a list of Pivots as identified
    by the Zigzag indicator

    Class variables
    ---------------
    plist : list, Required
            List of pivots obtained using the 'peak_valley_pivots' function from Zigzag indicator
    slist : list, Derived
            Lisf of Segment objects connecting the pivot points. For obtaining these segments
            I use the function 'pivots_to_modes' implemented in the Zigzag indicator
    clist : CandleList object
            CandleList for this PivotList
    '''

    def __init__(self, plist, clist):
        self.plist = plist

        # initializing the slist class member
        modes = pivots_to_modes(plist)

        segs = []
        ix=0
        pr_ix=0
        count = 0
        type = None
        for i in modes:
            if type is None:
                type = i
                count += 1
                ix += 1
                continue
            else:
                if i == type:
                    count += 1
                else:
                    s = Segment(type=type,
                                count=count,
                                instrument=clist.instrument,
                                clist=clist.clist[pr_ix:ix])
                    type = i
                    count = 1
                    segs.append(s)
                    pr_ix = ix
            ix += 1

        self.clist = clist
        segs.append(Segment(type=type,
                            count=count,
                            instrument=clist.instrument,
                            clist=clist.clist[pr_ix:ix]))

        self.slist = segs

    def __trim_edge_segs(self, pip_th, candle_th):
        '''
        Private function to trim the edges of the 'slist'.
        By trimming I mean to remove the segments below 'pip_th' and 'candle_th'

        Parameters
        ----------
        pip_th: int
                Number of pips used as threshold to consolidate segments
                Required
        candle_th: int
                Number of candles used as threshold to consolidate segments
                Required

        Returns
        -------
        list with Segments with edge segments removed
        '''

        # removing elements at the beginning of the segment list
        nlist=self.slist
        for s in self.slist:
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist=nlist[1:]

        pdb.set_trace()
        # removing elements at the end of the segment list
        for s in reversed(nlist):
            if s.diff > pip_th or s.count > candle_th:
                break
            else:
                nlist.pop()

        return nlist


    def get_major_segment(self, pip_th=200, candle_th=5):
        '''
        Function to reduce segment complexity and
        to merge the minor trend to the major trend.
        For example:
        We have a segment like the following:
        1,1,1-1,-1,1,1. After running this function we
        will get 1,1,1,1,1,1,1

        Parameters
        ----------
        pip_th: int
                Number of pips used as threshold to consolidate segments
                Default: 200
        candle_th: int
                Number of candles used as threshold to consolidate segments
                Default: 5

        Returns
        -------
        It will set the self.slist class member to the reduced Segment list
        '''

        slist=[s.calc_diff() for s in self.slist]

        nlist=self.__trim_edge_segs(pip_th,candle_th)

        pdb.set_trace()
        count_retraced=0
        nslist=[]

        """
        # iterate over Segment list from most recent to oldest
        for s in reversed(slist):
            print("type:{0}; diff:{1}; count:{2}\n".format(s.type,s.diff,s.count))
            if s.diff>pip_th or s.count>candle_th:
                if count_retraced==1:
                    p_s = nslist[-1]
                    p_s.merge(s)
                    nslist[-1] = p_s
                else:
                    nslist.append(s)
                count_retraced=0
            else:
                if len(nslist)>0:
                    count_retraced+=1
                    p_s=nslist[-1]
                    p_s.merge(s)
                    nslist[-1]=p_s
                else:
                    # it is the first segment in the slist
                    nslist.append(s)
        """
        ix=0
        sel_ixs=[]
        for s in reversed(slist):
            print("type:{0}; diff:{1}; count:{2}".format(s.type, s.diff, s.count))
            if s.diff < pip_th or s.count < candle_th:
                sel_ixs.append(ix)
            ix+=1
        pdb.set_trace()
        print("h")

class Segment(object):
    '''
    Class containing a Segment object identified using the function 'get_segment_list' from the PivotList

    Class variables
    ---------------
    type : int, Required
           1 or -1
    count : int, Required
            Number of entities of 'type'
    instrument : str, Required
                 Pair
    clist : CandleList, Required
            CandleList with list of candles for this Segment
    diff : int, Optional
           Diff in number of pips between the first and the last candles in this segment
    '''

    def __init__(self, type, count, instrument, clist, diff=None):
        self.type = type
        self.count = count
        self.instrument = instrument
        self.clist = clist
        self.diff = diff

    def merge(self, s):
        '''
        Function to merge self to s. The merge will be done by
        concatenating s.clist to self.clist and increasing self.count to
        self.count+s.count

        Parameters
        ----------
        s : Segment object to be merge

        Returns
        -------
        Nothing
        '''

        self.clist=s.clist+self.clist
        self.count=len(self.clist)

    def calc_diff(self, part="openAsk"):
        '''
        Function to calculate the absolute difference in
        number of pips between the first and the last candles
        of this segment

        Parameters
        ---------
        part : What part of the candles used for calculating the difference.
               Default: 'openAsk'

        Returns
        -------
        It will set the 'diff' class member attribute
        '''

        # calculate the diff in pips between the last and first candles of this segment
        diff = abs(getattr(self.clist[-1],part) - getattr(self.clist[0],part))
        diff_pips = float(calculate_pips(self.instrument, diff))

        self.diff=diff_pips

        return self

    def __repr__(self):
        return "Segment"

    def __str__(self):
        out_str = ""
        for attr, value in self.__dict__.items():
            out_str += "%s:%s " % (attr, value)
        return out_str


'''
calc_angles()      
{
    angles = []

pdb.set_trace()
modes = pivots_to_modes(pivots)
y_vals = yarr[np.logical_or(pivots == 1, pivots == -1)]
x_vals = xarr[np.logical_or(pivots == 1, pivots == -1)]
slopes = []
x0 = None
y0 = None
for x, y in zip(x_vals, y_vals):
    if
x0 is None and y0 is None:
x0 = x
y0 = y
else:
slope = (y0 - y) / (x0 - x)
slopes.append(slope)
x0 = x
y0 = y

# calculate angle between segments (see documentation for formula)
m1 = None
for m2 in slopes:
    if
m1 is None: \
    m1 = m2
continue
tan_sigma = abs((m2 - m1) / (1 + m2 * m1))
angle = math.degrees(math.atan(tan_sigma))
angles.append(angle)
m1 = m2

}
'''