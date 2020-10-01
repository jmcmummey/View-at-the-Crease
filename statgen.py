import pandas as pd
import numpy as np
import scipy.stats as stats
import sqlite3
from datetime import datetime as dt, timedelta
from dateutil.relativedelta import *
import re

class teamstats:

    """
        This object generates a variety of statistics for the given team/year/game_no
        attributes:
    
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
        Gets the opposing team information
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
        INPUT:
            year: the current season (YYYY-YYYY+1)
            game_no: the game_no for the current game previous games are [0-game_no-1]
            nme: the team abbr to calculate the SOS for
            wind: optional window to calc for
            RETURN:
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
                #get team_abbr

                q = '''SELECT team_abbr FROM team_list WHERE team_name=\"{0}\" AND CAST(SUBSTR(years_active,6,9) AS INT)>{1}'''.format(eachteam,int(year))
                nme = (self.run_query(q)['team_abbr'].values)[0]
                sos = sos + teams_faced[eachteam]*diff[nme]
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
        sos = np.round(self.sos_calc(year_value,game_value,team_value),3) #strength of schedule higher is tougher
        srs = np.round((cum_total['goals']-cum_total['opp_goals'])/games+sos,3) #simple rating system
        cum_total = game_details.loc[game_details.index<game_value,['goals','opp_goals','shots','shots_against']].sum()/game_value
        basic_stats = [games,wins,losses,ties,otl,points,points_pct,srs,sos]
        basic_stats.extend(cum_total)

        #team stats last 3 weeks (basic stats)
        window = (game_details['date_game']<game_date)&(game_details['date_game']>(game_date-timedelta(21)))
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

        labels = ['total_games','wins','loses','ties','otl','points','point_pct','srs','sos','ave_goals','ave_oppgoals','ave_shots','ave_oppshots','rest_days','recent_games','recent_wins','recent_loses','recent_ties','recent_otl','recent_points','recent_point_pct','recent_srs','recent_sos','recent_ave_goals','recent_ave_oppgoals','recent_ave_shots','recent_ave_oppshots']
        all_stats = basic_stats+recent_stats
        return pd.Series(all_stats,labels)
        
    def standings(self):
        """
            Generates a pretty table of the home and opposing team stats
        """
        stats = pd.concat((self.hometeamstats,self.oppteamstats),axis=1)
        stats.columns = [self.team_name,self.opp_name]
        statst = stats.transpose().iloc[:,:9]
        statst.columns = ['Games', 'Wins','Loses','Ties','OTL','Points','Point %','SRS','SOS']
        return statst.reset_index().rename(columns={'index':'Team'})

    def last_five(self):
        """
        Finds the results of the last 5 games between these teams
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
        with sqlite3.connect('C:\\Users\\jesse\\Documents\\Projects\\takeaseat\\assests\\hockey_data_goalies.db') as conn:
            x = pd.read_sql(q,conn)
        return x

class goalies:
    """
        This object generates a variety of statistics for the goalies of the given team for the/year/game_no
        attributes:
    """
    
    def __init__(self,*argv):
        #check if correct number of args entered
        if len(argv)==3:
            self.team_value = argv[0]
            self.year_value = argv[1]
            self.game_date = argv[2]
        else:
            raise ValueError('Wrong number of input arguments.  Please use either three.')
        self.roster = self.fill_roster() #get list of goalies and their stats
        
    def fill_roster(self):
    #call up all the players who played for that team this year

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
        active_players_T.drop(['unique_id','player'],inplace=True)
        active_players_T = active_players_T.iloc[2:,:]
        active_players_T.index = ['Height(cm)','Weight(kg)','Total Games','Goals Allowed','Saves','SV%','Minutes']
        active_players_T.reset_index(inplace=True)
        active_players_T = active_players_T.rename(columns={'index':"Stat"})

        #now run the baysian inference
        q = """SELECT *
        FROM team_log
        WHERE (CAST(SUBSTR(date_game,1,4) AS FLOAT)+CAST(SUBSTR(date_game,6,7) AS FLOAT)/12) > {1}
        AND date_game < \"{2}\"
        AND team_id ="{0}"
        """.format(self.team_value,int(self.year_value)+.66,self.game_date)
        pregames = self.run_query(q)
        no_games = pregames.shape[0]
        games_won = (pregames['game_outcome']=='W').sum()
        mc_size = 10000
        tot_mc = int(mc_size/no_games)
        goalz = ['Goals per Game +/-']
        winz = ['Games Won +/-']

        for each in active_players.index:
            result = 0
            wins = 0
            for x in range(tot_mc):
                result += sum(pregames['shots_against']*(1-stats.distributions.beta.rvs(231.14+active_players.loc[each,'SAVES'],24.2+active_players.loc[each,'GA'],0,1,no_games))-pregames['opp_goals'])
                wins += sum(np.round(pregames['shots_against']*(1-stats.distributions.beta.rvs(231.14+active_players.loc[each,'SAVES'],24.2+active_players.loc[each,'GA'],0,1,no_games)),0)<pregames['goals'])
            goalz.append(np.round(result/mc_size,2))
            winz.append(np.round((wins/tot_mc)-games_won,0))

        active_players_T = active_players_T.append(dict(zip(active_players_T.columns,goalz)),ignore_index=True)
        active_players_T = active_players_T.append(dict(zip(active_players_T.columns,winz)),ignore_index=True)


        return active_players_T

    def run_query(self,q):
        """Polls the database"""
        with sqlite3.connect('C:\\Users\\jesse\\Documents\\Projects\\takeaseat\\assests\\hockey_data_goalies.db') as conn:
            x = pd.read_sql(q,conn)
        return x