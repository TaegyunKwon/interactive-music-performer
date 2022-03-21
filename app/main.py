import asyncio
from http import HTTPStatus

from fastapi import BackgroundTasks, Depends, FastAPI
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .core.utils import (
    all_stop_playing,
    play_piece_to_outport,
    close_stream,
    load_piece_for_interactive_performance,
    start_interactive_performance,
)
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

# login_provider = UsernamePasswordProvider(
#     admin_model=Admin, login_logo_url="https://preview.tabler.io/static/logo.svg"
# )

app = FastAPI(title="Score Follower For Interactive Performance")
# app.mount("/admin", admin_app)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/test", tags=["Test"])
def test():
    print("test API for synchronous request")
    return {"hello": "world"}


@app.get("/async-test", tags=["Test"])
async def async_test():
    print("test API for asynchronous request - sleep for 0.1 sec...")
    await asyncio.sleep(0.1)
    return {"async hello": "world"}


@app.get(
    "/pieces/{piece_id}/play", status_code=HTTPStatus.ACCEPTED, tags=["Interactive API"]
)
def play_piece(
    piece_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    db_piece = crud.get_piece_by_id(db, piece_id=piece_id)
    background_tasks.add_task(play_piece_to_outport, piece=db_piece)
    return {"response": f"playing title({db_piece.title}) on the background"}


@app.get(
    "/pieces/{piece_id}/load",
    tags=["Interactive API"],
)
def load_piece(piece_id: int, db: Session = Depends(get_db)):
    piece = crud.get_piece_by_id(db, piece_id=piece_id)
    load_piece_for_interactive_performance(piece=piece)
    return {"response": f"loading title({piece.title})"}


@app.get(
    "/pieces/{piece_id}/perform",
    status_code=HTTPStatus.ACCEPTED,
    tags=["Interactive API"],
)
def perform_piece(
    piece_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    piece = crud.get_piece_by_id(db, piece_id=piece_id)
    background_tasks.add_task(start_interactive_performance, piece=piece)
    return {"response": f"following title({piece.title})"}


@app.get("/stop", tags=["Interactive API"])
def stop_all_tasks():
    all_stop_playing()
    close_stream()
    return {"response": "all stop playing & recording"}


@app.post("/pieces", response_model=schemas.Piece, tags=["Basic API"])
def create_piece(piece: schemas.PieceCreate, db: Session = Depends(get_db)):
    return crud.create_piece(db=db, piece=piece)


@app.get("/pieces/", response_model=List[schemas.Piece], tags=["Basic API"])
def read_pieces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_pieces(db, skip=skip, limit=limit)


@app.get("/pieces/{piece_id}", response_model=schemas.Piece, tags=["Basic API"])
def read_piece(piece_id: int, db: Session = Depends(get_db)):
    db_piece = crud.get_piece_by_id(db, piece_id=piece_id)
    return db_piece


@app.post(
    "/pieces/{piece_id}/schedules/", response_model=schemas.Schedule, tags=["Basic API"]
)
def create_schedule_by_piece(
    piece_id: int, schedule: schemas.ScheduleCreate, db: Session = Depends(get_db)
):
    return crud.create_schedule(db=db, schedule=schedule, piece_id=piece_id)


@app.get("/schedules/", response_model=List[schemas.Schedule], tags=["Basic API"])
def read_schedules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_schedules_by_piece(db, skip=skip, limit=limit)


@app.get(
    "/schedules/{schedule_id}", response_model=schemas.Schedule, tags=["Basic API"]
)
def read_schedule(schedule_id: int, db: Session = Depends(get_db)):
    return crud.get_schedule(db, schedule_id=schedule_id)


@app.post(
    "/pieces/{piece_id}/subpieces/", response_model=schemas.SubPiece, tags=["Basic API"]
)
def create_subpiece_by_piece(
    piece_id: int, subpiece: schemas.SubPieceCreate, db: Session = Depends(get_db)
):
    return crud.create_subpiece(db=db, subpiece=subpiece, piece_id=piece_id)


@app.get("/subpieces/", response_model=List[schemas.SubPiece], tags=["Basic API"])
def read_subpieces(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_subpieces(db, skip=skip, limit=limit)


@app.get(
    "/subpieces/{subpiece_id}", response_model=schemas.SubPiece, tags=["Basic API"]
)
def read_subpiece(subpiece_id: int, db: Session = Depends(get_db)):
    return crud.get_subpiece(db, subpiece_id=subpiece_id)
