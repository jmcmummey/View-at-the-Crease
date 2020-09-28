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
import sqlite3 

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'View From the Bench'

#########################################################################################
#SQL Handle functions
def run_query(q):
    with sqlite3.connect('C:\\Users\\jesse\\Documents\\Projects\\takeaseat\\Data\\hockey_datamvp.db') as conn:
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
                        html.H1(children='View From the Bench',style={'font-size':72,"margin-left": "25px","margin-bottom": "1px"}),

                        html.Div(children='''ADVANCED COACHING ANALYTICS''',style={"color":"red","margin-left": "25px","margin-bottom": "30px"})
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
                                dcc.Dropdown(
                                    id='player-selector',
                                    options=teams
                                    ,
                                    placeholder="Select a Player",
                                    style=player_style
                                ),
                                html.Div(id='slider-title',children='''
                                    Select Game
                                ''',style={"color":"gray","margin-bottom": "1px"}
                                ),
                                dcc.Slider(
                                    id='game-range',
                                    min=0,
                                    max=20,
                                    step=1,
                                    value=0,
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
@app.callback(
    [Output('season-selector','style'),
     Output('season-selector','options'),
     Output('player-selector','style'),
     Output('player-selector','options'),
     Output('game-range','marks'),
     Output('game-range','max'),
     Output('game-range','value')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value'),
    Input(component_id='player-selector', component_property='value')]
)

def update_output_div(team_value,year_value,player_value):

    max_slider = 20
    markz = {}

    if team_value == None: #nothing has been selected
        return season_style,teams,team_style,teams,markz,max_slider,0
    elif (team_value != None) & (year_value==None)& (player_value==None): #only teams have been selected
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            if i == 2004:
                pass
            else:
                seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i+1))})
        season_style['display']='Default'
        return season_style,seasons,team_style,teams,markz,max_slider,0
    elif (team_value != None) & (year_value!=None)& (player_value==None): #only teams have been selected
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            if i == 2004:
                pass
            else:
                seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i+1))})
        #all the players from that season and team
        q = ("""WITH roster AS (SELECT player_id FROM player_log 
                            WHERE team_id=\"{0}\" 
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                            GROUP BY player_id)
            SELECT pl.player,r.player_id
            FROM roster r
            LEFT JOIN player_list pl ON pl.unique_id=r.player_id""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        roster = run_query(q)
        players = []
        for i,row in roster.iterrows():
            players.append({'label':row['player'],'value':row['player_id']})
        season_style['display']='Default'
        player_style['display']='Default'
        return season_style,seasons,player_style,players,markz,max_slider,0
    else: #if everything has been selected
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            if i == 2004:
                pass
            else:
                seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i+1))})
        #all the players from that season and team
        q = ("""WITH roster AS (SELECT player_id FROM player_log 
                            WHERE team_id=\"{0}\" 
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                            GROUP BY player_id)
            SELECT pl.player,r.player_id
            FROM roster r
            LEFT JOIN player_list pl ON pl.unique_id=r.player_id""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        roster = run_query(q)
        players = []
        for i,row in roster.iterrows():
            players.append({'label':row['player'],'value':row['player_id']})
        season_style['display']='Default'
        player_style['display']='Default'
        #all the games from that season and team for the selected player
        q = ("""SELECT * 
                FROM player_log 
                WHERE player_id=\"{0}\"
                AND team_id=\"{1}\"
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {2}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {3}
                """.format(player_value,team_value,int(year_value) + .66,int(year_value)+1.66))
        games = run_query(q)
        dates = games['date_game'].str.extract(r'\d{4}-(\d{2}-\d{2})')[0].values
        max_slider = games.shape[0]-1
        for i,row in enumerate(dates):
            spacing = np.ceil(len(dates)/5)
            if (i%spacing) == 0:
                    markz[i] = row
        
        return season_style,seasons,player_style,players,markz,max_slider,0

@app.callback(
    [Output('slider-title','children'),
    Output('stat_table','data'),
    Output('table_well','style')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value'),
    Input(component_id='player-selector', component_property='value'),
    Input(component_id='game-range', component_property='value')]
)
def data_maker(team_value,year_value,player_value,game_value):
    if (team_value==None) | (year_value==None) | (player_value==None)|(game_value==None): #if nothing is entered in one of the cat.
        return ["Select Game"],pd.DataFrame(columns=['Stat','Value']).to_dict('records'),{'display':'None'}
    else:
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[:4]),int(season[-4:])):
            if i == 2004:
                pass
            else:
                seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i+1))})
        #all the players from that season and team
        q = ("""WITH roster AS (SELECT player_id FROM player_log 
                            WHERE team_id=\"{0}\" 
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                            GROUP BY player_id)
            SELECT pl.player,r.player_id
            FROM roster r
            LEFT JOIN player_list pl ON pl.unique_id=r.player_id""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        roster = run_query(q)
        players = []
        for i,row in roster.iterrows():
            players.append({'label':row['player'],'value':row['player_id']})
        season_style['display']='Default'
        player_style['display']='Default'
        #all the games from that season and team for the selected player
        q = ("""SELECT * 
                FROM player_log 
                WHERE player_id=\"{0}\"
                AND team_id=\"{1}\"
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {2}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {3}
                """.format(player_value,team_value,int(year_value) + .66,int(year_value)+1.66))
        games = run_query(q)
        dates = games['date_game'].str.extract(r'\d{4}-(\d{2}-\d{2})')[0].values
        #now get data for table can use game
        player_info = run_query("""SELECT * FROM player_list pl WHERE pl.unique_id=\"{}\"""".format(player_value))
        player_details = player_info.loc[0,['player','year_start','position','height_cm','weight_kg']].copy()
        player_details.index = ['Player Name',"First Season","Position","Height (cm)","Weight (kg)"]
        player_details['Age'] = np.round(games.at[game_value,'age'],2)
        player_details['Minutes This Season'] = np.round(games.at[game_value,'min_season'],2)
        player_details['Minutes Past 3 Weeks'] = np.round(games.at[game_value,'min_3w'],2)
        player_details['Days to Next Game'] = games.at[game_value,'days_to_next_g']
        player_details['Percent of Games at New Venue (Last 3 wks)'] = np.round(100*games.at[game_value,'venuec'],1)
        player_details = player_details.reset_index()
        player_details.columns = ['Stat','Value']
        
        return ["Game Selected: %s"%dates[game_value]],player_details.to_dict('records'),{'display':'block'}

if __name__ == '__main__':
    app.run_server(debug=True)