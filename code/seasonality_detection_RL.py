## Seasonality detection code usnig linear regression method

import pandas as pd
import numpy as np
# import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')
from datetime import datetime


shutdown_flag= True

if shutdown_flag:
    import restart_shutdown



threshold = 0.001
ma_window=4

start_time = datetime.now()
######################################################################################################################
print('SEANONALITY DETECTION ON ACTIVITY DATA')
print('#########################################################')


print('Reading input file')
df=pd.read_csv('../data/all_activity_normal.csv') # Read the data

######################################################################################################################
## Clean up
######################################################################################################################

# Drop the "unnecessary" columns (for now)

df.drop(columns=['Unnamed: 0','Country', 'Currency', 'Advertiser_URL',
                'BC_ID','BusinessCategory', 'Primary_BSC_ID', 'Primary_BusinessSubCategory',
                'Secondary_BSC_Count','Secondary_BSC_IDs','Seconardy_BSCs','BusinessSpecialtyID',
                'CTL', 'CPL','CPC', 'CTR',
                'BusinessSpecialty'], axis=1, inplace=True)
df.reset_index(inplace=True,drop=True)


# Dealing with Offer, Finance Product, idOffer (There are only a few of them?)

missing_offer_ids=df[df.Offer_Name.isna()]['idadvertiser_master'].unique()

# Check to see if their are missing at the exact same locations:

df=df[~df.idadvertiser_master.isin(missing_offer_ids)]
df.reset_index(inplace=True,drop=True)

# Create a duration column. For missing values, one option is to replace with the average 
# campaign duration of a given advertiser--> Local!
# However we're not sure why the cycle is missing an end date. Is that churn?
df['Cycle_Started']=pd.to_datetime(df.Cycle_Started, format='%Y-%m-%d',  errors='ignore')
df['Cycle_Ended']=pd.to_datetime(df.Cycle_Ended, format='%Y-%m-%d',  errors='ignore')

my_index=df[df['Cycle_Ended'] < df['Cycle_Started']].index

temp=df.loc[my_index, 'Cycle_Ended']

df.loc[my_index, 'Cycle_Ended'] = df.loc[my_index, 'Cycle_Started']

df.loc[my_index, 'Cycle_Started']=temp


df.reset_index(inplace=True,drop=True)
df['cycle_duration']=pd.to_timedelta(df['Cycle_Ended']-df['Cycle_Started']).astype('timedelta64[D]')

df.reset_index(inplace=True,drop=True)

# Get rid of the campaigns with zero budget and those starting at the end of the year.
df=df[~(df.campaign_budget==0)]
df=df[~(df.campaign_budget < 1)]

df=df[~(df.Cycle_Started==pd.to_datetime('2018-12-31 00:00:00'))]

df.reset_index(inplace=True,drop=True)

ids=df[pd.isnull(df.Cycle_Started)]['idadvertiser_master'].unique()

df=df[~(df.idadvertiser_master.isin(ids))]

df.reset_index(inplace=True,drop=True)

duration_mode=df.cycle_duration.mode() # Mode is 30. Let's impute the duration with this

#my_index=df[pd.isnull(df.cycle_duration)].index
#df.loc[my_index, 'cycle_duration']=duration_mode

df['cycle_duration'].fillna(duration_mode[0], inplace=True)

# Now reconstruct the end dates
my_index=df[pd.isnull(df.Cycle_Ended)].index
df.loc[my_index, 'Cycle_Ended']=df.loc[my_index, 'Cycle_Started']+pd.to_timedelta(str(duration_mode[0])+'D')
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################

# DETECTION HAPPENS HERE

###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
###############################################################################################################
# Sort my master_adv_id and cycle start date then reset the main index.
# It's possible to do this with adv_id
#df.sort_values(by=['idadvertiser_master','Cycle_Started'])
df.reset_index(drop=True, inplace=True)
# Trim down the dataframe
temp=df[['idadvertiser_master','idadvertiser','Cycle_Started','Cycle_Ended','cycle_duration']]
# Find unique ids 
adv_ids=temp.idadvertiser_master.unique()

# Create additional columns
temp['delta']=0.0
temp['summation']=0.0

from sklearn.linear_model import LinearRegression
mdl=LinearRegression(n_jobs=4)



#seasonal=[]
#period=[]

def ma(array, window=1):  # Moving average
    return np.convolve(array[0], np.ones((1,window))[0]/window, mode='same').reshape(1,array.shape[1])


# Loop over ids
for idd in adv_ids:
    print('Processing advertiser ID=', idd)
    subset = temp[temp.idadvertiser_master==idd]
    subset.sort_values(by=['idadvertiser_master','Cycle_Started'],inplace=True)
    subset.reset_index(drop=True, inplace=True)
    
    if subset.shape[0]< ma_window:
        f=open('../data/seasonal.txt', 'a+')
        f.write(str(0)+'\n' )
        f.close()

        f=open('../data/periods.txt', 'a+')
        f.write(str(0)+'\n' )
        f.close()
    else:
    
        # Separating start and end
        start = subset.Cycle_Started
        end = subset.Cycle_Ended

        end_shift = end
        end_shift[1:]=end[0:-1]

        delta = start-end_shift
        subset['delta']=0.0
        for i in range(0,subset.shape[0]):
            subset.loc[i,'delta']=delta.iloc[i].days

        subset.loc[0,'delta']=0

        #subset['delta']=delta
        subset['summation']=subset['cycle_duration']+subset['delta']

        # Create the time series

        time_series= np.ones((1,int(subset['summation'].sum())))
        pivot = 0
        for i in range(0,subset.shape[0]):
            if subset.loc[i,'delta'] > 0:
                start_index=int(subset.loc[0:i,'summation'].sum() )
                end_index=start_index+int( subset.loc[i,'delta'] )
                time_series[0][start_index:end_index]=0
                pivot=i
        

        time_series=time_series-ma(time_series, window=ma_window) # Remove the trend

        # Next largest power of 2        
        nfft=1<<(time_series.shape[1]-1).bit_length()

        y=np.fft.fft(time_series, n=nfft)
        y=abs(y**2)
        y=(y-y.min())
        y=y/y.max()

        freq_ts=(np.linspace(0,nfft/2,int(nfft/2)) *1/float(nfft))
        freq_ts=1/freq_ts
        freq_ts=freq_ts[1:]
        freq_ts=freq_ts.reshape(-1,1)
        #period_ts=freq_ts[::-1]
        #period_ts=period_ts.reshape(1,-1).T
        
        y=y[0][1:int(nfft/2)].reshape(1,-1).T
        
        if time_series.shape == (1,1):
            coeff=0.0
        else:
            mdl.fit(freq_ts, y)
            coeff=mdl.coef_

        if (np.abs(coeff) > threshold):
            f=open('../data/seasonal.txt', 'a+')
            f.write(str(1)+'\n')
            f.close()

            f=open('../data/periods.txt', 'a+')
            f.write(str( freq_ts[ np.argmax(y) ] )+'\n' )
            f.close()

        else:
            f=open('../data/seasonal.txt', 'a+')
            f.write(str(0)+'\n' )
            f.close()

            f=open('../data/periods.txt', 'a+')
            f.write(str(0)+'\n' )
            f.close()
               
###############################################################################################################
print('#########################################################')
print('DONE!')
end_time = datetime.now()
print('Execution time: {}'.format(end_time - start_time))

if shutdown_flag:
    restart_shutdown.shutdown(10)
###############################################################################################################
