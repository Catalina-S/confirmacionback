from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir solo este dominio
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados
)

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
patients_collection = db[COLLECTION_PATIENTS]
medication_requests_collection = db[COLLECTION_MEDICATION_REQUESTS]

# Inicializacion de la API
app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes (cambiar en producción)
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todas las cabeceras
)

# ---------------------------------------------------------------------
# Funciones de ayuda (CRUD para Patient y MedicationRequest)
# ---------------------------------------------------------------------
# Estas funciones ahora incluyen la interacción con MongoDB

def GetPatientById(patient_id: str):
    """
    Obtiene un paciente por su ID de MongoDB.
    """
    try:
        patient_object_id = ObjectId(patient_id)
    except Exception:
        return "error", "Invalid Patient ID format"  # Devuelve un mensaje de error claro

    patient = patients_collection.find_one({"_id": patient_object_id})
    if patient:
        patient["id"] = str(patient["_id"])
        del patient["_id"]
        return "success", patient
    else:
        return "notFound", None



def GetPatientByIdentifier(system: str, value: str):
    """
    Obtiene un paciente por su identificador.
    """
    patient = patients_collection.find_one({"identifier.system": system, "identifier.value": value})
    if patient:
        patient["id"] = str(patient["_id"])
        del patient["_id"]
        return "success", patient
    else:
        return "notFound", None



def WritePatient(patient_data: dict):
    """
    Crea un nuevo paciente.
    """
    # TODO:  Validar el `patient_data` según el esquema FHIR de Patient
    #       Esto es crucial para la integridad de los datos.
    #       Aquí iría la lógica de validación (puedes usar fhirpy o jsonschema)

    # Por simplicidad, aquí solo verificamos que el identificador sea único.
    if patients_collection.find_one({"identifier.system": patient_data.get("identifier", {}).get("system"),
                                    "identifier.value": patient_data.get("identifier", {}).get("value")}):
        return "error", "Patient with this identifier already exists"

    result = patients_collection.insert_one(patient_data)
    if result.inserted_id:
        return "success", str(result.inserted_id)
    else:
        return "error", "Failed to create patient"



def GetMedicationRequestById(medication_request_id: str):
    """
    Obtiene una solicitud de medicación por su ID.
    """
    try:
        medication_request_object_id = ObjectId(medication_request_id)
    except Exception:
        return "error", "Invalid MedicationRequest ID format"

    medication_request = medication_requests_collection.find_one({"_id": medication_request_object_id})
    if medication_request:
        medication_request["id"] = str(medication_request["_id"])
        del medication_request["_id"]
        return "success", medication_request
    else:
        return "notFound", None



def WriteMedicationRequest(medication_request_data: dict):
    """
    Crea una nueva solicitud de medicación.
    """
    # TODO: Validar el `medication_request_data` contra el esquema FHIR.
    #  Agregar validacion aqui
    result = medication_requests_collection.insert_one(medication_request_data)
    if result.inserted_id:
        return "success", str(result.inserted_id)
    else:
        return "error", "Failed to create MedicationRequest"


# ---------------------------------------------------------------------
# Rutas de la API (Endpoints)
# ---------------------------------------------------------------------

@app.get("/")
async def root():
    """
    Raíz de la API.  Puede devolver un mensaje de bienvenida o la documentación.
    """
    return {"message": "Welcome to the FHIR API"}



@app.get("/patient/{patient_id}", response_model=dict)
async def get_patient_by_id(patient_id: str):
    """
    Obtiene un paciente por su ID.
    """
    status, patient = GetPatientById(patient_id)
    if status == 'success':
        return patient
    elif status == 'notFound':
        raise HTTPException(status_code=404, detail="Patient not found")
    else:
        raise HTTPException(status_code=500, detail=f"Internal error. {patient}")



@app.get("/patient/", response_model=dict)
async def get_patient_by_identifier(system: str = Query(..., title="Identifier System"), value: str = Query(..., title="Identifier Value")):
    """
    Obtiene un paciente por su identificador.
    """
    status, patient = GetPatientByIdentifier(system, value)
    if status == 'success':
        return patient
    elif status == 'notFound':
        raise HTTPException(status_code=404, detail="Patient not found") #cambiado 204 por 404
    else:
        raise HTTPException(status_code=500, detail=f"Internal error. {patient}")



@app.post("/patient/", response_model=dict)
async def create_patient(patient: dict):
    """
    Crea un nuevo paciente.
    """
    status, patient_id = WritePatient(patient)
    if status == 'success':
        return {"_id": patient_id}
    else:
        raise HTTPException(status_code=500, detail=f"Validating error: {patient_id}")



@app.get("/medicationrequest/{medication_request_id}", response_model=dict)
async def get_medication_request(medication_request_id: str):
    """
    Obtiene una solicitud de medicación por su ID.
    """
    status, data = GetMedicationRequestById(medication_request_id)
    if status == 'success':
        return data
    elif status == 'notFound':
        raise HTTPException(status_code=404, detail="MedicationRequest not found")
    else:
        raise HTTPException(status_code=500, detail=f"Error: {data}")



@app.post("/medicationrequest/", response_model=dict)
async def create_medication_request(medication_request: dict):
    """
    Crea una nueva solicitud de medicación.
    """
    status, req_id = WriteMedicationRequest(medication_request)
    if status == 'success':
        return {"_id": req_id}
    else:
        raise HTTPException(status_code=500, detail=f"Error: {req_id}")




if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
