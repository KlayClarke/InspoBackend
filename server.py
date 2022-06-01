import os
import boto3
import psycopg2
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()


POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")


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
    # upload file to AWS S3
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(S3_BUCKET_NAME)
    bucket.upload_fileobj(file.file, file.filename,
                          ExtraArgs={"ACL": "public-read"})
    uploaded_file_url = f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{file.filename}"
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
    conn.close()


if __name__ == "__main__":
    uvicorn.run(app, host='localhost', port="8000", reload=False)
