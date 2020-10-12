ARG ODOO_VERSION=12.0
FROM odoo:${ODOO_VERSION}

USER root

RUN sed -i -- 's/; admin_passwd = admin/admin_passwd = you-must-change-me/g' /etc/odoo/odoo.conf

RUN mkdir -p /mnt/addons/tmp

RUN apt update && apt install -y git
RUN cd /mnt/addons/tmp && \
    git clone -b ${ODOO_VERSION} --depth=1 https://github.com/litnimax/remote_agent && \
    mv remote_agent /mnt/addons && rm -rf /mnt/addons/tmp

RUN pip3 install phonenumbers tinyrpc

COPY ./controllers/ /mnt/addons/asterisk_calls/controllers/
COPY ./data/ /mnt/addons/asterisk_calls/data/
COPY ./deploy/agent/agent.py /mnt/addons/asterisk_calls/deploy/agent/
COPY ./deploy/agent/start_agent.sh /mnt/addons/asterisk_calls/deploy/agent/
COPY ./deploy/agent/requirements.txt /mnt/addons/asterisk_calls/deploy/agent/
COPY ./deploy/agent/astcalls_agent.service /mnt/addons/asterisk_calls/deploy/agent/
COPY ./doc/ /mnt/addons/asterisk_calls/doc/
COPY ./i18n/ /mnt/addons/asterisk_calls/i18n/
COPY ./models/ /mnt/addons/asterisk_calls/models/
COPY ./reports/ /mnt/addons/asterisk_calls/reports/
COPY ./security/ /mnt/addons/asterisk_calls/security/
COPY ./static/ /mnt/addons/asterisk_calls/static/
COPY ./views/ /mnt/addons/asterisk_calls/views/
COPY ./wizard/ /mnt/addons/asterisk_calls/wizard/
COPY ./__init__.py /mnt/addons/asterisk_calls/__init__.py
COPY ./__manifest__.py /mnt/addons/asterisk_calls/__manifest__.py

COPY ./deploy/odoo/odoo.conf /etc/odoo/odoo.conf

USER odoo

