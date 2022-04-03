FROM python:3-alpine

WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ["get.py", "place2022.py", "./"]

CMD [ "python", "./place2022.py" ]