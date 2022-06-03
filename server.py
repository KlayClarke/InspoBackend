import os
import boto3
import psycopg2
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from firebase_admin import credentials, firestore, initialize_app, storage
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()


POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")

# to use a service account / initalize firebase credentials
cred = credentials.Certificate(
    "vstore-352120-firebase-adminsdk-8p6ee-4254d42f1c.json")
initialize_app(cred, {"storageBucket": FIREBASE_STORAGE_BUCKET})


# upload image to firebase storage to test func
file = "swiftplaygrounds.jpeg"
bucket = storage.bucket()
blob = bucket.blob(file)
blob.upload_from_filename(file)


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
    videos_list = []
    for video in videos:
        videos_list.append(video.to_dict())
        return (f"I am running with {videos_list[0]}")


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


# @app.post('/videos', status_code=201)
# async def add_video(file: UploadFile):
#     # upload file to AWS S3
#     s3 = boto3.resource("s3", aws_access_key_id=AWS_ACCESS_KEY_ID,
#                         aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#     bucket = s3.Bucket(S3_BUCKET_NAME)
#     bucket.upload_fileobj(file.file, file.filename,
#                           ExtraArgs={"ACL": "public-read"})
#     uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
#     # store url in postgres database
#     # connect to database
#     conn = psycopg2.connect(
#         database=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
#     )
#     cur = conn.cursor()
#     cur.execute(
#         f"INSERT INTO videos (video_title, video_url) VALUES ('{file.filename}', '{uploaded_file_url}')"

#     )
#     conn.commit()
#     cur.close()
#     conn.close()


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
