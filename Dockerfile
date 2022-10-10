FROM python:slim

WORKDIR /usr/src/app
RUN groupadd -g 2022 python && useradd -g 2022 -u 2022 --home-dir /usr/src/app python && chown python:python /usr/src/app
USER python
ENV PATH="${PATH}:/usr/src/app/.local/bin"
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./torrentino.py" ]
