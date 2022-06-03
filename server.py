import os
import boto3
import psycopg2
import pyrebase
from random_id import random_id
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from firebase_admin import credentials, firestore, initialize_app, storage as fb_admin_storage
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()


POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
# S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN")
FIRBASE_DATABASE_URL = os.getenv("FIRBASE_DATABASE_URL")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")
FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")

# to use a service account / initalize firebase credentials
cred = credentials.Certificate(
    FIREBASE_SERVICE_ACCOUNT)
initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})

config = {
    "apiKey": FIREBASE_API_KEY,
    "authDomain": FIREBASE_AUTH_DOMAIN,
    "databaseURL": FIRBASE_DATABASE_URL,
    "storageBucket": FIREBASE_STORAGE_BUCKET,
    "serviceAccount": FIREBASE_SERVICE_ACCOUNT
}

firebase = pyrebase.initialize_app(config)


class VideoModel(BaseModel):
    id: int
    video_title: str
    video_url: str


app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def check_status():
    conn = psycopg2.connect(
        database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
    )
    print(conn)


@app.get("/status")
async def check_status():
    return ("Hello, " + POSTGRES_USER)


@app.get("/videos", response_model=List[VideoModel])
async def get_videos():
    # connect to database
    conn = psycopg2.connect(
        database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM videos ORDER BY id DESC")
    rows = cur.fetchall()
    formatted_videos = []
    for row in rows:
        formatted_videos.append(
            VideoModel(id=row[0], video_title=row[1], video_url=row[2])
        )
    cur.close()
    conn.close()
    return formatted_videos


@app.post('/videos', status_code=201)
async def add_video(file: UploadFile):
    # generate random number to save with image upload (prevent naming conflict)
    randomnum = random_id()
    # upload image to firebase storage to test func
    bucket = fb_admin_storage.bucket()
    blob = bucket.blob(f"images/{randomnum}{file.filename}")
    blob.upload_from_file(file.file)
    blob.make_public()
    pyrebase_storage = firebase.storage()
    # get url of image from firebase storage
    uploaded_file_url = pyrebase_storage.child(
        f"images/{randomnum}{file.filename}").get_url('token')
    # store url in postgres database
    # connect to database
    conn = psycopg2.connect(
        database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
    )
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO videos (video_title, video_url) VALUES ('{file.filename}', '{uploaded_file_url}')"
    )
    conn.commit()
    cur.close()
    cur = conn.cursor()
    cur.execute("SELECT * FROM videos ORDER BY id DESC")
    rows = cur.fetchall()
    formatted_videos = []
    for row in rows:
        formatted_videos.append(
            VideoModel(id=row[0], video_title=row[1], video_url=row[2])
        )
    conn.close()
    return formatted_videos


@app.delete('/videos/{id}')
async def delete_video(id: int):
   # connect to database
    conn = psycopg2.connect(
        database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
    )
    cur = conn.cursor()
    cur.execute(f"DELETE FROM videos WHERE id={id}")
    conn.commit()
    cur.close()
    cur = conn.cursor()
    cur.execute("SELECT * FROM videos ORDER BY id DESC")
    rows = cur.fetchall()
    formatted_videos = []
    for row in rows:
        formatted_videos.append(
            VideoModel(id=row[0], video_title=row[1], video_url=row[2])
        )
    conn.close()
    return formatted_videos


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port="8000", reload=False)
