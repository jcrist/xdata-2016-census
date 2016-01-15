import pandas as pd
import numpy as np
from toolz import get
import json

from bokeh.plotting import Figure
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.models.widgets import HBox, VBoxForm, Slider, CheckboxGroup, Select
from bokeh.io import curdoc


def select_permits():
    types = get(permit_type_checkbox.active, permit_types)
    res_non = get(res_non_checkbox.active, res_non_types)
    selected = df[(df.year >= min_year.value) &
                  (df.year <= max_year.value) &
                  (df.permit_value >= min_permit_cost.value) &
                  (df.permit_value <= max_permit_cost.value) &
                  (df.type.isin(types)) &
                  (df.res_non.isin(res_non))]
    return selected


def total_permits(df):
    return pd.DataFrame(dict(value=df.groupby(df.geo_id_2000).permit_value.count()))


def mean_permit_value(df):
    return pd.DataFrame(dict(value=df.groupby(df.geo_id_2000).permit_value.mean()))


def median_permit_value(df):
    return pd.DataFrame(dict(value=df.groupby(df.geo_id_2000).permit_value.median()))


def delta_housing_units(df):
    return pd.DataFrame(dict(value=df.groupby(df.geo_id_2000)
                             .dwelling_units_gained_or_lost.sum()))


def log_alpha(values):
    min = values.min()
    alpha = np.log1p(values - min)
    return alpha/alpha.max() * 0.9 + 0.1


def update(attrname, old, new):
    df = select_permits()
    agg = methods[agg_method.value](df)
    agg = agg.join(blocks_2000)

    source.data = dict(
            xs=agg['xs'],
            ys=agg['ys'],
            color=['blue']*agg.shape[0],
            value=agg.value,
            alpha=log_alpha(agg.value))
    p.title = agg_method.value


# -- Prepare Data --
def extract(b):
    b = json.loads(b)
    coordinates = b['geometry']['coordinates']
    xs, ys = zip(*coordinates[0])
    return xs, ys

with pd.HDFStore('census.h5', mode='r') as hdf:
    blocks_2000 = hdf['geojson_2000']
xs, ys = zip(*map(extract, blocks_2000.block_shapes))
blocks_2000['xs'] = xs
blocks_2000['ys'] = ys
blocks_2000 = blocks_2000.drop('block_shapes', axis=1)

df = pd.read_csv('permits.csv', low_memory=False)


# -- Input Controls --
min_year = Slider(title='Min Year', value=2000, start=2000, end=2014, step=1)
max_year = Slider(title='Max Year', value=2014, start=2000, end=2014, step=1)

min_permit_cost = Slider(title='Min Permit Value', value=0, start=0, end=.12e9, step=1e4)
max_permit_cost = Slider(title='Max Permit Value', value=.12e9, start=0, end=.12e9, step=1e4)

permit_types = ['Additions, Alterations, Repairs', 'Demolition', 'Move Building', 'New Construction']
permit_type_checkbox = CheckboxGroup(name='Permit Type',
                                     labels=permit_types, active=[0, 1, 2, 3])

res_non_types = ['Residential', 'Non-Residential']
res_non_checkbox = CheckboxGroup(name='Residential/Non-Residential',
                                 labels=res_non_types, active=[0, 1])

methods = {'Number of Permits': total_permits,
           'Mean Permit Value': mean_permit_value,
           'Median Permit Value': median_permit_value,
           'Delta Housing Units': delta_housing_units}

agg_method = Select(title='Aggregation Method', value="Number of Permits", options=list(methods))


# Create Column Data Source that will be used by the plot
source = ColumnDataSource(data=dict(xs=[], ys=[], color=[], alpha=[], value=[]))

hover = HoverTool(tooltips=[
    ("Value", "@value"),
])

p = Figure(plot_height=700, plot_width=700, title="",
           x_range=[-94.9, -94.25], y_range=[38.8, 39.45],
           tools=[hover, 'wheel_zoom', 'reset', 'pan'])
p.patches(xs="xs", ys="ys", source=source, fill_color="color",
          fill_alpha='alpha', line_color=None)


controls = [min_year, max_year, min_permit_cost, max_permit_cost,
            agg_method, permit_type_checkbox, res_non_checkbox]

for control in controls:
    if hasattr(control, 'value'):
        control.on_change('value', update)
    elif hasattr(control, 'active'):
        control.on_change('active', update)

inputs = HBox(VBoxForm(controls), width=300)

update(None, None, None)    # initial load of the data

curdoc().add_root(HBox(inputs, p, width=1100))
