import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import seaborn as sns
import concurrent.futures

df=pd.read_csv("../data/keri_churn_data_tidy.csv")
df.sort_values(by=['idadvertiser_varchar'], inplace=True)
df['time_stamp']=df.csr_year_varchar*100+df.csr_month_varchar

ids=df.idadvertiser_varchar.unique()
num_col=['campaign_budget_varchar', 'spend_varchar', 'clicks_varchar',
       'impressions_varchar', 'calls_varchar', 'qualified_calls_varchar',
       'emails_varchar', 'cvt_varchar', 'qualified_web_events_varchar',
       'advtrans_varchar']

def time_plot(temp, col_names, address):
    for col in col_names:
        plt.figure(figsize=(8,5))
        plt.cla()
        plt.plot(np.arange(0,temp.time_stamp.shape[0]), temp[col], LineWidth=4.0);
        plt.xlabel('Months', fontsize=18)
    #plt.yticks(rotation=45)
        plt.tick_params(direction='in', length=10, width=5, colors='k',
                   grid_color='k', grid_alpha=1, labelsize=20)
        ax = plt.gca()
        tag=temp.advertiser_name_varchar.iloc[0]+"-statrting: "+ \
        str(temp.csr_month_varchar.iloc[0])+"-"+str(temp.csr_year_varchar.iloc[0])
        plt.text(0.01,0.9, tag, transform=ax.transAxes, fontsize=15)
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        
        
        save_to=address+"/"+col+".png"
        plt.savefig(save_to)
        plt.close()

#def get_adv_plots( my_tuple=(ids, data_frame) ):
def get_adv_plots( my_tuple=(list, pd.DataFrame) ):
    ad_id=my_tuple[0]
    df=my_tuple[1]
    for ad_id in ids:
        temp=df[df.idadvertiser_varchar == ad_id].sort_values(by=['time_stamp'])
        address ='../outputs/advertisers/case_id_'+str(ad_id)
        #print(address)
        os.makedirs(address, exist_ok=True)
        time_plot(temp, num_col, address)

num_process=4
#df.shape
my_mod=np.floor_divide(df.shape[0],num_process)

indecies=[]
for i in range(0,num_process-1):
    indecies.append( (i*my_mod, (i+1)*my_mod) )


with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
    executor.map(get_adv_plots, [(ids, df.iloc[indecies[0][0]:indecies[0][1],:]), 
                          (ids, df.iloc[indecies[1][0]:indecies[1][1],:]), 
                          (ids, df.iloc[indecies[2][0]:indecies[2][1],:]),
                          (ids, df.iloc[indecies[2][1]:,:])])