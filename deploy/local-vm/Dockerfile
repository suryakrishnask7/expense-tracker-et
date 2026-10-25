FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Install SSH server, python, rsync, curl, and utilities
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-venv \
    python3-pip \
    rsync \
    curl \
    sudo \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Configure default ubuntu user with passwordless sudo access
RUN echo 'ubuntu:ubuntu' | chpasswd && \
    usermod -aG sudo ubuntu && \
    echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Set up SSH and application directory
RUN mkdir -p /home/ubuntu/.ssh /opt/expense-tracker-et /var/log/expense-tracker-et && \
    chmod 700 /home/ubuntu/.ssh && \
    chown -R ubuntu:root /home/ubuntu /opt/expense-tracker-et /var/log/expense-tracker-et

# Configure sshd
RUN mkdir -p /var/run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

EXPOSE 22 5000

CMD ["/usr/sbin/sshd", "-D"]
