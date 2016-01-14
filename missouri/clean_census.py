import pandas as pd
import json
import fiona
from toolz import dissoc


files_2000 = {'White': 'DEC_00_SF1_H011A_with_ann.csv',
              'Black': 'DEC_00_SF1_H011B_with_ann.csv',
              'Native': 'DEC_00_SF1_H011C_with_ann.csv',
              'Asian': 'DEC_00_SF1_H011D_with_ann.csv',
              'Pacific_Islander': 'DEC_00_SF1_H011E_with_ann.csv',
              'Other': 'DEC_00_SF1_H011F_with_ann.csv',
              'Two_or_more': 'DEC_00_SF1_H011G_with_ann.csv',
              'Hispanic': 'DEC_00_SF1_H011H_with_ann.csv'}

files_2010 = {'White': 'DEC_10_SF1_H11A_with_ann.csv',
              'Black': 'DEC_10_SF1_H11B_with_ann.csv',
              'Native': 'DEC_10_SF1_H11C_with_ann.csv',
              'Asian': 'DEC_10_SF1_H11D_with_ann.csv',
              'Pacific_Islander': 'DEC_10_SF1_H11E_with_ann.csv',
              'Other': 'DEC_10_SF1_H11F_with_ann.csv',
              'Two_or_more': 'DEC_10_SF1_H11G_with_ann.csv',
              'Hispanic': 'DEC_10_SF1_H11H_with_ann.csv'}

merge_to_other = ['Native', 'Pacific_Islander', 'Other', 'Two_or_more']


def clean_2000_data():
    dataframes = {}
    for group, path in files_2000.items():
        df = pd.read_csv('2000_Data/' + path, skiprows=1)
        df = df.drop(['Id', 'Geography',
                      'Total population in occupied housing units:'], axis=1)
        df = df.set_index('Id2')
        df.index.name = 'Geo_Id'
        df.columns = ['Owned', 'Rented']
        if group not in merge_to_other:
            df['Race'] = group
        dataframes[group] = df

    other = sum(dataframes.pop(k) for k in merge_to_other)
    other['Race'] = 'Other'
    dataframes['Other'] = other

    df = pd.concat(dataframes.values())
    df = df.pivot(df.index, 'Race')
    df['Year'] = 2000
    return df


def clean_2010_data():
    dataframes = {}
    for group, path in files_2010.items():
        df = pd.read_csv('2010_Data/' + path, skiprows=1)
        df = df.set_index('Id2')
        df.index.name = 'Geo_Id'
        df['Owned'] = df['Owned with a mortgage or a loan'] + df['Owned free and clear']
        df = df.drop(['Id', 'Geography', 'Population in occupied housing units:',
                      'Owned with a mortgage or a loan',
                      'Owned free and clear'], axis=1)
        df.columns = ['Owned', 'Rented']
        if group not in merge_to_other:
            df['Race'] = group
        dataframes[group] = df

    other = sum(dataframes.pop(k) for k in merge_to_other)
    other['Race'] = 'Other'
    dataframes['Other'] = other

    df = pd.concat(dataframes.values())
    df = df.pivot(df.index, 'Race')
    df['Year'] = 2010
    return df


def clean_blob(f):
    return json.dumps(dissoc(f, 'id', 'properties'))


def build_gjson(frame, collection, code):
    ids = set(frame.index)
    features = [clean_blob(f) for f in c if code(f) in ids]
    assert len(ids) == len(features)
    df = pd.DataFrame({'block_shapes': features}, index=ids)
    df.index.name = 'Geo_Id'
    return df

df_2000 = clean_2000_data()
df_2010 = clean_2010_data()

code = lambda t: int('{STATE}{COUNTY}{TRACT:0<6}{BLKGROUP}'.format(**t['properties']))
c = fiona.open('shapefiles/MO_block_groups_2000.shp')
blocks_2000 = build_gjson(df_2000, c, code)


code = lambda t: int('{STATE}{COUNTY}{TRACT:0<6}{BLKGRP}'.format(**t['properties']))
c = fiona.open('shapefiles/MO_block_groups_2010.shp')
blocks_2010 = build_gjson(df_2010, c, code)

hdf = pd.HDFStore('census.h5')
hdf.put('census_2000', df_2000)
hdf.put('census_2010', df_2010)
hdf.put('geojson_2000', blocks_2000)
hdf.put('geojson_2010', blocks_2010)
hdf.close()
