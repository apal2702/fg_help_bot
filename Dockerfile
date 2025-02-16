
FROM registry.twilio.com/library/base-python-38:latest

RUN apt-get update && \
    apt-get install -y vim supervisor redis-server jq && \
    pip install --upgrade pip -i "https://pypi.dev.twilio.com/simple/" -vvv


RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install

#COPY config/accsec-threat-network.cfg etc/host-groups/

EXPOSE 9012 9013 6379 8080 8888 9454

COPY . /mnt/accsec/


WORKDIR /mnt/accsec/

RUN  pip install -r /mnt/accsec/requirements.txt --index-url https://pypi.dev.twilio.com/simple/

RUN pip install -e .
#RUN chmod +x /mnt/accsec/docker-entrypoint.sh

#ßENTRYPOINT ["/mnt/accsec/docker-entrypoint.sh"]
# Initializing from supervisord
CMD ["supervisord","-c","/mnt/accsec/config/service_script.conf"]
