import pandas as pd
import numpy as np
import scipy.stats as stats
import sqlite3
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import *
import re
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from joblib import dump, load

#this module contains two classes: teamstats and goalies, both of which generate statistics displayed in the main application 

class teamstats:

    """
        This class generates a variety of statistics for the team given the year and game_no

        attributes:

        team_value (str) - the team abbr
        year_value (int) - the year in question (YYYY)-(YYYY+1)
        game_no (int) - game number for the team where game 1 is the second game of the season
        game_date (str) - the date of the game
        team_name (str) - note this is the full team name
        opp_name (str) - the opposing team name
        opp_team_value (str) - the opposing team abbr
        opp_game_no - the opposing team game no
        hometeamstats - a dataframe of the hometeam stats
        oppteamstats - a dataframe of the opposition team stats

        methods: 

        opp_team() - generates information on opposing team for the game selected
        sos_calc() - generates the team SOS (strength of season) based on their schedule 
        team_stat_gen() - generates statistics on the entered team based on their schedule to date (returns DataFrame)
        standings() - Combines the home and away dataframes
        last_five() - finds the last five contests between the two teams over last season and this one
        run_query() - used to query the database
    """
    def __init__(self,*argv):
        """
            INPUT ARGS:
                team_value(string) the team abbr ie ANA
                year_value(int) the season year YYYY where season is YYYY-YYYY+1
                game_no(in) - game number for the team where game 1 is the second game of the season
        """

        #check if correct no of args entered
        if len(argv)==3:
            self.team_value = argv[0]
            self.year_value = argv[1]
            self.game_no = argv[2]
        else:
            raise ValueError('Wrong number of input arguments.  Please use either three.')
        
        #get opposing teamdata
        (self.game_date,self.team_name,self.opp_name,self.opp_value,self.opp_game_no) = self.opp_team()

        #get hometeamstats
        self.hometeamstats = self.team_stat_gen(self.team_value,self.year_value,self.game_no)
        #get hometeamstats
        self.oppteamstats = self.team_stat_gen(self.opp_value,self.year_value,self.opp_game_no)

    def opp_team(self):
        """
        Gets the opposing team information for the date selected
        INPUT (from self attributes):
            self.team_value (str)
            self.year_value (int)
            self.game_no (int)
        OUTPUT
            game_date (str) - the date of the game
            team_name (str) - note this is the full team name
            opp_name (str) - the opposing team name
            opp_team_value (str) - the opposing team abbr
            opp_game_no - the opposing team game no
        """
        #find the game date
        q = ("""SELECT *
            FROM team_log 
            WHERE team_id=\"{0}\" 
            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
            AND game_number={3}""".format(self.team_value,int(self.year_value) + .66,int(self.year_value)+1.66,self.game_no))
        game_selected = self.run_query(q)
        game_date = game_selected['date_game'].values[0]
        opp_name =  game_selected['opp_name'].values[0]

        #get home team name
        q = """SELECT team_name
            FROM team_list 
            WHERE team_abbr=\"{0}\"""".format(self.team_value)
        team_name = self.run_query(q).at[0,'team_name']

        #get opponent abbr
        q = """SELECT * 
            FROM team_list 
            WHERE team_name=\"{0}\" 
            AND CAST(SUBSTR(years_active,6,9) as INT)>{1}""".format(opp_name,self.year_value)
        opp_abbr = self.run_query(q).at[0,'team_abbr']

        #get game # for opponent
        q = """SELECT * 
            FROM team_log 
            WHERE team_id=\"{0}\" 
            AND date_game=\"{1}\"""".format(opp_abbr,game_date)
        opp_gn = self.run_query(q).at[0,'game_number']

        return (game_date,team_name,opp_name,opp_abbr,opp_gn)
    
    def sos_calc(self,year,game_no,nme,wind=[0]):
        """
            CALCULATES THE SOS FOR THE TEAM entered faced before a given date
            The SOS is a measure of the Strength Of Schedule, reflective of how hard
            a season the team has had.  It's used to adjust the normalised goal differential to get a measure
            of how good a team is (beyond its number of wins)
        INPUT:
            year: the current season (YYYY-YYYY+1)
            game_no: the game_no for the current game previous games are [0-game_no-1]
            nme: the team abbr to calculate the SOS for
            wind: optional window to calc for
        OUTPUT:
            sos: the computed sos statistics sum(no_times_faced*(goalsfor-goalsagainst)/no_games)/no_games
        """
        
        sos = 0
        
        #get the details on the game
        q = ("""SELECT * 
                FROM team_log 
                WHERE team_id=\"{0}\"
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                """.format(nme,int(year) + .66,int(year)+1.66))
        games = self.run_query(q)
        games['date_game'] = games['date_game'].astype('datetime64')
        
        gamedate = games.at[game_no,'date_game']

        if game_no>0:
            #list of teams faced to date (and number of times)
            if len(wind) ==1:
                teams_faced = games.loc[games['date_game']<gamedate,'opp_name'].value_counts()
            else:
                teams_faced = games.loc[wind,'opp_name'].value_counts()
        
            #get list of games played in the league that season up until the gameday
            q = ("""SELECT * 
                    FROM team_log 
                    WHERE (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {0}
                    AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {1}
                    """.format(int(year) + .66,int(year)+1.66))
            temp_games = self.run_query(q)
            temp_games['date_game'] = temp_games['date_game'].astype('datetime64')

            #calculate statistics for each team
            goals = temp_games[temp_games['date_game']<gamedate].groupby('team_id').agg([sum,'count'])

            diff = (goals['goals']['sum']-goals['opp_goals']['sum'])/goals['goals']['count'] #calculates metric for all teams to date

            for eachteam in teams_faced.index:
                #get team_abbr faced and 

                q = '''SELECT team_abbr FROM team_list WHERE team_name=\"{0}\" AND CAST(SUBSTR(years_active,6,9) AS INT)>{1}'''.format(eachteam,int(year))
                nme = (self.run_query(q)['team_abbr'].values)[0]
                sos = sos + teams_faced[eachteam]*diff[nme] #updates the SOS
            if len(wind) == 1:
                return sos/game_no
            else:
                return sos/wind.sum()
        else:
            return 0

    def team_stat_gen(self,team_value,year_value,game_value):
        """
            Generates team based statistics for the season (and the last 3 weeks) upto the selected game
            INPUT:
                team_value: The team abbr
                year_value: The season in question where year is YYYY:YYYY+1
                game_value: The game_no for the current game previous games are [0-game_no-1] # must be more than 10
            OUTPUT:
                returns a data series of team stats
        """

        #get the details on the game
        q = ("""SELECT * 
                FROM team_log 
                WHERE team_id=\"{0}\"
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                """.format(team_value,int(year_value) + .66,int(year_value)+1.66))
        game_details = self.run_query(q)
        game_details['date_game'] = game_details['date_game'].astype('datetime64')
        try:
            game_date = game_details.at[game_value,'date_game']
        except:
            print(game_details,team_value,year_value,game_value)
            
        rest_days = game_date-game_details.at[game_value-1,'date_game']

        #team stats up to this point of the season (basic stats)
        cum_total = game_details.loc[game_details.index<game_value,['goals','opp_goals','shots','shots_against']].sum()
        games = (game_details.loc[game_details.index<game_value,'game_outcome']=='W').count() 
        wins = (game_details.loc[game_details.index<game_value,'game_outcome']=='W').sum()
        losses = (game_details.loc[game_details.index<game_value,'game_outcome']=='L').sum()
        ties = (game_details.loc[game_details.index<game_value,'game_outcome']=='T').sum()
        otl = ((game_details.loc[game_details.index<game_value,'game_outcome']=='L')&(game_details['overtimes'].notnull())).sum()
        points = wins*2+ties+otl
        points_pct = np.round(points/(2*games),3)
        #SOS/SRS deal with the strength of schedule
        sos = np.round(self.sos_calc(year_value,game_value,team_value),3) #strength of schedule higher is tougher
        srs = np.round((cum_total['goals']-cum_total['opp_goals'])/games+sos,3) #simple rating system
        cum_total = game_details.loc[game_details.index<game_value,['goals','opp_goals','shots','shots_against']].sum()/game_value
        basic_stats = [games,wins,losses,ties,otl,points,points_pct,srs,sos]
        basic_stats.extend(cum_total)

        #team stats last 3 weeks (basic stats) format rSTAT where r==recent
        window = (game_details['date_game']<game_date)&(game_details['date_game']>(game_date-timedelta(21))) #window == contests in last three weeks
        rec_game_details = game_details.loc[window]
        rgames = (rec_game_details['game_outcome']=='W').count() 
        rwins = (rec_game_details['game_outcome']=='W').sum()
        rlosses = (rec_game_details['game_outcome']=='L').sum()
        rties = (rec_game_details['game_outcome']=='T').sum()
        rotl = ((rec_game_details['game_outcome']=='L')&(rec_game_details['overtimes'].notnull())).sum()
        rpoints = rwins*2+rties+rotl
        rpoints_pct = np.round(rpoints/(2*rgames),3)
        rcumum = rec_game_details[['goals','opp_goals','shots','shots_against']].sum()
        sos_rec = self.sos_calc(year_value,game_value,team_value,window) #strength of schedule higher is tougher
        srs_rec = (rcumum['goals']-rcumum['opp_goals'])/rgames+sos_rec #simple rating system
        rcumum_total = rcumum/rgames
        recent_stats = [rest_days.days,rgames,rwins,rlosses,rties,rotl,rpoints,rpoints_pct,srs_rec,sos_rec]
        recent_stats.extend(list(rcumum_total))

        #now put these arrays into a Series
        labels = ['total_games','wins','loses','ties','otl','points','point_pct','srs','sos','ave_goals','ave_oppgoals','ave_shots','ave_oppshots','rest_days','recent_games','recent_wins','recent_loses','recent_ties','recent_otl','recent_points','recent_point_pct','recent_srs','recent_sos','recent_ave_goals','recent_ave_oppgoals','recent_ave_shots','recent_ave_oppshots']
        all_stats = basic_stats+recent_stats
        return pd.Series(all_stats,labels)
        
    def standings(self):
        """
            Generates a pretty table of the home and opposing team stats dataframes
            INPUT:
                hometeamstats (DataFrame)
                oppteamstats (DataFrame)
            OUTPUT:
                combinedDataFrame (DataFrame)
        """
        stats = pd.concat((self.hometeamstats,self.oppteamstats),axis=1)
        stats.columns = [self.team_name,self.opp_name]
        statst = stats.transpose().iloc[:,:9]
        statst.columns = ['Games', 'Wins','Loses','Ties','OTL','Points','Point %','SRS','SOS']
        return statst.reset_index().rename(columns={'index':'Team'})

    def last_five(self):
        """
            Finds the results of the last 5 games between these teams over the last two seasons (this season and last season)
            INPUT:
                team_value (str): The team abbr
                year_value (int): The season in question where year is YYYY:YYYY+1
                game_value (int): The game_no for the current game previous games are [0-game_no-1] # must be more than 10
                opp_name (str): the opposition name
            OUTPUT:
                (dataframe): a dataframe of the (upto) last five contests

        """
        q = ("""SELECT *
                FROM team_log 
                WHERE team_id=\"{0}\" 
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) < {2}
                AND opp_name=\"{3}\"""".format(self.team_value,int(self.year_value)-1 + .66,int(self.year_value)+1.66,self.opp_name))
        past_games = self.run_query(q)
        last_5 = past_games[past_games['date_game']<self.game_date][-5:][['team_id','date_game','game_location','opp_name','goals',
                                                                    'opp_goals','game_outcome','overtimes','shots','shots_against'
                                                                    ]]
        last_5['game_outcome'] =last_5['game_outcome'].replace({'W':'Win','L':'Loss','T':'Tie'})
        last_5['game_location'] = last_5['game_location'].replace({None:'','@':'@'})
        last_5['overtimes'] =last_5['overtimes'].fillna('')
        last_5['host'] = self.team_name
        last_5.loc[last_5['game_location']=='@','host'] = self.opp_name
        l5s = last_5[['host','date_game','goals','opp_goals','game_outcome','overtimes','shots','shots_against']].copy()
        l5s.columns = ['Host','Date','Goals','Opp. Goals','Outcome','OT?','Shots','Opp. Shots']
        return l5s

    def run_query(self,q):
        """Polls the database"""
        with sqlite3.connect('assests/hockey_data_goalies.db') as conn:
            x = pd.read_sql(q,conn)
        return x

