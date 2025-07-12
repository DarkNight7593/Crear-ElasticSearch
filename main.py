from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess

app = FastAPI()

class TenantRequest(BaseModel):
    tenant: str
    puerto: int

@app.post("/crear-tenant")
def crear_tenant(req: TenantRequest):
    nombre_contenedor = f"elastic_{req.tenant}"
    data_path = f"/home/ubuntu/data_{req.tenant}"
    puerto = req.puerto

    try:
        # Lanzar contenedor Docker
        subprocess.run([
            "docker", "run", "-d",
            "--name", nombre_contenedor,
            "--restart=always",
            "-e", "discovery.type=single-node",
            "-e", "network.host=0.0.0.0",
            "-p", f"{puerto}:9200",
            "-v", f"{data_path}:/usr/share/elasticsearch/data",
            "docker.elastic.co/elasticsearch/elasticsearch:7.17.13"
        ], check=True)

        # Crear índice en Elasticsearch
        subprocess.run([
            "curl", "-X", "PUT", f"http://localhost:{puerto}/cursos",
            "-H", "Content-Type: application/json",
            "-d", "@indice_cursos.json"
        ], check=True)

        return { "message": f"Tenant {req.tenant} creado en puerto {puerto}" }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error: {e}")
