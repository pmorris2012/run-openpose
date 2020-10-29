FROM pmorris2012/openpose:latest

RUN pip3 install tqdm

COPY run_openpose /app

WORKDIR /app

ENTRYPOINT ["python3", "process_folder.py"]
