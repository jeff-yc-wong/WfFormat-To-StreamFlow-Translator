FROM ubuntu:20.04
RUN apt-get update && apt-get install -y openssh-server stress-ng
# Configure SSH
RUN mkdir /var/run/sshd
RUN echo 'root:redhat' | chpasswd
#password for user login
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
EXPOSE 22

WORKDIR /root
RUN mkdir ~/.ssh
COPY ./id_rsa.pub ./.ssh/authorized_keys

RUN chmod 700 ~/.ssh
RUN chmod 600 ~/.ssh/authorized_keys 
# Start SSH server
CMD ["/usr/sbin/sshd", "-D"]
