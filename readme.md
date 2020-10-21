<h1>View at the Crease - a 3 Week Insight Project</h1>

<p>This repository contains the data and files composed during my Insight Data Science Fellowship.  The purpose of the project was to develop an analytical dashboard with key performance indicators to inform ice hockey coaches (and potentially fantasy coaches too) when selecting which goaltender to play on any given night.</p>
<p>The project uses an SQLite dashboard of the last 30 years of goaltender data scrapped from a variety of websites included game log data, injury reports and salary information.
The dashboard created using Dash/Plotly and deployed in AWS Elastic Block Store can be found here <a href="http://www.intelligentanalytics.xyz" title="View at the Crease">www.intelligentanalytics.xyz</a></p>

The repository consists of several working folders each outlined below:

<h2>Folder Structure</h2>
<p>
  <ul><li><b>Main Folder:</b>
            <p>The main Python files for the development of the deployed (to AWS EBS) app including:
                <ul>
                    <li>
                       <p><b>application.py:</b> the main DASH application used for updating the dashboard on the local host.</p>
                    </li>
                    <li>
                       <p><b>statgen.py:</b> Python file with classes called in the main application used to generate the real time statistics, for the home and away team as   well as for the goaltenders of the home team, as the coaches interact with the dashboard.                           </p>
                    </li>
                    <li>
                       <p><b>requirements.txt:</b> the requirements document used to track all the modules used within the environment.</p>
                    </li>
                </ul>
            </p>
      </li>
  </ul>
 <ul><li><b>Assets:</b>
            <p>Working files used by the Dashboard:
                <ul>
                    <li>
                       <p><b>hockey_data_goalies.db:</b> the SQlite database which stores the data.</p>
                    </li>
                    <li>
                       <p><b>BootstrappedLogR.joblib:</b> The trained ML logistic regression model</p>
                    </li>
                    <li>
                       <p><b>viewfromthecrease.css:</b> The dashboard .css file</p>
                    </li>
                </ul>
            </p>
      </li>
  </ul>
  <ul><li><b>current AWS EBS Deployment:</b>
            <p>These are the files (originally from the main directory and assets folder) which are now actively deployed on AWS.  They may be out of date with the main                        directory files due to updates in progress, but not yet deployed.</p>
      </li>
  </ul>
   <ul><li><b>Data:</b>
            <p>This directory consists of files used in the collection and aggregation of the data. The data was scrapped from a variety of websites, including <a href="http://www.hockey-reference.com/" title="Hockey Statistics">www.hockey-reference.com/</a> and <a href="http://www.prosportstransactions.com/hockey/index.htm" title="Hockey Injury Data">www.prosportstransactions.com/hockey/index.htm</a> using python requests and beautiful soup.  At the present time the NHL season is over, so while these methods could be deployed to update the database throughout the season, at the current time the database is based on solely historic data.  Some import files include:
                <ul>
                    <li>
                       <p><b>7_DatabaseBuilder-Goalies.ipynb:</b> the main jupyter notebook which takes the scraped data and inserts it into the SQlite database.</p>
                    </li>
                    <li>
                       <p><b>{0-5,8}_VariousNames.ipynb:</b> The files which scrape and process data from a variety of websites.</p>
                    </li>
                </ul>
            </p>
      </li>
  </ul>
   <ul><li><b>Analysis:</b>
            <p>This directory consists of files used in the analysis and modeling of the data.  It includes some work that was done early on in the project (when all the                        positions were considered) as well as other EDA.  Some important files include:
                <ul>
                    <li>
                       <p><b>7_Save Percentage Baysian Analysis.ipynb:</b> The notebook in which the Baysian analysis is first performed</p>
                    </li>
                    <li>
                       <p><b>5_Goalie_Injury_Predictor_Generate_data.ipynb:</b> This notebook uses the database to generate the features for all the goalies in the database that                              are later used to train the ML model. These same features are used for live predictions within the dashboard by the statgen.py module</p>
                    </li>
                    <li>
                       <p><b>10_ML_Injury_Predictor - Log-R.ipynb:</b> the notebook in which the logistic regression is fit to the data to predict injury.</p>
                    </li>
                </ul>
            </p>
      </li>
  </ul>
</p>
