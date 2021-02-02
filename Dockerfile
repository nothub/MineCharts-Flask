FROM n0thub/python:latest
COPY . .
RUN if [ -f requirements.txt ]; then pip3 install --no-cache-dir -r requirements.txt; fi
EXPOSE 5000
CMD ["main.py"]
