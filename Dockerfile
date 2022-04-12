FROM fedora:latest

RUN dnf -y update && \
    dnf -y install dnf-plugins-core && \
    dnf -y builddep modulemd-tools && \
    dnf -y install gcc krb5-devel python3-tox

CMD cd /modulemd-tools && ./entrypoint.sh
