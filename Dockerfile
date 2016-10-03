FROM fedora:latest
MAINTAINER Red Hat, Inc. <container-tools@redhat.com>

ENV MHM_RELEASE v0.1.0-alpha
ENV PYTHONPATH  /commissaire-http/src/

# Install required dependencies and commissaire-http
# NOTE: gcc, libffi-devel and openssl-devel are required to build some of the
#       dependencies when using pip. redhat-rpm-config has at least one file
#       referenced by one of the build dependencies.
RUN dnf -y update && dnf -y install --setopt=tsflags=nodocs redhat-rpm-config python3-pip python3-virtualenv git gcc libffi-devel openssl-devel ; dnf clean all && \
git clone https://github.com/projectatomic/commissaire-http.git && \
py3-virtualenv /environment && \
. /environment/bin/activate && \
cd commissaire-http && \
pip install -U pip && \
pip install -r requirements.txt && \
pip install git+https://github.com/projectatomic/commissaire.git && \
pip freeze > /installed-python-deps.txt  && \
pip install -e . && \
dnf remove -y gcc git redhat-rpm-config libffi-devel && \
dnf clean all

EXPOSE 8000
WORKDIR /commissaire-http
RUN mkdir -p /etc/commissaire
CMD . /environment/bin/activate && commissaire-server
