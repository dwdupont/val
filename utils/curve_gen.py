



import numpy as np
import pandas as pd
from typing import Union
import json
import os 
from tqdm.auto import tqdm 



with open('data/sheet1.json', 'r') as f:
    sheet1 = json.load(f)

def get_roc_df(path_or_obj, *args, **kw):
    if isinstance(path_or_obj, pd.DataFrame):
        return path_or_obj
    elif isinstance(path_or_obj, str):
        return pd.read_excel(path_or_obj, *args, **kw)
    else:
        raise AssertionError(f"Invalid input type {type(path_or_obj)} for input argument path_or_obj")


def generate_curves(
    meanval,
    medval,
    roc_bottom:Union[pd.DataFrame, str] = "./rates_of_change_full.xlsx", 
    roc_top:Union[pd.DataFrame, str] = "./rates_of_change_full.xlsx", 
    series_type="Price", 
    json_outfn=None
):
    # TODO: 1) Put json serialization 2) pass arguments for paths to files (with defaults) 3) push this to a repo.

    roc_bottom = get_roc_df(roc_bottom, sheet_name=f"{series_type}Bot", header=None)
    roc_top = get_roc_df(roc_top, sheet_name=f"{series_type}Top", header=None)

    # exhaustive search
    best_score = np.inf
    best_values = None
    for ix1 in range(len(roc_bottom.keys())):
        # print(ix1)
        for ix2 in range(len(roc_top.keys())):
            rb = np.array(roc_bottom[ix1])
            rt = np.array(roc_top[ix2])
            r = np.append(rb, rt)
            values_normalized = np.exp(np.cumsum(np.log(r)))
            minval = meanval / values_normalized.mean()
            values = minval * values_normalized
            score = np.abs(np.median(values) - medval)
            if (score < best_score):
                best_score = score
                best_values = values 
                # print(f"best score={best_score}")
    
    if json_outfn is not None:
        with open(json_outfn, "w") as fj:
            json.dump(
                {"mean": meanval,
                "med": medval, 
                f"{series_type}": best_values.tolist()
                },
            fj)

    return best_values


# sqft => price per sqft 
# rental => price * 0.05 



def generate_for_row(row, roc_path, sheet1, zipcode) -> pd.DataFrame:
    # price 
    if np.isnan(row['MeanPrice']) or np.isnan(row['MedianPrice']):
        return None 
    price_curve = generate_curves(row['MeanPrice'], row['MedianPrice'], roc_path, roc_path, series_type='Price')
    
    # LLV
    llv_curve = price_curve * sheet1
    llv_dom_curve = llv_curve * 0.4 
    llv_sub1_curve = llv_curve * 0.3
    llv_sub2_curve = llv_curve * 0.3
    
    # SCV
    scv_curve = price_curve * sheet1
    scv_dom_curve = scv_curve * 0.4 
    scv_sub1_curve = scv_curve * 0.3
    scv_sub2_curve = scv_curve * 0.3
    
    # size 
    if np.isnan(row['MeanHouseSize']) or np.isnan(row['MedianHouseSize']):
        return None
    size_curve = generate_curves(row['MeanHouseSize'], row['MedianHouseSize'], roc_path, roc_path, series_type='Price')
    # lot size 
    if np.isnan(row['MeanLotSize']) or np.isnan(row['MedianLotSize']):
        return None 
    lot_curve = generate_curves(row['MeanLotSize'], row['MedianLotSize'], roc_path, roc_path, series_type='Lot')
    # quality 
    if np.isnan(row['MeanPricePerSqFt']) or np.isnan(row['MedianPricePerSqFt']):
        return None 
    price_sqft_curve = generate_curves(row['MeanPricePerSqFt'], row['MedianPricePerSqFt'], roc_path, roc_path, series_type='sqft')
    quality = price_sqft_curve * sheet1 
    quality_dom_curve = quality * 0.4 
    quality_sub1_curve = quality * 0.3
    quality_sub2_curve = quality * 0.3 
    
    table = pd.DataFrame(columns=['zip', 'price', 'lot_location_value', 'llv_dom', 'llv_sub_dom_1', 'llv_sub_dom_2',
                         'quality', 'quality_dom', 'quality_sub_dom_1', 'quality_sub_dom_2', 
                         'price_sqft', 'size', 'lot_size', 'scv', 'scv_dom_1', 'scv_sub_dom_1', 'scv_sub_dom_2',
                         'rental', 'rank'], 
                 index=[i for i in range(100)])
    for i in range(100):
        table.loc[i] = pd.Series({
            'zip': zipcode,
            'price': price_curve[i],
            'lot_location_value': llv_curve[i],
            'llv_dom': llv_dom_curve[i],
            'llv_sub_dom_1': llv_sub1_curve[i],
            'llv_sub_dom_2': llv_sub2_curve[i],
            'quality': quality[i],
            'quality_dom': quality_dom_curve[i],
            'quality_sub_dom_1': quality_sub1_curve[i],
            'quality_sub_dom_2': quality_sub2_curve[i],
            'price_sqft': price_sqft_curve[i],
            'size': size_curve[i],
            'lot_size': lot_curve[i],
            'scv': scv_curve[i],
            'scv_dom_1': scv_dom_curve[i],
            'scv_sub_dom_1': scv_sub1_curve[i],
            'scv_sub_dom_2': scv_sub2_curve[i],
            'rental': price_curve[i]*0.05
        })
    
    return table 

def check_nan(val):
    if type(val) == str:
        try:
            val = int(val)
            return False
        except:
            return True
    return np.isnan(val)
    
# ['State','ZipCode','TotalProperties','MedianPrice','MeanPrice','MedianHouseSize', 'MeanHouseSize','MedianPricePerSqFt','MeanPricePerSqFt','MedianLotSize', 'MeanLotSize']

def generate_csv(sheet1, roc_path='data/rates_of_change_full.xlsx', mumed_path='data/BK-Data-Manual-CA-1.24.xlsx'):
    sheet1 = np.array(sheet1)
    cols = ['State','ZipCode','TotalProperties','MedianPrice','MeanPrice','MedianHouseSize', 'MeanHouseSize','MedianPricePerSqFt','MeanPricePerSqFt','MedianLotSize', 'MeanLotSize']
    mumed = pd.read_excel(mumed_path)
    for ci in range(len(cols)):
        mumed.columns.values[ci] = cols[ci]
    skipped = 0 
    exists = set([int(float(x.replace('.csv', ''))) for x in  os.listdir('data/market-data-zipcode')])
    to_do = []
    for i, zc in enumerate(mumed['ZipCode']):
        if check_nan(zc):
            continue
        zc = int(zc)
        if zc in exists:
            continue
        to_do.append(i)
    
    print(f'Exists={len(exists)} ToDo={len(to_do)}')


    for i in tqdm(to_do):
        zc = mumed.loc[i]['ZipCode']
        save_path = f'data/market-data-zipcode/{zc}.csv'
        if f'{zc}.csv' in exists:
            continue
        if check_nan(zc):
            skipped += 1 
            continue 
        zc = int(zc)
        data = generate_for_row(mumed.loc[i], roc_path, sheet1, zc)
        if data is not None:
            # save 
            data.to_csv(save_path)
            pass 
        else:
            skipped += 1
            
    print(f'Skipped {skipped} zipcodes')
        



if __name__ == '__main__':

    generate_csv(sheet1)








