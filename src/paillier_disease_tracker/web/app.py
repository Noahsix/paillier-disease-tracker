from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
import threading
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..client import ClientApplication, DbPreview, DiseaseCountFlow, ValidationReport
from ..config import DEFAULT_DB_PATH, DEFAULT_DISEASES, DEFAULT_KEYS_PATH, DEFAULT_KEY_SIZE
from ..crypto import generate_keypair
from ..keys import load_keypair, save_keypair


@dataclass
class WebState:
    lock: threading.Lock = field(default_factory=threading.Lock)
    app: ClientApplication | None = None
    db_path: Path | None = None
    keys_path: Path | None = None


class ProjectSetupRequest(BaseModel):
    db_path: str = Field(default=str(DEFAULT_DB_PATH))
    keys_path: str = Field(default=str(DEFAULT_KEYS_PATH))
    key_size: int = Field(default=DEFAULT_KEY_SIZE, ge=128)


class ProjectLoadRequest(BaseModel):
    db_path: str = Field(default=str(DEFAULT_DB_PATH))
    keys_path: str = Field(default=str(DEFAULT_KEYS_PATH))


class AddPatientRequest(BaseModel):
    pseudonym: str
    diagnoses: dict[str, int]


class SeedBulkRequest(BaseModel):
    patients: int = Field(default=5000, ge=0)
    seed: int = Field(default=42)
    prefix: str = Field(default="bulk_patient")
    batch_size: int = Field(default=1000, ge=1)


class AddDiseaseRequest(BaseModel):
    name: str


class DiseaseRequest(BaseModel):
    disease: str


class CountRequest(BaseModel):
    disease: str
    include_flow: bool = False


