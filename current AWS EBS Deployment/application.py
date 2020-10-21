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
#this is the team/goalie object which handles stat generation
from statgen import teamstats as team
from statgen import goalies as goalie 

external_stylesheets = ['/assets/viewfromthecrease.css']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,external_stylesheets])
application = app.server
app.title = 'The View at the Crease'


#########################################################################################
#SQL Handle functions
def run_query(q):
    with sqlite3.connect('assets/hockey_data_goalies.db') as conn:
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

team_style = {'width': '100%',"margin-bottom": "5px",'display':'Default','font-size': 20}
season_style = {'width': '100%',"margin-bottom": "5px",'display':'Default','font-size': 20}
player_style = {'width': '100%',"margin-bottom": "25px",'display':'Default','font-size': 20}


app.layout = html.Div(#sets up the dashboard(
    children = [
        dbc.Row(
                dbc.Col([#title header
                        html.H1(children='     The View at the Crease',style={"border-color":'#e04848','border-style':'solid','border-width':"6px",'color':'#f7e6e6',
                                                                             "background-color":'#44b0eb','font-family':'Garamond','font-size':72,"margin-left": "0px","margin-bottom": "1px","text-align":'center'}),

                        html.Div(children='''GOALTENDER ANALYTICS FOR COACHES''',style={'font-size':30,'fontWeight': 'bold',"color":'#e04848','font-family':'Garamond',"margin-left": "0px","margin-top": "15px","margin-bottom": "30px","text-align":'left'})
                        ],width={"size": 8, "order": 1, "offset": 2})
                ),
        dbc.Row([
                dbc.Col([#dropdowns for team/year/game selection
                        html.Div([
                                dcc.Dropdown(#Dropdown for team selection
                                    id='team-selector',
                                    options=teams,
                                    placeholder="Select a Team",
                                    style= team_style
                                ),
                                dcc.Dropdown(#dropdown for season selection
                                    id='season-selector',
                                    options=teams
                                    ,
                                    placeholder="Select a Season",
                                    style=season_style 
                                ),
                                html.Div(id='slider-title',children='''
                                    Select Game:
                                ''',style={"color":"white","margin-bottom": "1px",'font-size': 20}
                                ),
                                dcc.Slider(#slider to select game
                                    id='game-range',
                                    min=10,
                                    max=20,
                                    step=1,
                                    value=10,
                                )
                                ],style={"position":'center',"margin-left": "50px","margin-bottom":"30px",'width':'100%','display':'inline-block'}
                                ),
                                html.Div([#team data table handling current standings
                                    html.H1(children='Team Standings',style={'font-size':32,'font-family':'Garamond',"color":"white","margin-left": "25px","margin-bottom": "10px"}),
                                    dash_table.DataTable(
                                        id='standing_table',
                                        columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                        style_cell={'textAlign': 'center','font-size': 18},
                                        style_header={'backgroundColor': '#44b0eb','color':'#f7e6e6','fontWeight': 'bold','font-size': 20,'border': '1px #44b0eb','whiteSpace': 'normal',
        'height': 'auto'}, 
                                        data=pd.DataFrame(columns=['Stat','Value']).to_dict('records')
                                        ),
                                    html.H1(children='Previous Results',style={'font-size':32,'font-family':'Garamond',"margin-top": "10px","color":"white","margin-left": "25px","margin-bottom": "10px"}),
                                    dash_table.DataTable(#data table handling previous results
                                        id='pr_table',
                                        columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                        style_cell={'textAlign': 'center','font-size': 18},
                                        style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(238, 238, 238)'},
                                        {'if': {'column_id': 'Host'},'width': '100px'}],
                                        style_header={'backgroundColor': '#44b0eb','color':'#f7e6e6','fontWeight': 'bold','font-size': 20,'border': '1px #44b0eb','whiteSpace': 'normal'},
                                        data=pd.DataFrame(columns=['Stat','Value']).to_dict('records')
                                        )],id='standing_table_sty',style={"margin-left": "0px","border-color":'#e04848',"display":"None"})]
                        ,width={"size": 3, "order": 1, "offset": 1}),
                dbc.Col([
                        html.Div([html.H1(children='Goalie Statistics',style={'font-size':32,'font-family':'Garamond',"color":"white","margin-left": "25px","margin-bottom": "10px","margin-top": "1px"}),
                                dash_table.DataTable( #data table handling goalie results
                                id='goalie_table',
                                columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])],
                                style_cell={'textAlign': 'center','font-size': 18},
                                data=pd.DataFrame(columns=['Stat','Value']).to_dict('records'),
                                style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(238, 238, 238)'}],
                                style_header={'backgroundColor': '#44b0eb','fontWeight': 'bold','font-size': 20,'color':'#f7e6e6','border': '1px #44b0eb', 'whiteSpace': 'normal',
        'height': 'auto'})],id='table_well',style={"display":"None"})]
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
    """  Controls User Selection of Team/Season Dropdowns and Populates the slider with the appropriate dates
    """
    max_slider = 20
    markz = {}
    if team_value == None: # If no team has been selected
        return season_style,teams,markz,max_slider,10,
    elif (team_value != None) & (year_value==None): #When the team has been selected: Populate the season registry
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]#polling for all available seasons
        seasons = []
        #gets all available seasons for that team
        for i in  np.arange(int(season[-4:])-1,int(season[:4]),-1):
            print(i)
            seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i))})
        season_style['display']='Default'
        return season_style,seasons,markz,max_slider,10,
    else: #Teams and Season has been selected - populate the slider with the date range
        q = """select years_active from team_list WHERE team_abbr=\"{}\"""".format(team_value)
        season = run_query(q).iloc[0,0]
        seasons = []
        for i in np.arange(int(season[-4:]),int(season[:4]),-1):
            seasons.append({'label':(str(i)+'-'+str(i+1)),'value':(str(i))})
        #all the games from that season for that team
        q = ("""SELECT * 
                FROM team_log 
                WHERE team_id=\"{0}\" 
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}""".format(team_value,int(year_value) + .66,int(year_value)+1.66))
        games = run_query(q)
        dates = games['date_game'].str.extract(r'\d{4}-(\d{2}-\d{2})')[0].values #this is extracting all the dates.  The index is the date number
        max_slider = games.shape[0]-1
        for i,row in enumerate(dates):
            #skip 10 first games of the season (assume that there's too little data built up yet
            if i<9:
                pass
            else:
                spacing = np.ceil((len(dates)-10)/5)
                if ((i-10)%spacing) == 0:
                        markz[i] = row

        return season_style,seasons,markz,max_slider,10,

