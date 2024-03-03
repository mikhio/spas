FROM python:latest
RUN mkdir /Spas
COPY . /Spas/
WORKDIR /Spas
Run pip install flask
EXPOSE 8080
CMD ["python", "spas.py"]