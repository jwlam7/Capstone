import numpy as np
import pandas as pd

import plotly.express as px 
import plotly.graph_objects as go 
from dash import Dash, dash_table, dcc, html, Input, Output
#----------------------------------------------------------------------------------------------------------
# Used to display the transactions made by customers living in a given zip code for a given month and year. 
# Order by day in descending order.

# read cleaned data + filter for only the SSN (need this to merge dataframes) and CUST_ZIP
customer_df = pd.read_csv('cleaned_files/cleaned_customer.csv')
customer_df = customer_df[['SSN', 'CUST_ZIP', 'CUST_STATE']]

# read cleaned data + rename column (need this to merge dataframes)
credit_card_df = pd.read_csv('cleaned_files/cleaned_credit.csv')
credit_card_df.rename(columns={'CUST_SSN':'SSN'}, inplace=True)

# merge both dataframes
merged_df = credit_card_df.merge(customer_df, on='SSN')
# drop SSN - customer privacy
merged_df.drop(columns=['SSN'], inplace=True)
# convert column TIMEID to date type
merged_df['TIMEID'] = pd.to_datetime(merged_df['TIMEID'], format='%Y%m%d')
# keep only the date (not the timezone)
merged_df['TIMEID'] = merged_df['TIMEID'].dt.date 

# dropdown label
transaction_type = merged_df['TRANSACTION_TYPE'].unique()
transaction_type_options = [{'label': type, 'value': type} for type in transaction_type]
# state label
state = merged_df['CUST_STATE'].unique()
state.sort()
state_options = [{'label': s, 'value': s} for s in state]

# find unique zipcodes
list_of_zipcodes = merged_df['CUST_ZIP'].sort_values().unique()
zipcodes_df = pd.DataFrame(list_of_zipcodes, columns=['Filter by Zip Code'])
# find unique months
list_of_months = pd.to_datetime(merged_df['TIMEID']).dt.month.unique()
list_of_months.sort()
months_df = pd.DataFrame(list_of_months, columns=['Filter by Month'])
# find unique years
list_of_years = pd.to_datetime(merged_df['TIMEID']).dt.year.unique()
list_of_years.sort()
years_df = pd.DataFrame(list_of_years, columns=['Filter by Year'])
#----------------------------------------------------------------------------------------------------------
# Plotly Dash App
app = Dash(__name__)

app.layout = html.Main([
                html.Div([
                    html.H1('Customer Transactions'),
                    html.Div([
                        html.Section([
                            dash_table.DataTable(merged_df.to_dict('records'),                              # https://dash.plotly.com/datatable
                                                [{'name': i, 'id': i} for i in merged_df.columns], 
                                                page_size=10, 
                                                id='data_table',
                                                style_as_list_view=True,
                                                style_header={'fontWeight': 'bold'},
                                                style_cell={'textAlign': 'center', 'font-family': 'Sans-serif'}),
                            html.Div([
                                html.Section([
                                    html.Div([
                                        html.Section([
                                            html.P('Transactions'),
                                            html.P('0')
                                        ]),
                                        html.Section([
                                            html.P('Total Dollars'),
                                            html.P('$0')
                                        ])
                                    ], className='values'),
                                    dcc.Dropdown(
                                        id='transaction_type',
                                        className='dropdown',
                                        placeholder='Select a transaction type',
                                        options=transaction_type_options,
                                        maxHeight=100
                                    )], className='values_container'),
                                html.Section([
                                    html.Div([
                                        html.Section([
                                            html.P('Branches'),
                                            html.P('0')
                                        ]),
                                        html.Section([
                                            html.P('Total Dollars'),
                                            html.P('$0')
                                        ])
                                    ], className='values'),
                                    dcc.Dropdown(
                                        id='state',
                                        className='dropdown',
                                        placeholder='Select a state',
                                        options=state_options,
                                        maxHeight=100
                                    )], className='values_container')
                            ], className='stats')
                        ], className='data'),
                        html.Aside([
                            dash_table.DataTable(zipcodes_df.to_dict('records'), 
                                                 [{'name': i, 'id': i} for i in zipcodes_df],
                                                 id='zipcode_list',
                                                 style_header={'fontWeight': 'bold'}, 
                                                 style_table={'height': '350px','overflowY': 'auto'}),
                            html.Br(),
                            dash_table.DataTable(months_df.to_dict('records'), 
                                                 [{'name': i, 'id': i} for i in months_df],
                                                 id='months_list',
                                                 style_header={'fontWeight': 'bold'}, 
                                                 style_table={'height': '150px','overflowY': 'auto'}),
                            html.Br(),
                            dash_table.DataTable(years_df.to_dict('records'), 
                                                 [{'name': i, 'id': i} for i in years_df],
                                                 id='years_list',
                                                 style_header={'fontWeight': 'bold'}, 
                                                 style_table={'height': '150px','overflowY': 'auto'})
                        ], className='data_sidebar')
                    ], className='container')
                ], className='main_container')
            ], className='main')
#----------------------------------------------------------------------------------------------------------
# update dashboard based on user input
@app.callback(
    Output('data_table', 'data'), 
    [Input('zipcode_list', 'active_cell'), Input('months_list', 'active_cell'), Input('years_list', 'active_cell')] 
)
def update_data_table(zipcode_list, months_list, years_list):
    if zipcode_list == None and months_list == None and years_list == None:
        return merged_df.to_dict('records')
    else:
        # defaults to all, if end-user does not click on any filters 
        zipcode_target = merged_df['CUST_ZIP'] != None
        month_target = merged_df['TIMEID'] != None
        year_target = merged_df['TIMEID'] != None

        # filter by zipcode 
        if zipcode_list:
            zipcode_cell_value = zipcodes_df.iloc[zipcode_list['row']].values[0]
            zipcode_target = merged_df['CUST_ZIP'] == zipcode_cell_value

        # filter by month
        if months_list:
            month_cell_value = months_df.iloc[months_list['row']].values[0]
            month_target = pd.to_datetime(merged_df['TIMEID']).dt.month == month_cell_value
        
        # filter by year
        if years_list:
            year_cell_value = years_df.iloc[years_list['row']].values[0]
            year_target = pd.to_datetime(merged_df['TIMEID']).dt.year == year_cell_value
        
        # if both month filter + year filter are clicked, need to find only the ones in common in both
        if months_list and years_list:
            common_target = month_target.isin(year_target)
            filtered_df = merged_df[zipcode_target & common_target]
        elif months_list == None and years_list:
            filtered_df = merged_df[zipcode_target & year_target]
        elif months_list and years_list == None:
            filtered_df = merged_df[zipcode_target & month_target]
        else:
            filtered_df = merged_df[zipcode_target & month_target & year_target]
        # sort by day in descending order
        filtered_df = filtered_df.sort_values('TIMEID', ascending=False)
        # needs to match the data in data_table
        return filtered_df.to_dict('records')
#----------------------------------------------------------------------------------------------------------
if __name__ == '__main__':
    app.run_server(debug=True)                                                                              # for code reloading / hot reloading
