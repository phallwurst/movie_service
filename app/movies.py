import gzip
import csv
import os

from typing import Any
from fastapi import APIRouter, UploadFile
from sqlalchemy import select

from app.model import DownloadPayload, MoviesQuery, AddMoviePayload

from app import db

router = APIRouter()


@router.get("/hello")
async def hello():
    return "hello"


async def query_movies(session, payload: MoviesQuery) -> None:
    query = select(db.Movie)

    if payload.movie_name:
        query = query.where(db.Movie.movie_name.ilike(f"%{payload.movie_name}%"))

    if payload.start_year:
        query = query.where(db.Movie.year >= payload.start_year)

    if payload.end_year:
        query = query.where(db.Movie.year <= payload.end_year)

    if payload.genres:
        for genre in payload.genres:
            query = query.where(db.Movie.genres.any(genre))

    if payload.rating:
        try:
            query = query.where(db.Movie.rating >= float(payload.rating))
        except ValueError:
            pass

    query = query.order_by(db.Movie.movie_name.asc())

    return session.scalars(query).all()


@router.post("/search")
async def search(payload: MoviesQuery) -> Any:
    print("Searching movie data...")

    with db.get_db() as session:
        results = await query_movies(session, payload)

    print("Processing results...")

    movies = [
        {
            "movie_name": movie.movie_name,
            "year": movie.year,
            "genres": movie.genres,
            "rating": movie.rating,
        }
        for movie in results
    ]

    print(f"Found {len(movies)} results.")

    return {"results": movies}


@router.post("/download")
async def download(payload: DownloadPayload):
    print("Downloading movie data...")
    print("Retrieving data...")

    with db.get_db() as session:
        movies = await query_movies(session, payload)

    movie_datas = []

    print("Processing data...")

    for movie in movies:
        movie_datas.append({
            "movie_name": movie.movie_name,
            "year": movie.year,
            "genres": movie.genres,
            "rating": movie.rating,
        })

    csv_file_name = f"{payload.file_name}.csv"
    gz_file_name = f"{csv_file_name}.gz"

    print("Writing data to CSV...")

    # Write movie_datas to CSV
    with open(csv_file_name, "w", newline='', encoding='utf-8') as csvfile:
        fieldnames = ["movie_name", "year", "genres", "rating"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for data in movie_datas:
            # Convert genres list back to comma-separated string for CSV
            if isinstance(data["genres"], list):
                data["genres"] = ", ".join(data["genres"])

            writer.writerow(data)

    print("gzipping CSV file...")

    # Gzip the CSV file
    with open(csv_file_name, "rb") as f_in, gzip.open(gz_file_name, "wb") as f_out:
        f_out.writelines(f_in)

    #remove the original CSV file
    try:
        os.remove(csv_file_name)
    except Exception:
        pass

    print("Download complete...")

    return {"message": "Download complete"}


@router.post("/seed")
async def seed(file: UploadFile):
    print("Seeding movie data...")

    spooled_file = file.file
    file_contents = spooled_file.read()

    print("Processing csv...")

    seen_rows = set()
    skip_count = 0
    row_datas = []
    reader = csv.DictReader(file_contents.decode('utf-8').splitlines())

    for row in reader:
        row_tuple = tuple(row.values())

        if row_tuple in seen_rows:
            skip_count += 1
            continue

        seen_rows.add(row_tuple)

        row['genres'] = row.get('genres', '').replace(', ', ',').split(',') if row.get('genres') else []

        try:
            row['rating'] = float(row['rating'])
        except ValueError:
            row['rating'] = None

        if not row.get('year'):
            row['year'] = None

        row_datas.append(row)

    print(f"Inserting movie data...")

    with db.get_db() as session:
        session.bulk_insert_mappings(db.Movie, row_datas)
        session.commit()

    print(f"Seeded {len(row_datas)} rows.")
    print(f"Skipped {skip_count} duplicate rows.")

    return {"message": "Movie data seeded successfully"}


@router.post("/add-movie")
async def add_movie(payload: AddMoviePayload):
    if not all([payload.movie_name, payload.year, payload.genres, payload.rating]):
        return {"error": "All fields are required."}

    try:
        movie_year = int(payload.year)
    except ValueError:
        return {"error": "Year must be a valid integer."}

    try:
        movie_rating = float(payload.rating)
    except ValueError:
        return {"error": "Rating must be a valid number."}

    with db.get_db() as session:
        movie = db.Movie(
            movie_name=payload.movie_name,
            year=movie_year,
            genres=payload.genres,
            rating=movie_rating
        )
        session.add(movie)
        session.commit()

    return {"message": "Movie added successfully"}
