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

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
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
player_style = {'width': '100%',"margin-bottom": "15px",'display':'Default'}


app.layout = html.Div(children=[
        html.H1(children='View From the Bench',style={'font-size':72,"margin-bottom": "1px"}),

        html.Div(children='''
            ADVANCED COACHING ANALYTICS
        ''',style={"color":"red","margin-left": "8px","margin-bottom": "30px"}
        ),
        html.Div([
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
                value=20,
            )]
            ,style={"position":'center',"margin-left": "25px",'width':'30%','display':'inline-block'}
            ),
            html.Div([
                dash_table.DataTable(
                id='table',
                columns=[{"name": i, "id": i} for i in teamsdf.columns],
                data=teamsdf.to_dict('records'),
            )],style={"position":'right',"margin-left": "25px",'width':'30%','display':'inline-block'})
        ])])

#####################################################################################
@app.callback(
    [Output('season-selector','style'),
     Output('season-selector','options'),
     Output('player-selector','style'),
     Output('player-selector','options'),
     Output('game-range','marks'),
     Output('game-range','max'),
     Output('slider-title','children'),],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value'),
    Input(component_id='player-selector', component_property='value'),
    Input(component_id='game-range', component_property='value')]
)

def update_output_div(team_value,year_value,player_value,slider_value):

    max_slider = 20
    markz = {}

    if team_value == None: #nothing has been selected
        return season_style,teams,team_style,teams,markz,max_slider,'Select Game'
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
        return season_style,seasons,team_style,teams,markz,max_slider,'Select Game'
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
        return season_style,seasons,player_style,players,markz,max_slider,'Select Game'
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
        #called for the first time
        if (slider_value == 20) & (len(markz)==0):
            #select the last game
            max_slider = slider_value
        for i,row in enumerate(dates):
            spacing = np.ceil(len(dates)/5)
            if (i%spacing) == 0:
                    markz[i] = row
        
        return season_style,seasons,player_style,players,markz,max_slider,('Select Game: %s' % dates[slider_value])


if __name__ == '__main__':
    app.run_server(debug=True)