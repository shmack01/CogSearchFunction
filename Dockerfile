# For more information, please refer to https://aka.ms/vscode-docker-python
FROM mcr.microsoft.com/azure-functions/python:3.0-python3.8-appservice

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1


ENV AzureWebJobsScriptRoot=/home/site/wwwroot \
    AzureFunctionsJobHost__Logging__Console__IsEnabled=true

COPY . /home/site/wwwroot

RUN apt-get update && \
      apt-get -y install sudo

RUN sudo apt-get -y install ghostscript

RUN cd /home/site/wwwroot && \
    pip install -r requirements.txt


# Creates a non-root user and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
#RUN useradd appuser && chown -R appuser /home/site/wwwroot
#USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
#CMD ["python", "PDFModPython\__init__.py"]
