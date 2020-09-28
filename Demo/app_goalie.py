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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'View From the Crease'
cwd_directory = os.getcwd()
print(cwd_directory +'\\Data\\hockey_data_goalies.db')
#########################################################################################
#SQL Handle functions
def run_query(q):
    with sqlite3.connect(cwd_directory +'\\Data\\hockey_data_goalies.db') as conn:
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
#########################################################################################

#fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")

team_style = {'width': '100%',"margin-bottom": "5px",'display':'Default'}
season_style = {'width': '100%',"margin-bottom": "5px",'display':'Default'}
player_style = {'width': '100%',"margin-bottom": "25px",'display':'Default'}


app.layout = html.Div(
    [
        dbc.Row(
                dbc.Col([
                        html.H1(children='View From the Crease',style={'font-size':72,"margin-left": "25px","margin-bottom": "1px"}),

                        html.Div(children='''GOALTENDER ANALYTICS FOR COACHES''',style={"color":"red","margin-left": "25px","margin-bottom": "30px"})
                        ])
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
                                ],style={"position":'center',"margin-left": "25px",'width':'100%','display':'inline-block'}
                                )]
                        ,width={"size": 3, "order": 1, "offset": 0}),
                dbc.Col([
                        html.Div([dash_table.DataTable(
                                id='stat_table',
                                columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                style_cell={'textAlign': 'center'},
                                data=pd.DataFrame(columns=['Stat','Value']).to_dict('records')
                                )],id='table_well',style={"display":"None"})]
                        ,width={"size": 4, "order": 2, "offset": 1})
                ])
            ])

# #####################################################################################
#DROPDOWN/SLIDER CONTROL
@app.callback(
    [Output('season-selector','style'),
     Output('season-selector','options'),
     Output('game-range','marks'),
     Output('game-range','max'),
     Output('game-range','value'),
     Output('slider-title','children')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value')]
)

def update_output_div(team_value,year_value):
    """  Controls User Selection of Team/Season Dropdowns and populates the slider
    """
    max_slider = 20
    markz = {}

    if team_value == None: #nothing has been selected
        return season_style,teams,markz,max_slider,10,"Select Game:"
    elif (team_value != None) & (year_value==None): #Teams have been selected: Populate the season registry
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i))})
        season_style['display']='Default'
        return season_style,seasons,markz,max_slider,10,'Select Game:'
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

        return season_style,seasons,markz,max_slider,10,'Game Selected: %s' % markz[10]
#TABLE POPULATION
@app.callback(
    [Output('slider-title','children'),
    Output('stat_table','data'),
    Output('stat_table','columns'),
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
        return ["Select Game"],pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,{'display':'None'}
    else:
        #call up all the players who played for that team this year
        q = ("""WITH goalies as (SELECT player_id
        FROM player_log 
        WHERE team_id=\"{0}\" 
        AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
        AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
        GROUP BY player_id)
        SELECT pl.*
        FROM goalies g
        LEFT JOIN player_list pl ON pl.unique_id=g.player_id""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        active_players = run_query(q)
        active_players_T = active_players.transpose()
        active_players_T.columns = active_players_T.loc['player']
        active_players_T.drop(['unique_id','player'],inplace=True)
        active_players_T.reset_index(inplace=True)
        active_players_T = active_players_T.rename(columns={'index':"Stat"})
        columns=[{"name": i, "id": i} for i in active_players_T]
        #all the games from that season and team for the selected player
        q = ("""SELECT * 
                FROM team_log 
                WHERE team_id=\"{0}\" 
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        games = run_query(q)
        dates = games['date_game'].str.extract(r'\d{4}-(\d{2}-\d{2})')[0].values
        
        return ["Game Selected: %s"%dates[game_value]],active_players_T.to_dict('records'),columns,{'display':'block'}

if __name__ == '__main__':
    app.run_server(debug=True)