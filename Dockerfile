FROM python:3-alpine

# Set vars
ENV SCRIPTS_HOME /opt/ingestion_scripts
ENV SCRIPTS_USER scripts

# Install dependencies
RUN apk update && \
    apk add make automake gcc g++ subversion python3-dev libffi-dev openssl-dev

RUN adduser --home ${SCRIPTS_HOME} --shell /bin/sh --disabled-password ${SCRIPTS_USER}

WORKDIR ${SCRIPTS_HOME}

# Create scripts folder, the default user and set proper permisns
RUN mkdir -p ${SCRIPTS_HOME}
RUN chown -R ${SCRIPTS_USER}.${SCRIPTS_USER} ${SCRIPTS_HOME}

# Copy the scripts to the container
COPY anpr anpr
COPY cie cie
COPY common common
COPY devitalia devitalia
COPY repubblica-digitale repubblica-digitale
COPY spid spid
COPY requirements.txt .

# Install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

USER ${SCRIPTS_USER}

ENTRYPOINT ["/bin/sh"]
