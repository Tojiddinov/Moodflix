# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

# Expose the port your app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
