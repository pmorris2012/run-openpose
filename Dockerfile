FROM pmorris2012/openpose:latest

COPY requirements.txt /app
RUN pip3 install -r /app/requirements.txt

COPY run-openpose /app
WORKDIR /app

ENTRYPOINT ["python3", "process_folder.py"]
