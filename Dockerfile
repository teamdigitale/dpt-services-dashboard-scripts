FROM ubuntu:20.04

# Set vars
ENV DEBIAN_FRONTEND noninteractive
ENV SCRIPTS_HOME /opt/ingestion_scripts
ENV SCRIPTS_USER scripts

# Install dependencies
RUN apt-get update

RUN apt-get install -y \
  automake \
  make \
  gcc \
  g++ \
  libffi-dev \
  libssl-dev \
  python3-apscheduler \
  python3-dev \
  python3-httplib2 \
  python3-pandas \
  python3-pip \
  python3-requests \
  python3-yaml \
  subversion

RUN pip3 install \
  google-api-python-client \
  google-auth-httplib2 \
  google-auth-oauthlib \
  oauth2client \
  pymongo

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

USER ${SCRIPTS_USER}

ENTRYPOINT ["/bin/sh"]
