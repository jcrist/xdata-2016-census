import pandas as pd
import ujson
from cytoolz import dissoc

exclude = [':meta', 'location_1', ':position', 'subdivision', ':updated_meta',
           ':created_meta', ':sid', 'location_2', 'location']

def dissoc(rec, keys):
    for k in keys:
        rec.pop(k, None)
    return rec

fields = {'number': float,
          'school_district': str,
          'type': str,
          'legal_description': str,
          'dwelling_units_gained_or_lost': int,
          'parcel': str,
          'class_description': str,
          'pin': float,
          'how_far_north': float,
          'day': int,
          ':created_at': int,
          'structure_class': float,
          'council_district': float,
          'suffix': str,
          'res_non': str,
          'month': int,
          'year': int,
          'permit_value': float,
          'prefix': str,
          'how_far_east': float,
          'owner_name': str,
          'name': str,
          'applicant_representative': str,
          'project_description': str,
          'applicant_name': str,
          'fraction': object,
          'permit_number': float,
          'sf_mf': object,
          'county': str,
          ':updated_at': int,
          ':id': str}


def load_and_clean(name):
    with open('building_permit_data/{0}.json'.format(name)) as f:
        data = ujson.load(f)
    lines = data[name]
    new_lines = [dissoc(l, exclude) for l in lines]
    df = pd.DataFrame.from_records(new_lines)
    for k in df.columns:
        if k in fields:
            df[k] = df[k].astype(fields[k])
    return df

files = ['fx3a-kauu', 'akhc-zaz6', 'cvnj-fvgf', '4hr8-fgbf',
         'hqe6-tuji', 'vcj3-ncb3', 'qt6m-65bz'] 

df = pd.concat([load_and_clean(f) for f in files])