state = WebState()
app = FastAPI(title="Paillier Disease Tracker Web")


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(FileNotFoundError)
async def handle_file_error(request: Request, exc: FileNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(RuntimeError)
async def handle_runtime_error(request: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


def _static_dir() -> Path:
    if hasattr(sys, "_MEIPASS"):
        candidate = Path(sys._MEIPASS) / "paillier_disease_tracker" / "web" / "static"
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parent / "static"


_static_root = _static_dir()
if _static_root.exists():
    app.mount("/static", StaticFiles(directory=_static_root), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    index_path = _static_root / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail="Static index.html not found")
    return FileResponse(index_path)


def _resolve_paths(db_path: str, keys_path: str) -> tuple[Path, Path]:
    db = Path(db_path).expanduser().resolve()
    keys = Path(keys_path).expanduser().resolve()
    return db, keys


def _set_state(app_instance: ClientApplication, db_path: Path, keys_path: Path) -> None:
    state.app = app_instance
    state.db_path = db_path
    state.keys_path = keys_path


def _ensure_app() -> ClientApplication:
    if state.app is None:
        raise HTTPException(status_code=400, detail="Project is not loaded. Run setup or load first.")
    return state.app


def _flow_payload(flow: DiseaseCountFlow) -> dict[str, Any]:
    return {
        "disease": flow.disease,
        "rows": [
            {
                "pseudonym": row.pseudonym,
                "plain_value": row.plain_value,
                "ciphertext": str(row.ciphertext),
            }
            for row in flow.rows
        ],
        "encrypted_homomorphic_result": str(flow.encrypted_homomorphic_result),
        "decrypted_result": flow.decrypted_result,
        "plain_reference": flow.plain_reference,
    }


def _validation_report_payload(report: ValidationReport) -> dict[str, Any]:
    return {
        "results": [
            {
                "disease": result.disease,
                "homomorphic_sum": result.homomorphic_sum,
                "plain_sum": result.plain_sum,
                "homomorphic_count": result.homomorphic_count,
                "plain_count": result.plain_count,
                "is_valid": result.is_valid,
            }
            for result in report.results
        ],
        "total_diseases": report.total_diseases,
        "passed_diseases": report.passed_diseases,
        "all_valid": report.all_valid,
    }


def _db_preview_payload(preview: DbPreview) -> dict[str, Any]:
    return {
        "diseases": preview.diseases,
        "rows": [
            {"pseudonym": row.pseudonym, "diagnoses": row.diagnoses}
            for row in preview.rows
        ],
        "total_patients": preview.total_patients,
        "total_diagnoses": preview.total_diagnoses,
    }


@app.get("/api/config")
def get_config() -> dict[str, Any]:
    return {
        "db_path": str(DEFAULT_DB_PATH),
        "keys_path": str(DEFAULT_KEYS_PATH),
        "key_size": DEFAULT_KEY_SIZE,
        "diseases": list(DEFAULT_DISEASES),
    }


@app.post("/api/project/setup")
def setup_project(request: ProjectSetupRequest) -> dict[str, Any]:
    with state.lock:
        db_path, keys_path = _resolve_paths(request.db_path, request.keys_path)
        public_key, private_key = generate_keypair(request.key_size)
        save_keypair(keys_path, public_key, private_key)

        app_instance = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
        existing_patients = app_instance.repository.total_patients()
        if existing_patients:
            app_instance.repository.clear_patient_data()
        app_instance.repository.reset_catalog(list(DEFAULT_DISEASES))

        _set_state(app_instance, db_path, keys_path)

        return {
            "message": "Setup complete",
            "db_path": str(db_path),
            "keys_path": str(keys_path),
            "existing_patients_cleared": existing_patients,
            "diseases": app_instance.list_diseases(),
            "mapping": app_instance.repository.disease_mapping(),
        }


@app.post("/api/project/load")
def load_project(request: ProjectLoadRequest) -> dict[str, Any]:
    with state.lock:
        db_path, keys_path = _resolve_paths(request.db_path, request.keys_path)
        public_key, private_key = load_keypair(keys_path)
        app_instance = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
        app_instance.initialize_catalog(list(DEFAULT_DISEASES))

        _set_state(app_instance, db_path, keys_path)

        return {
            "message": "Project loaded",
            "db_path": str(db_path),
            "keys_path": str(keys_path),
            "diseases": app_instance.list_diseases(),
            "mapping": app_instance.repository.disease_mapping(),
        }


@app.get("/api/diseases")
def list_diseases() -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        return {
            "diseases": app_instance.list_diseases(),
            "mapping": app_instance.repository.disease_mapping(),
        }


@app.post("/api/diseases/add")
def add_disease(request: AddDiseaseRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Disease name cannot be empty")

        app_instance.add_disease(name)
        return {
            "diseases": app_instance.list_diseases(),
            "mapping": app_instance.repository.disease_mapping(),
        }


@app.post("/api/patients/add")
def add_patient(request: AddPatientRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        pseudonym = request.pseudonym.strip()
        if not pseudonym:
            raise HTTPException(status_code=400, detail="Pseudonym cannot be empty")

        patient_id = app_instance.add_patient(pseudonym, request.diagnoses)
        return {"patient_id": patient_id, "pseudonym": pseudonym}


@app.post("/api/patients/seed-demo")
def seed_demo() -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        inserted = app_instance.seed_demo_data()
        return {"inserted": inserted}


@app.post("/api/patients/seed-bulk")
def seed_bulk(request: SeedBulkRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        inserted = app_instance.seed_bulk_data(
            patient_count=request.patients,
            seed=request.seed,
            pseudonym_prefix=request.prefix,
            batch_size=request.batch_size,
        )
        total = app_instance.repository.total_patients()
        return {"inserted": inserted, "total_patients": total}


@app.post("/api/analytics/count")
def count_disease(request: CountRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        result = app_instance.count_and_sum_disease(request.disease)
        flow = app_instance.build_count_flow(request.disease) if request.include_flow else None

        is_valid = (
            result.decrypted_count == result.plain_count_reference
            and result.decrypted_sum == result.plain_sum_reference
        )

        payload = {
            "disease": result.disease,
            "row_count": result.row_count,
            "encrypted_count": str(result.encrypted_count),
            "encrypted_sum": str(result.encrypted_sum),
            "decrypted_count": result.decrypted_count,
            "decrypted_sum": result.decrypted_sum,
            "plain_count_reference": result.plain_count_reference,
            "plain_sum_reference": result.plain_sum_reference,
            "is_valid": is_valid,
        }

        if flow is not None:
            payload["flow"] = _flow_payload(flow)

        return payload


@app.post("/api/analytics/encrypted-rows")
def encrypted_rows(request: DiseaseRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        rows = app_instance.repository.get_encrypted_rows_for_disease(request.disease)
        return {
            "disease": request.disease,
            "rows": [{"pseudonym": row[0], "ciphertext": str(row[1])} for row in rows],
        }


@app.post("/api/validation/selected")
def validate_selected(request: DiseaseRequest) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        result = app_instance.validate_disease_sum(request.disease)
        return {
            "disease": result.disease,
            "homomorphic_sum": result.homomorphic_sum,
            "plain_sum": result.plain_sum,
            "homomorphic_count": result.homomorphic_count,
            "plain_count": result.plain_count,
            "is_valid": result.is_valid,
        }


@app.post("/api/validation/all")
def validate_all() -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        report = app_instance.validate_all_disease_sums()
        return _validation_report_payload(report)


@app.get("/api/db/preview")
def db_preview(limit: int = Query(default=50, ge=1, le=500)) -> dict[str, Any]:
    with state.lock:
        app_instance = _ensure_app()
        preview = app_instance.build_db_preview(limit=limit)
        return _db_preview_payload(preview)
