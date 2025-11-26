from typing import Annotated, Optional
from pydantic import BaseModel, Field


class MoviesQuery(BaseModel):
    """
    This class is only served as a base example for query
    Please update this model to best optimize the usecase
    """

    movie_name: Annotated[Optional[str], Field(description="Name of the movie to search for")]
    start_year: Annotated[Optional[str], Field(description="Start year of the movie, inclusive")]
    end_year: Annotated[Optional[str], Field(description="End year of the movie, inclusive")]
    genres: Annotated[Optional[list[str]], Field(description="Genres to include")]
    rating: Annotated[Optional[str], Field(description="Minimum rating of the movie to search for")]


class DownloadPayload(MoviesQuery):
    file_name: Annotated[str, Field(description="Name of the file to create")]


class AddMoviePayload(BaseModel):
    movie_name: Annotated[str, Field(description="Name of the movie")]
    year: Annotated[str, Field(description="Release year of the movie")]
    genres: Annotated[list[str], Field(description="List of genres for the movie")]
    rating: Annotated[str, Field(description="Rating of the movie")]