#TABLE POPULATION - both for the teams and the goalies
@app.callback(
    [Output('slider-title','children'),
    Output('standing_table','data'),
    Output('standing_table','columns'),
    Output('standing_table','style_cell_conditional'),
    Output('pr_table','data'),
    Output('pr_table','columns'),
    Output('pr_table','style_cell_conditional'),
    Output('standing_table_sty','style'),
    Output('goalie_table','data'),
    Output('goalie_table','columns'),
    Output('goalie_table','style_data_conditional'),
    Output('table_well','style')],
    [Input(component_id='team-selector', component_property='value'),
    Input(component_id='season-selector', component_property='value'),
    Input(component_id='game-range', component_property='value')]
)
def data_maker(team_value,year_value,game_value):
    """
    Once the team/season/day have been selected - load the team and goalie datatables
    """
    #style for standing table
    style_cell_conditional_st=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(238, 238, 238)'},
                                        {'if': {'column_id': 'Team'},'minWidth': '200px', 'width': '200px', 'maxWidth': '200px'},
                                        {'if': {'column_id': 'Games'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Wins'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Loses'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Ties'},'minWidth': '40px', 'width': '40px', 'maxWidth': '40px'},
                                        {'if': {'column_id': 'OTL'},'minWidth': '40px', 'width': '40px', 'maxWidth': '40px'},
                                        {'if': {'column_id': 'Points'},'minWidth': '70px', 'width': '70px', 'maxWidth': '70px'},
                                        {'if': {'column_id': 'Point %'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'SRS'},'minWidth': '70px', 'width': '70px', 'maxWidth': '70px'},
                                        {'if': {'column_id': 'SOS'},'minWidth': '70px', 'width': '70px', 'maxWidth': '70px'}]

    #style for previous games table
    style_cell_conditional_pr = [{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(238, 238, 238)'},
                                        {'if': {'column_id': 'Host'},'minWidth': '200px', 'width': '200px', 'maxWidth': '200px'},
                                        {'if': {'column_id': 'Date'},'minWidth': '110px', 'width': '110px', 'maxWidth': '110px'},
                                        {'if': {'column_id': 'Goals For'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Goals Against'},'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
                                        {'if': {'column_id': 'Result'},'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'},
                                        {'if': {'column_id': 'OT?'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Shots For'},'minWidth': '60px', 'width': '60px', 'maxWidth': '60px'},
                                        {'if': {'column_id': 'Shots Against'},'minWidth': '80px', 'width': '80px', 'maxWidth': '80px'}]  
    #goalie table style
    style_data_conditional_gt = []                                        

    columns=[{"name": i, "id": i} for i in pd.DataFrame(columns=['Stat','Value'])] #blank data for when the tables are hidden
    if (team_value==None) | (year_value==None) |(game_value==None): #if nothing is entered in one of the categories hide all
        return ["Select Game"],pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,style_cell_conditional_st,pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,style_cell_conditional_pr,{"margin-left": "25px",'display':'None'},pd.DataFrame(columns=['Stat','Value']).to_dict('records'),columns,style_data_conditional_gt,{"margin-left": "25px","border-color":'#e04848','border-style':'solid','border-width':"3px",'display':'None'}
    else: #now a selection has been made - populate the data tables
        #import team info
        teaminfo = team(team_value,year_value,game_value)
        teamstandings = teaminfo.standings()
        columns = [{"name": i, "id": i} for i in teamstandings]
        last5 = teaminfo.last_five()
        last5.rename(columns={'Goals':'Goals For','Opp. Goals':'Goals Against','Outcome':'Result','Shots':'Shots For','Opp. Shots':'Shots Against'},inplace=True)
        columnsl5 = [{"name": i, "id": i} for i in last5]
        #import goalie info
        g = goalie(teaminfo.team_value,teaminfo.year_value,teaminfo.game_date)
        columns_gt = [{"name": i, "id": i.replace(' ','')} for i in g.roster]
        columns_rn = {}
        for c in g.roster:
            columns_rn[c] = c.replace(' ','')
        #replace spaces in column names as there's a potential bug in the dash code
        g.roster.rename(columns=columns_rn,inplace=True)
        #now add styling
        for i in g.roster.columns[1:]:
            #hardcode formatting as dash filter_query is NOT WORKING
            #goals per game
            if g.roster.at[6,i]>.15:
                style_data_conditional_gt.append({'if': {'row_index':6,'column_id': i},'color': '#8c0000','fontWeight': 'bold'}) #poor GPG
            elif g.roster.at[6,i]<=-.15:
                style_data_conditional_gt.append({'if': {'row_index':6,'column_id': i},'color': '#078c00','fontWeight': 'bold'}) #better GPG
            #Win/loss                
            if g.roster.at[7,i]<-3:
                style_data_conditional_gt.append({'if': {'row_index':7,'column_id': i},'color': '#8c0000','fontWeight': 'bold'}) #poor impact on wins
            #INJURY RISK
            if g.roster.loc[8,i]==2:
                style_data_conditional_gt.append({'if': {'row_index':8,'column_id': i},'backgroundColor': '#fffc9c'}) #intermediate risk
            elif g.roster.loc[8,i]==3:
                style_data_conditional_gt.append({'if': {'row_index':8,'column_id': i},'backgroundColor': '#ff9999'}) #higher risk
    return ["Game Selected: %s"% teaminfo.game_date],teamstandings.to_dict('records'),columns,style_cell_conditional_st,last5.to_dict('records'),columnsl5,style_cell_conditional_pr,{"margin-left": "25px",'display':'block'},g.roster.to_dict('records'),columns_gt,style_data_conditional_gt,{"margin-left": "25px",'display':'Block'}

if __name__ == '__main__':
    application.run(debug=True,port=8080)