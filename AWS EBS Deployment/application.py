# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import numpy as np
import os
import sqlite3
#this is the team object with handsls
from statgen import teamstats as team
from statgen import goalies as goalie 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,external_stylesheets])
application = app.server
app.title = 'The View at the Crease'


#########################################################################################
#SQL Handle functions
def run_query(q):
    with sqlite3.connect('assests/hockey_data_goalies.db') as conn:
        x = pd.read_sql(q,conn)
    return x
def show_tables():
    r = """
    Select name,type
    FROM sqlite_master
    WHERE type in ("table","view");
        """
    return run_query(r)

#Load Teams
teamsdf = run_query("""Select team_name, team_abbr From team_list""")
teams = []
for i,row in teamsdf.sort_values('team_name',axis=0).iterrows():
    teams.append({'label':row['team_name'],'value':row['team_abbr']})
########################################################################################

#fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

team_style = {'width': '100%',"margin-bottom": "5px",'display':'Default'}
season_style = {'width': '100%',"margin-bottom": "5px",'display':'Default'}
player_style = {'width': '100%',"margin-bottom": "25px",'display':'Default'}


app.layout = html.Div(
    [
        dbc.Row(
                dbc.Col([
                        html.H1(children='     The View at the Crease',style={"border-color":'#F21919','border-style':'solid','border-width':"6px",
                                                                             "background-color":'#1998F2','font-size':72,"margin-left": "0px","margin-bottom": "1px","text-align":'center'}),

                        html.Div(children='''GOALTENDER ANALYTICS FOR COACHES''',style={'font-size':24,"color":"red","margin-left": "75px","margin-top": "15px","margin-bottom": "15px","text-align":'left'})
                        ],width={"size": 7, "order": 1, "offset": 0})
                ),
        dbc.Row([
                dbc.Col([
                        html.Div([
                                dcc.Dropdown(
                                    id='team-selector',
                                    options=teams,
                                    placeholder="Select a Team",
                                    style= team_style
                                ),
                                dcc.Dropdown(
                                    id='season-selector',
                                    options=teams
                                    ,
                                    placeholder="Select a Season",
                                    style=season_style 
                                ),
                                html.Div(id='slider-title',children='''
                                    Select Game:
                                ''',style={"color":"gray","margin-bottom": "1px"}
                                ),
                                dcc.Slider(
                                    id='game-range',
                                    min=10,
                                    max=20,
                                    step=1,
                                    value=10,
                                )
                                ],style={"position":'center',"margin-left": "50px","margin-bottom":"30px",'width':'100%','display':'inline-block'}
                                ),
                                html.Div([
                                    html.H1(children='Team Standings',style={'font-size':24,"margin-left": "25px","margin-bottom": "10px"}),
                                    dash_table.DataTable(
                                        id='standing_table',
                                        columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                        style_cell={'textAlign': 'center'},
                                        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(248, 248, 248)'},
                                        {'if': {'column_id': 'Team'},'width': '100px'}],
                                        style_header={'backgroundColor': 'rgb(230, 230, 230)','fontWeight': 'bold'}, 
                                        data=pd.DataFrame(columns=['Stat','Value']).to_dict('records')
                                        ),
                                    html.H1(children='Previous Results',style={'font-size':24,"margin-top": "10px","margin-left": "25px","margin-bottom": "10px"}),
                                    dash_table.DataTable(
                                        id='pr_table',
                                        columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                        style_cell={'textAlign': 'center'},
                                        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(248, 248, 248)'},
                                        {'if': {'column_id': 'Host'},'width': '100px'}],
                                        style_header={'backgroundColor': 'rgb(230, 230, 230)','fontWeight': 'bold'},
                                        data=pd.DataFrame(columns=['Stat','Value']).to_dict('records')
                                        )],id='standing_table_sty',style={"margin-left": "50px","display":"None"})]
                        ,width={"size": 3, "order": 1, "offset": 0}),
                dbc.Col([
                        html.Div([html.H1(children='Goalie Statistics',style={'font-size':24,"margin-left": "25px","margin-bottom": "10px"}),
                                dash_table.DataTable(
                                id='goalie_table',
                                columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                style_cell={'textAlign': 'center'},
                                data=pd.DataFrame(columns=['Stat','Value']).to_dict('records'),
                                style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(248, 248, 248)'}],
                                style_header={'backgroundColor': 'rgb(230, 230, 230)','fontWeight': 'bold'})],id='table_well',style={"display":"None"})]
                                ,width={"size": 4, "order": 2, "offset": 2})
                ]),
            
            ])
#,style={"height": "100vh"}
# #####################################################################################
#DROPDOWN/SLIDER CONTROL
@app.callback(
    [Output('season-selector','style'),
     Output('season-selector','options'),
     Output('game-range','marks'),
     Output('game-range','max'),
     Output('game-range','value')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value')]
)

def update_output_div(team_value,year_value):
    """  Controls User Selection of Team/Season Dropdowns and populates the slider
    """
    max_slider = 20
    markz = {}
    if team_value == None: #nothing has been selected
        return season_style,teams,markz,max_slider,10,
    elif (team_value != None) & (year_value==None): #Teams have been selected: Populate the season registry
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i))})
        season_style['display']='Default'
        return season_style,seasons,markz,max_slider,10,
    else: #Teams and Season has been selected - populate the slider
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i))})
        #all the games from that season for that team
        q = ("""SELECT * 
                FROM team_log 
                WHERE team_id=\"{0}\" 
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        games = run_query(q)
        dates = games['date_game'].str.extract(r'\d{4}-(\d{2}-\d{2})')[0].values
        max_slider = games.shape[0]-1
        for i,row in enumerate(dates):
            #skip 10 first games of the season
            if i<9:
                pass
            else:
                spacing = np.ceil((len(dates)-10)/5)
                if ((i-10)%spacing) == 0:
                        markz[i] = row

        return season_style,seasons,markz,max_slider,10,
#TABLE POPULATION
@app.callback(
    [Output('slider-title','children'),
    Output('standing_table','data'),
    Output('standing_table','columns'),
    Output('pr_table','data'),
    Output('pr_table','columns'),
    Output('standing_table_sty','style'),
    Output('goalie_table','data'),
    Output('goalie_table','columns'),
    Output('table_well','style')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value'),
    Input(component_id='game-range', component_property='value')]
)
def data_maker(team_value,year_value,game_value):
    """
    Loads the goalie data for the year/game
    """
    columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])]
    if (team_value==None) | (year_value==None) |(game_value==None): #if nothing is entered in one of the cat.
        return ["Select Game"],pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,{"margin-left": "25px",'display':'None'},pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,{"margin-left": "25px",'display':'None'}
    else:
        #import team info
        teaminfo = team(team_value,year_value,game_value)
        teamstandings = teaminfo.standings()
        columns = [{"name": i, "id": i} for i in teamstandings]
        last5 = teaminfo.last_five()
        columnsl5 = [{"name": i, "id": i} for i in last5]
        #import goalie info
        g = goalie(teaminfo.team_value,teaminfo.year_value,teaminfo.game_date)
        
        return ["Game Selected: %s"% teaminfo.game_date],teamstandings.to_dict('records'),columns,last5.to_dict('records'),columnsl5,{"margin-left": "25px",'display':'block'},g.roster.to_dict('records'),[{"name": i, "id": i} for i in g.roster],{"margin-left": "25px",'display':'Block'}

if __name__ == '__main__':
    application.run(debug=True,port=8080)