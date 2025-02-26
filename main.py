from fastapi import FastAPI, UploadFile, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import ProcessingRequest, Product
from config import settings
import csv
import uuid
import asyncio
import aiohttp
from images_utils import process_image
import os

app = FastAPI()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def validate_csv(file):
    reader = csv.DictReader(file.decode().splitlines())
    required_columns = {"S. No.", "Product Name", "Input Image Urls"}
    if not all(col in reader.fieldnames for col in required_columns):
        raise ValueError("Invalid CSV format")
    return reader

async def process_images(request_id: uuid.UUID, session: Session, webhook_url: str = None):
    try:
        products = session.query(Product).filter_by(request_id=request_id).all()
        
        async with aiohttp.ClientSession() as http_session:
            for product in products:
                output_urls = []
                for i, input_url in enumerate(product.input_urls):
                    output_path = f"{settings.UPLOAD_DIR}/{request_id}_{product.serial_number}_{i}.jpg"
                    result = await asyncio.to_thread(
                        process_image, input_url, output_path
                    )
                    if result:
                        output_urls.append(output_path)
                    else:
                        output_urls.append(None)
                product.output_urls = output_urls
                session.commit()
        
        # Update request status
        request = session.query(ProcessingRequest).get(request_id)
        request.status = "COMPLETED"
        request.completed_at = "CURRENT_TIMESTAMP"
        session.commit()
        
        # Trigger webhook if provided
        if webhook_url:
            async with http_session.post(webhook_url, json={
                "request_id": str(request_id),
                "status": "COMPLETED"
            }) as response:
                print(f"Webhook response: {response.status}")
                
    except Exception as e:
        request = session.query(ProcessingRequest).get(request_id)
        request.status = "FAILED"
        session.commit()
        print(f"Processing failed: {str(e)}")
    finally:
        session.close()

@app.post("/upload")
async def upload_csv(file: UploadFile, webhook_url: str = None):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Please upload a CSV file")
    
    session = SessionLocal()
    try:
        # Validate CSV
        content = await file.read()
        csv_reader = validate_csv(content)
        
        # Create processing request
        request_id = uuid.uuid4()
        request = ProcessingRequest(request_id=request_id, webhook_url=webhook_url)
        session.add(request)
        
        # Store products
        for row in csv_reader:
            input_urls = [url.strip() for url in row["Input Image Urls"].split(",")]
            product = Product(
                request_id=request_id,
                serial_number=int(row["S. No."]),
                product_name=row["Product Name"],
                input_urls=input_urls
            )
            session.add(product)
        
        session.commit()
        
        # Start async processing in background
        asyncio.create_task(process_images(request_id, SessionLocal(), webhook_url))
        
        return {"request_id": str(request_id)}
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Error processing upload: {str(e)}")
    finally:
        session.close()

@app.get("/status/{request_id}")
async def get_status(request_id: str):
    session = SessionLocal()
    try:
        request = session.query(ProcessingRequest).get(uuid.UUID(request_id))
        if not request:
            raise HTTPException(404, "Request not found")
        
        products = session.query(Product).filter_by(request_id=request.request_id).all()
        response = {
            "request_id": str(request.request_id),
            "status": request.status,
            "products": [
                {
                    "serial_number": p.serial_number,
                    "product_name": p.product_name,
                    "input_urls": p.input_urls,
                    "output_urls": p.output_urls or []
                } for p in products
            ]
        }
        return response
    finally:
        session.close()