class goalies:
    """
        This class generates a variety of statistics for the goalies of the given team for the/year/game_no

        attributes:
            team_value (str) - the team abbr
            year_value (int) - the year in question (YYYY)-(YYYY+1)
            game_no (int) - game number for the team where game 1 is the second game of the season
            game_date (str) - the date of the game
            team_name (str) - note this is the full team name
            roster(dataframe) - a dataframe of all the goalies who played for that team

        methods:
            fill_roster() - calls all the players who have played for the team this year and returns a dataframe of their ids
            risk() - uses a random forest model to calculate the injury risk
            riskfunc() - calculates a risk factor based on the ML probability and the baseline risk
            run_query() - used to poll the database
            
    """
    
    def __init__(self,*argv):
        #check if correct number of args entered
        if len(argv)==3:
            self.team_value = argv[0]
            self.year_value = argv[1]
            self.game_date = argv[2]
        else:
            raise ValueError('Wrong number of input arguments.  Please use either three.')
        self.roster =self.fill_roster() #get list of goalies and their stats
        #now add risk to roster
        self.roster = self.roster.append(self.risk(),ignore_index=True)
        
    def fill_roster(self):
        """
        call up all the players who played for that team this year
        return a dataframe and their ids and their stats (up to the baysian estimation of their impact)
        computed by mapping the prior dist.  to posterior using their saves/goals allowed to date, then 
        running a quick monte carlo on the season data

        INPUT:
            self.team_value (str) - the team abbr
            self.date_game (str) - the date of the game under prediction
            self.year_value (int) - the year of the season under examination
        OUTPUT:
            a dataframe of their stats
        """
        
        #Get all the stats from the database
        q = ("""WITH goalies as 
                (SELECT player_id,
                        SUM(goals_against) GA,
                        SUM(saves) SAVES,
                        SUM(CAST(SUBSTR(time_on_ice,1,2) AS INT)) TOI,
                        ROUND(1-CAST(SUM(goals_against) AS FLOAT)/CAST(SUM(saves)+ SUM(goals_against) as FLOAT),3) SPCT
                FROM player_log pl
                WHERE team_id=\"{0}\"
                AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
                AND date_game < \"{2}\"
                GROUP BY player_id)
                
                SELECT pl.*, g.GA, g.SAVES, g.SPCT, g.TOI
                FROM goalies g
                LEFT JOIN player_list pl ON pl.unique_id=g.player_id""".format(self.team_value,int(self.year_value) + .66,self.game_date))
        active_players = self.run_query(q)
        active_players_T = active_players.transpose()
        active_players_T.columns = active_players_T.loc['player']
        active_players_T.drop(['unique_id','player','total_games'],inplace=True)
        active_players_T = active_players_T.iloc[2:,:]
        active_players_T.index = ['Height(cm)','Weight(kg)','Goals Allowed','Saves','SV%','Minutes']
        active_players_T.reset_index(inplace=True)
        active_players_T = active_players_T.rename(columns={'index':"Stat"})

        #now run the baysian inference and a montecarlo of 5000 games to determine their 
        #impact had they played all the games
        q = """SELECT *
        FROM team_log
        WHERE (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
        AND date_game < \"{2}\"
        AND team_id ="{0}"
        """.format(self.team_value,int(self.year_value)+.66,self.game_date)
        pregames = self.run_query(q)
        no_games = pregames.shape[0]
        games_won = (pregames['game_outcome']=='W').sum()
        mc_size = 5000
        tot_mc = int(mc_size/no_games)
        goalz = ['Goal Allowed per G.']
        winz = ['Win Delta']

        #for each layer use their estimated save percentage distribution to run the monte carlo
        #to estimate 1) +/- goals allowed per game 2)number of wins (relative to the star)
        for each in active_players.index:
            result = 0
            wins = 0
            for x in range(tot_mc):
                result += sum(pregames['shots_against']*(1-stats.distributions.beta.rvs(231.14+active_players.loc[each,'SAVES'],24.2+active_players.loc[each,'GA'],0,1,no_games))-pregames['opp_goals'])
                wins += sum(np.round(pregames['shots_against']*(1-stats.distributions.beta.rvs(231.14+active_players.loc[each,'SAVES'],24.2+active_players.loc[each,'GA'],0,1,no_games)),0)<pregames['goals'])
            goalz.append(np.round(result/mc_size,2))
            winz.append(int(np.round((wins/tot_mc)-games_won,0)))
        
        winz = [i-max(winz[1:]) if type(i) == int else i for i in winz]
        #now add to the dataframe and return
        active_players_T = active_players_T.append(dict(zip(active_players_T.columns,goalz)),ignore_index=True)
        active_players_T = active_players_T.append(dict(zip(active_players_T.columns,winz)),ignore_index=True)

        return active_players_T

    def risk(self):
        """
        Calculate the increased risk due to known risk factors (age, minutes played, prior injuries) run through random_forest model
        INPUTS:
            Dataframe of player features
            Previous random forest model
        OUTPUTS:
            risk_factor (float) for each player
        """
        #load models... random forest and the pipeline
        ran_for = load('assests/ranforest_regression.joblib')
        pipe = load('assests/pipeline.joblib')

        #get unique ids (unfortunately, not saved in the roster)
        q = ("""SELECT * 
            FROM player_log 
            WHERE team_id=\"{0}\"
            AND (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
            AND date_game < \"{2}\"
            GROUP BY player_id
            """.format(self.team_value,int(self.year_value) + .66,self.game_date))
        ids = self.run_query(q)

        #now generate data for season for each id
        prodf = pd.DataFrame(columns=['player_id','team_id','opp_id','date_game','age','rest_days','min_season',
                                        'shots_against','save_pct','min3W','sa3W','svepct3W','future_save_pct','injured'])
        row = 0
        #for each player
        for each_id in ids['player_id']:
            print(each_id)
            #load the games they've played this season
            q = ("""SELECT * 
            FROM player_log 
            WHERE (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {0}
            AND date_game < \"{1}\"
            AND player_id = \"{2}\"
            """.format(int(self.year_value) + .66,self.game_date,each_id))
            season_logs = self.run_query(q)
            #massage the data to get the right format
            season_logs['date_game'] = season_logs['date_game'].astype('datetime64') #convert to datetime
            season_logs['time_on_ice'] = season_logs['time_on_ice'].str.extract(r'(\d*)\:\d*')[0].astype(int)+season_logs['time_on_ice'].str.extract(r'\d*\:(\d*)')[0].astype(int)/60
            
            #for the last season (this looks like a loop, but it's only getting at the last season)
            for r,game in season_logs[-1:].iterrows():
                prodf.loc[row,'player_id'] = season_logs.loc[r,'player_id']
                prodf.loc[row,'team_id'] = season_logs.loc[r,'team_id']
                prodf.loc[row,'opp_id'] = season_logs.loc[r,'opp_id']
                prodf.loc[row,'date_game'] = season_logs.loc[r,'date_game']
                prodf.loc[row,'age'] = season_logs.loc[r,'age']
                try: #if only one game this season, then set equal to 0 when it fails
                    prodf.loc[row,'rest_days'] = (season_logs.loc[r,'date_game']-season_logs.loc[r-1,'date_game']).days
                    prodf.loc[row,'min_season'] = season_logs.loc[:(r-1),'time_on_ice'].sum()
                    prodf.loc[row,'shots_against'] = season_logs.loc[:(r-1),'shots_against'].sum()
                    prodf.loc[row,'save_pct'] = np.round(season_logs.loc[:(r-1),'saves'].sum()/season_logs.loc[:(r-1),'shots_against'].sum(),3)
                    window = (season_logs.loc[r,'date_game']>season_logs['date_game'])&(season_logs['date_game']>(season_logs.loc[r,'date_game']-timedelta(21)))
                    prodf.loc[row,'min3W'] = season_logs.loc[window,'time_on_ice'].sum()
                    prodf.loc[row,'sa3W'] = season_logs.loc[window ,'shots_against'].sum()
                    prodf.loc[row,'svepct3W'] = season_logs.loc[window,'saves'].sum()/season_logs.loc[window,'shots_against'].sum()
                    prodf.loc[row,'future_save_pct'] = np.round(season_logs.loc[r,'saves'].sum()/season_logs.loc[r,'shots_against'].sum(),3)
                    prodf.loc[row,'injured'] = season_logs.loc[r,'injured']    
                    prodf.loc[row,'pre_inj'] = season_logs.loc[r,'pre_inj']
                except:
                    prodf.loc[row,'rest_days'] = 30
                    prodf.loc[row,'min_season'] = 0
                    prodf.loc[row,'shots_against'] = 0
                    prodf.loc[row,'save_pct'] = .905 #league average
                    #window = (season_logs.loc[r,'date_game']>season_logs['date_game'])&(season_logs['date_game']>(season_logs.loc[r,'date_game']-timedelta(21)))
                    prodf.loc[row,'min3W'] = 0
                    prodf.loc[row,'sa3W'] = 0
                    prodf.loc[row,'svepct3W'] = .905
                    prodf.loc[row,'future_save_pct'] = np.round(season_logs.loc[r,'saves'].sum()/season_logs.loc[r,'shots_against'].sum(),3)
                    prodf.loc[row,'injured'] = season_logs.loc[r,'injured']    
                    prodf.loc[row,'pre_inj'] = season_logs.loc[r,'pre_inj']
            row+=1 #counter for each player
        #fit for each player
        columns = ['age','min_season','rest_days','shots_against','save_pct','min3W','sa3W','svepct3W','pre_inj']
        probs = ran_for.predict_proba(pipe.fit_transform(prodf[columns]))[:,1]
        #the above generates a probability, this is converted to risk by using the precision and the baseline in the function risk function
        data = ['Injury Risk Factor']
        data.extend(self.riskfunc(probs))
        new_row =  dict(zip(self.roster.columns,data))
        return new_row

    def riskfunc(self,x):
        """
        Estimate the increased risk factor by player based on the probability.
        The risk factor is calculated based on the precision of the model / the baseline probability.
        That is among the population (tp and fp) left above this probability level, what's the ratio of injured/total population
        compared with the baseline of 1%
        INPUT:
            x(float) - the probability from 0 to 1
        OUTPUT:
            risk factor(float) 
        """
        y = x**3+0.37*(x**2)-0.2572*x+0.0118
        return np.round(10**y,1)

    def run_query(self,q):
        """Polls the database"""
        with sqlite3.connect('assests/hockey_data_goalies.db') as conn:
            x = pd.read_sql(q,conn)
        return x