FROM python:latest
RUN mkdir /Spas
COPY . /Spas/
WORKDIR /Spas
Run pip install -r requirements.txt
EXPOSE 8080
CMD ["python", "api.py"]