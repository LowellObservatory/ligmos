ARG miniconda_version=4.10.3
FROM continuumio/miniconda3:${miniconda_version}

ARG userid="31415"
ARG groupid="31415"

# In the *container*
#   Note that a matching group is added automatically
RUN addgroup --gid ${groupid} lig && \
    adduser lig --uid ${userid} --gid ${groupid} \
    --gecos '' --disabled-password

# Additional quality-of-life packages, plus SNMP stuff:
#   Add the non-free repository first so we can get the nonfree MIBs
RUN export DEBIAN_RELEASE=bullseye && \
    echo "deb http://deb.debian.org/debian ${DEBIAN_RELEASE} non-free" > \
        /etc/apt/sources.list.d/debian-non-free.list
RUN apt-get update --fix-missing && apt-get install -y vim build-essential \
                                                       gcc vim rsync wget \
                                                       procps libgl1 \
                                                       snmp libsnmp-dev \
                                                       snmp-mibs-downloader \
                                                       libffi-dev \
                                                       smitools libsmi2-dev

# Copy in the lists of stuff that Conda and pip need to install
#   (./ is relative to WORKDIR)
COPY --chown=lig:lig conda_install.txt ./
COPY --chown=lig:lig condaforge_install.txt ./
COPY --chown=lig:lig pip_install.txt ./

# One layer each for the conda and pip installs
RUN conda install -y --file conda_install.txt
RUN conda install -c conda-forge --file condaforge_install.txt
RUN pip install --no-cache-dir -r pip_install.txt

RUN pip install snimpy

USER lig
RUN mkdir /home/lig/.snmp && mkdir /home/lig/.snmp/mibs
COPY --chown=lig:lig ./mibs/* /home/lig/.snmp/mibs/

# At this point it's a minimal working LIG python image
#   so copy in the LIG codes and get them going
USER lig:lig
WORKDIR /home/lig/
RUN mkdir conf && mkdir logs && mkdir Codes

# Install the ligmos library, for all users
WORKDIR /home/lig/Codes/
COPY --chown=lig:lig ./ligmos ./ligmos
WORKDIR /home/lig/Codes/ligmos

# Totally unnecessary root install but whatever
USER root
RUN pip install -e .

# Dump us into an iPython shell if there's no
#   actual command issued to start a LIG code
USER lig
WORKDIR /home/lig/
CMD ["ipython"]
