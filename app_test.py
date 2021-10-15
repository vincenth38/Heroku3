import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table
import pandas as pd
import base64
import io
import datetime
from pathlib import Path
import dash_uploader as du
import uuid

########### Initiate the app
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
#app.title=tabtitle
# 1) configure the upload folder
du.configure_upload(app, r"C:\tmp\Uploads")

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-data-upload'),

    # 2) Use the Upload component
    html.Div([du.Upload(),])

])
def clean_data(df):
    df['Planned Units'] = df['Planned Units'].str.replace(r'h', '')
    df['Remaining Units'] = df['Remaining Units'].str.replace(r'h', '')
    df['Planned Units'] = pd.to_numeric(df['Planned Units'])
    df['Remaining Units'] = pd.to_numeric(df['Remaining Units'])
    df = df.fillna(0)
    # df.filter(like='FY', axis=1).replace('h','',regex=True,inplace=True)
    df_FM = df.loc[:, df.columns.str.startswith('FY')].replace('h', '', regex=True)
    df_FM = df_FM.astype(float)

    # Convert Columns to date
    df_FM.columns = df_FM.columns.str.replace(", FM", "-")
    df_FM.columns = df_FM.columns.str.replace("FY", "")
    df_FM = df_FM.add_suffix('-01')
    df_FM.columns = pd.to_datetime(df_FM.columns).date

    # CONVERSION TO REAL DATE
    df_FM.columns = df_FM.columns + pd.DateOffset(months=-3)
    # df_FY.columns.DateOffset(months = x['month shift']), axis=1)

    # df_FY.columns.replace(', FM','-',regex=True)
    df_FM.head()
    df_FM_FTE = df_FM / (145)
    df_FM_FTE = df_FM_FTE.add_suffix('FTE')

    # QUARTER with FY ending up in September
    df_FQ = df_FM.groupby(pd.PeriodIndex(df_FM.columns, freq='Q-SEP'), axis=1).sum()
    df_FQ_FTE = df_FQ / (145 * 3)

    #    df_FQ_FTE
    df_FY = df_FM.groupby(pd.PeriodIndex(df_FM.columns, freq='A-SEP'), axis=1).sum()
    df_FY_FTE = df_FY / (1740)

    df_FQ_FTE = df_FQ_FTE.add_suffix('FTE')
    df_FQ_FTE.head()
    df_FY_FTE = df_FY_FTE.add_suffix('FTE')

    df = df.fillna(0)

    spec_chars_date = ["a", 'A', "AM", "*", "PM", "d"]
    for char in spec_chars_date:
        df['Start'] = df['Start'].str.replace(char, '')
        df['Finish'] = df['Finish'].str.replace(char, '')
        df['Actual Duration'] = df['Actual Duration'].str.replace(char, '')
        df['At Completion Duration'] = df['At Completion Duration'].str.replace(char, '')
        df['Planned Duration'] = df['Planned Duration'].str.replace(char, '')
        df['Remaining Duration'] = df['Remaining Duration'].str.replace(char, '')

    df['Start'] = pd.to_datetime(df['Start'])
    df['Finish'] = pd.to_datetime(df['Finish'])

    df['L3'] = df['WBS Path'].str[:4]
    df['L4'] = df['WBS Path'].str[:7]
    df['L5'] = df['WBS Path'].str[:10]
    df['L6'] = df['WBS Path'].str[:13]

    # Get unique Resources ID
    unique_ressource = df['Resource Name'].unique()

    # Read the category of resources
    df_res_cat = pd.read_excel('/content/drive/MyDrive/Colab Notebooks/Resource_Conversion.xlsx')
    df = df.merge(df_res_cat, on='Resource Name', how='left')

    # Concatenate all the dataframe into one
    df = pd.concat([df, df_FM, df_FM_FTE, df_FQ, df_FQ_FTE, df_FY, df_FY_FTE], axis=1)

    # Reorder WBS Columns
    df = df[['L3'] + ['L4'] + ['L5'] + [col for col in df.columns if col not in ['L3', 'L4', 'L5']]]
    df.drop('WBS Path', axis=1, inplace=True)


    # EXPORT THE 1.03 DATA

    #df[(df['L3'] == '1.03')].head()
    # df.to_excel('/content/drive/MyDrive/Colab Notebooks/data.xlsx')
    #df[(df['L3'] == '1.03')].to_csv('/content/drive/MyDrive/Colab Notebooks/2011-10-11_1.03_Ressources_Clean.csv',
    #                                encoding='utf-8', index=False)



def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
            df = clean_data(df)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
 #      df = df.head()
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in df.columns]
        ),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@app.callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children









if __name__ == '__main__':
    app.run_server(debug=True)