from sqlalchemy import MetaData
from sqlalchemy import Table, Column, Integer, String, Float, text
from sqlalchemy import create_engine
import pandas as pd
from uuid import uuid4

data_path = "/home/hasyim/Bootcamp_AI/capston/Capston3/chatbot/data/raw/imdb_top_1000.csv"
df = pd.read_csv(data_path)

df=df.replace({'Released_Year': 'PG'}, None)

df['Gross'] = df['Gross'].str.replace(',', '', regex=True)

df_clean = df.drop(columns="Overview")

df_clean[['Released_Year','Gross']] = df_clean[['Released_Year','Gross']].apply(pd.to_numeric)

df_clean['film_id'] = [str(uuid4()) for _ in range(len(df_clean['Series_Title']))]

engine = create_engine('sqlite:////home/hasyim/Bootcamp_AI/capston/Capston3/chatbot/data/process/IMDB_FILM_capston3.db')

with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS FILM_TABEL"))
    
metadata_obj = MetaData()

FILM = Table(
    "FILM_TABEL",
    metadata_obj,
    Column("film_id", String, primary_key=True, default=lambda: str(uuid4())),
    Column("Series_Title", String, nullable=False),
    Column("Released_Year", Float),
    Column("Certificate", String),
    Column("Runtime", String),
    Column("Genre", String),
    Column("IMDB_Rating", Float),
    Column("Meta_score", Float),
    Column("Director", String),
    Column("Star1", String),
    Column("Star2", String),
    Column("Star3", String),
    Column("Star4", String),
    Column("No_of_Votes", Integer),
    Column("Gross", Float),
    Column("Poster_Link", String),
    extend_existing=True
)

df_clean.to_sql(
    name='FILM_TABEL',
    con=engine,
    if_exists='append',
    index=False
)