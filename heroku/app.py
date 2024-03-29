import os
import psycopg2
from flask import Flask, jsonify, render_template, request, redirect
from sqlalchemy import create_engine
import pandas as pd

# postgres login credentials and DB location
from sql_config import pw
from sql_config import user
db_loc = 'localhost:5432'
db_name = 'CoronaVirus'

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Database Setup
#################################################

from flask_sqlalchemy import SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '') or "sqlite:///db.sqlite"

# Remove tracking modifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

from .models import covid19, 

#################################################
# Flask Routes
#################################################

# Query all coronavirus data
# create route that renders index.html template
@app.route("/")
def home():
    return render_template("index.html")

@app.route('/dataCovid19')
def sendDataCovid19():
    # engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    engine = create_engine("sqlite:///Datasets/Covid19_20200403.sqlite")
    connection = engine.connect()
    
    df_covid19 = pd.read_sql("SELECT * FROM covid19", connection)
    return df_covid19.to_json(orient='records')








# # Query the database and send the jsonified results
# @app.route("/send", methods=["GET", "POST"])
# def send():
#     if request.method == "POST":
#         name = request.form["petName"]
#         lat = request.form["petLat"]
#         lon = request.form["petLon"]

#         pet = Pet(name=name, lat=lat, lon=lon)
#         db.session.add(pet)
#         db.session.commit()
#         return redirect("/", code=302)

#     return render_template("form.html")


# @app.route("/api/pals")
# def pals():
#     results = db.session.query(Pet.name, Pet.lat, Pet.lon).all()

#     hover_text = [result[0] for result in results]
#     lat = [result[1] for result in results]
#     lon = [result[2] for result in results]

#     pet_data = [{
#         "type": "scattergeo",
#         "locationmode": "USA-states",
#         "lat": lat,
#         "lon": lon,
#         "text": hover_text,
#         "hoverinfo": "text",
#         "marker": {
#             "size": 50,
#             "line": {
#                 "color": "rgb(8,8,8)",
#                 "width": 1
#             },
#         }
#     }]

#     return jsonify(pet_data)













# Query latest coronavirus count, exclude zero data or data without coordinates
@app.route('/dataCovid19Latest')
def sendLatestCovid19():
    # engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    connection = engine.connect()
    query = f'''SELECT admin2, province_state, country_region,
        date, cases, death, latitude, longitude
        FROM covid19
        WHERE date = (SELECT MAX(date) FROM covid19)
        AND ((cases + death) > 0)
        AND NOT (latitude = 0 AND longitude = 0)
        '''
    df = pd.read_sql(query, connection)
    return df.to_json(orient='records')

# Query Latest Covid-19 data along with country info for scatter plot
@app.route('/dataLatestInfo')
def mergeMetaData():
    engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    connection = engine.connect()
    query = f'''
        SELECT c.code,
            c19.country_region, c19.date, c19.cases, c19.death,
            p.population_2020 as population, p.med_age,
            g.gdp_2019_billions_usd*1e9/p.population_2020 as gdp,
            h.exp_pct_gdp_2016 as health_exp
        FROM covid19 as c19
        LEFT JOIN countries as c
            ON c19.country_region = c.covid19_country
        LEFT JOIN global_population as p
            on p.country = c.pop_country
        LEFT JOIN global_gdp as g
            on g.country = c.gdp_country
        LEFT JOIN health_exp_gdp as h
            on h.country = c.hexp_country
        WHERE c19.date = (SELECT MAX(date) FROM covid19)
        AND ((c19.cases + c19.death) > 0)
        AND c19.admin2 IS NULL
        AND c19.province_state IS NULL
        '''
    df = pd.read_sql(query, connection)
    return df.to_json(orient='records')

#  query country data
@app.route('/dataByCountry')
def queryCountryDaily():
    engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    connection = engine.connect()
    query = f'''
        SELECT country_region, date, cases, death
        FROM covid19 as c19
        WHERE admin2 IS NULL AND province_state IS NULL
    '''
    df = pd.read_sql(query, connection)
    return df.to_json(orient='records')

# Query Countries with no Reported Cases
@app.route('/countryNoCase')
def queryZeroCase():
    engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    connection = engine.connect()
    query = f'''
        SELECT c.code, c.iso_country, p.population_2020 as population, c.latitude, c.longitude
        FROM countries as c
        LEFT JOIN global_population as p
            on p.country = c.pop_country
        WHERE c.covid19_country IS NULL
        '''
    df = pd.read_sql(query, connection)
    return df.to_json(orient='records')

#  query states data
@app.route('/dataByStates')
def queryStatesDaily():
    engine = create_engine(f"postgresql+psycopg2://{user}:{pw}@{db_loc}/{db_name}")
    connection = engine.connect()
    query = f'''
        SELECT province_state, date, cases, death
        FROM covid19
        WHERE admin2 IS NULL AND province_state IS NOT NULL AND country_region = 'US'
    '''
    df = pd.read_sql(query, connection)
    return df.to_json(orient='records')

#################################################
# Run the application
#################################################
if __name__ == '__main__':
    app.run(debug=True)
