from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import requests
import time
import os

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
        # Verificar si ya existe un contenedor con ese nombre
        resultado = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}"],
            capture_output=True, text=True, check=True
        )
        contenedores = resultado.stdout.strip().split("\n")

        if nombre_contenedor in contenedores:
            return {
                "message": f"El contenedor '{nombre_contenedor}' ya existe. Proceso omitido.",
                "tenant": req.tenant,
                "puerto": puerto
            }

        # Crear carpeta de datos con permisos para elasticsearch (UID 1000)
        os.makedirs(data_path, exist_ok=True)
        subprocess.run(["sudo", "chown", "-R", "1000:1000", data_path], check=True)

        # Lanzar contenedor con límites de recursos
        subprocess.run([
            "docker", "run", "-d",
            "--name", nombre_contenedor,
            "--restart=always",
            "--memory=1g",
            "--cpus=0.6",
            "--memory-swappiness=0",
            "-e", "discovery.type=single-node",
            "-e", "network.host=0.0.0.0",
            "-e", "xpack.ml.enabled=false",
            "-e", "xpack.security.enabled=false",
            "-e", "xpack.monitoring.enabled=false",
            "-e", "ES_JAVA_OPTS=-Xms512m -Xmx512m",
        
            # 👇 CORS habilitado
            "-e", "http.cors.enabled=true",
            "-e", "http.cors.allow-origin=*",
            "-e", "http.cors.allow-methods=OPTIONS, HEAD, GET, POST, PUT, DELETE",
            "-e", "http.cors.allow-headers=*",  
        
            "-p", f"{puerto}:9200",
            "-v", f"{data_path}:/usr/share/elasticsearch/data",
            "docker.elastic.co/elasticsearch/elasticsearch:7.17.13"
        ], check=True)


        # Esperar a que el servicio de Elasticsearch esté disponible
        for intento in range(50):
            try:
                res = requests.get(f"http://localhost:{puerto}")
                if res.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                time.sleep(3)
        else:
            raise HTTPException(status_code=500, detail="Elasticsearch no respondió después de 30 segundos")

        # Cargar el índice desde archivo
        ruta_json = os.path.join(os.path.dirname(__file__), "indice_cursos.json")
        with open(ruta_json, 'r') as f:
            indice = json.load(f)

        # Crear índice en Elasticsearch
        resp = requests.put(
            f"http://localhost:{puerto}/cursos",
            headers={"Content-Type": "application/json"},
            json=indice
        )

        if resp.status_code >= 300:
            raise HTTPException(status_code=500, detail=f"Error al crear índice: {resp.text}")

        return {
            "message": f"Tenant '{req.tenant}' creado exitosamente en puerto {puerto}",
            "tenant": req.tenant,
            "puerto": puerto
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error al ejecutar Docker o permisos: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
