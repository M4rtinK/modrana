FROM fedora:latest

RUN dnf -y install make python3 python3-six python3-nose\
    pyotherside qt5-qtdeclarative-devel espeak mimic flite

RUN mkdir /modrana-testing
COPY . /modrana-testing

WORKDIR /modrana-testing
RUN make test-python
