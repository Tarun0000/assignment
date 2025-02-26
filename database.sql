-- Create processing_requests table
CREATE TABLE processing_requests (
    request_id UUID PRIMARY KEY,
    status VARCHAR(20) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    webhook_url VARCHAR(255)
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    request_id UUID REFERENCES processing_requests(request_id),
    serial_number INTEGER,
    product_name VARCHAR(100),
    input_urls TEXT[],  -- Array of text for input URLs
    output_urls TEXT[]  -- Array of text for output URLs
);