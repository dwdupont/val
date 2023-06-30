from pydantic import BaseModel 
from typing import Optional, List



class RankValue(BaseModel):
    rank: Optional[int]
    value: Optional[float]

class HomeRank(BaseModel):
    zipcode: int 
    house_sqft: RankValue 
    lot_sqft: RankValue 
    llv1: RankValue 
    llv2: RankValue 
    llv3: RankValue
    scq1: RankValue
    scq2: RankValue
    scq3: RankValue
    llv: Optional[RankValue] = None 
    scq: Optional[RankValue] = None 
    scv: Optional[RankValue] = None 
    scv1: Optional[RankValue] = None 
    scv2: Optional[RankValue] = None 
    scv3: Optional[RankValue] = None 
    price: Optional[RankValue] = None 
    price_sqft: Optional[RankValue] = None 
    rental: Optional[RankValue] = None  
    




def value_home(data, zipcode:int, house_size:int, lot_size:int, 
               bucket1:int, bucket2:int, bucket3:int, 
               bucket4:int, bucket5:int, bucket6:int):
    hr = HomeRank(zipcode=zipcode, house_sqft=RankValue(value=house_size), lot_sqft=RankValue(value=lot_size),
                 llv1=RankValue(rank=bucket1), llv2=RankValue(rank=bucket2), llv3=RankValue(rank=bucket3),
                 scq1=RankValue(rank=bucket4), scq2=RankValue(rank=bucket5), scq3=RankValue(rank=bucket6))
    zdata = data.loc[data['zip'] == hr.zipcode]
    if len(zdata) == 0:
        return None
    hr.llv1.value = zdata.loc[zdata['rank'] == hr.llv1.rank].iloc[0]['llv_dom']
    hr.llv2.value = zdata.loc[zdata['rank'] == hr.llv2.rank].iloc[0]['llv_sub_dom_1']
    hr.llv3.value = zdata.loc[zdata['rank'] == hr.llv3.rank].iloc[0]['llv_sub_dom_2']
    
    hr.scq1.value = zdata.loc[zdata['rank'] == hr.scq1.rank].iloc[0]['quality_dom'] 
    hr.scq2.value = zdata.loc[zdata['rank'] == hr.scq2.rank].iloc[0]['quality_sub_dom_1'] 
    hr.scq3.value = zdata.loc[zdata['rank'] == hr.scq3.rank].iloc[0]['quality_sub_dom_2']
    
    hr.llv = RankValue(value=hr.llv1.value + hr.llv2.value + hr.llv3.value)
    hr.scq = RankValue(value=hr.scq1.value + hr.scq2.value + hr.scq3.value)
    
    hr.scv1 = RankValue(value= hr.scq1.value * hr.house_sqft.value)
    hr.scv2 = RankValue(value= hr.scq2.value*hr.house_sqft.value)
    hr.scv3 = RankValue(value= hr.scq3.value*hr.house_sqft.value)
    hr.scv = RankValue(value= hr.scq.value*hr.house_sqft.value)
    
    hr.price = RankValue(value=hr.llv.value + hr.scv.value)
    hr.price_sqft = RankValue(value=hr.price.value / hr.house_sqft.value)
    
    closest_llv = 999999999 
    closest_scq = 999999999
    closest_scv = 999999999
    closest_scv1 = 999999999
    closest_scv2 = 999999999
    closest_scv3 = 999999999
    closest_price = 999999999
    closest_price_sqft = 999999999
    closest_house_size = 999999999
    closest_lot_size = 999999999
    for i in range(len(zdata)):
        if abs(zdata.iloc[i]['lot_location_value'] - hr.llv.value) < closest_llv:
            closest_llv = abs(zdata.iloc[i]['lot_location_value'] - hr.llv.value)
            hr.llv.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['quality'] - hr.scq.value) < closest_scq:
            closest_scq = abs(zdata.iloc[i]['quality'] - hr.scq.value)
            hr.scq.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['scv_dom_1'] - hr.scv1.value) < closest_scv1:
            closest_scv1 = abs(zdata.iloc[i]['scv_dom_1'] - hr.scv1.value)
            hr.scv1.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['scv_sub_dom_1'] - hr.scv2.value) < closest_scv2:
            closest_scv2 = abs(zdata.iloc[i]['scv_sub_dom_1'] - hr.scv2.value)
            hr.scv2.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['scv_sub_dom_2'] - hr.scv3.value) < closest_scv3:
            closest_scv3 = abs(zdata.iloc[i]['scv_sub_dom_2'] - hr.scv3.value)
            hr.scv3.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['scv'] - hr.scv.value) < closest_scv:
            closest_scv = abs(zdata.iloc[i]['scv'] - hr.scv.value)
            hr.scv.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['price'] - hr.price.value) < closest_price:
            closest_price = abs(zdata.iloc[i]['price'] - hr.price.value)
            hr.price.rank = zdata.iloc[i]['rank']
            hr.rental = RankValue(value=zdata.iloc[i]['rental'], rank=zdata.iloc[i]['rank'])
        if abs(zdata.iloc[i]['price_sqft'] - hr.price_sqft.value) < closest_price_sqft:
            closest_house_size = abs(zdata.iloc[i]['price_sqft'] - hr.price_sqft.value)
            hr.price_sqft.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['size'] - hr.house_sqft.value) < closest_house_size:
            closest_house_size = abs(zdata.iloc[i]['size'] - hr.house_sqft.value)
            hr.house_sqft.rank = zdata.iloc[i]['rank']
        if abs(zdata.iloc[i]['lot_size'] - hr.lot_sqft.value) < closest_lot_size:
            closest_lot_size = abs(zdata.iloc[i]['lot_size'] - hr.lot_sqft.value)
            hr.lot_sqft.rank = zdata.iloc[i]['rank']
    
    return hr 
    


    
