FROM python:3-slim

ARG DEBIAN_FRONTEND=noninteractive
RUN <<EOT 
    #Update OS
    apt update 
    apt -y upgrade 
    apt install -y \
    git \
    wget \
    nano \
    g++ \
    p7zip-full \
    s3fs
    rm -rf /var/lib/apt/lists/* 
    apt autoclean
EOT

ADD environment.yml /tmp/environment.yml

SHELL ["/bin/bash", "-c"]
RUN <<EOT 
    # Install Conda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    mkdir /root/.conda 
    bash Miniconda3-latest-Linux-x86_64.sh -b
    rm -f Miniconda3-latest-Linux-x86_64.sh
    echo "Miniconda installation complete" 
    export PATH=$PATH:/root/miniconda3/bin
    conda init bash
    source /root/.bashrc 
    echo "Running $(conda --version)"
    conda update -n base conda -y 
    conda install mamba -c conda-forge -y
EOT
RUN <<EOT 
    # Creates env testbed
    export PATH=$PATH:/root/miniconda3/bin
    conda env create -f /tmp/environment.yml -y
    conda init bash
    . /root/.bashrc
    conda activate testbed
    mamba update --all -y
    pip install ping3 -y
    mamba clean -afy
    echo 'alias ll="ls -lA --color"'>>/root/.bashrc
    echo 'export PATH=/root/miniconda3/envs/testbed/bin:$PATH' >>/root/.bashrc
    echo 'conda activate testbed' >> /root/.bashrc
EOT

RUN <<EOT
      # create folders
      mkdir -p /root/testbed
      mkdir -p /root/testbed/data
      mkdir -p /root/testbed/output
      mkdir -p /root/aws
      mkdir -p /root/cdse
      mkdir -p /root/.aws
EOT

COPY ../data/GCP.7z /root/testbed/data
COPY *.py /root/testbed
COPY settings.yml /root/testbed
COPY credentials /root/.aws

RUN chmod 600 /root/.aws/credentials

RUN <<EOT 
    # GroundControlPoint 
    7z x /root/testbed/data/GCP.7z -o/root/testbed/data/
EOT

RUN <<EOT
    # Cleanup 
    rm /root/testbed/data/GCP.7z
    rm /tmp/environment.yml
EOT

#RUN echo "s3fs eodata ~/s3-cdse -o profile=cdse -o dbglevel=info -o url=https://eodata.dataspace.copernicus.eu/ -o use_path_request_style"
#RUN echo "s3fs#eodata /root/s3-cdse fuse _netdev,allow_other,nonempty,umask=000,profile=cdse,url=https://eodata.dataspace.copernicus.eu 0 0" >> /etc/fstab
#RUN echo "s3fs#eodata /root/s3-cdse fuse _netdev,allow_other,nonempty,umask=000,profile=cdse,uid=0,gid=0,umask=0002,url=https://eodata.dataspace.copernicus.eu 0 0">> /etc/fstab

RUN <<EOT
    echo "s3fs eodata ~/cdse -o profile=cdse -o dbglevel=info -o url=https://eodata.dataspace.copernicus.eu/ -o use_path_request_style -o use_cache="" ">>/root/.bashrc
    echo "s3fs sentinel-s2-l2a ~/aws -o url=https://s3-eu-central-1.amazonaws.com -o endpoint=eu-central-1 -o sigv4 -o requester_pays -o profile=aws -o use_cache="" ">>/root/.bashrc
    #echo "# allow all users to create icmp sockets\n net.ipv4.ping_group_range=0 2147483647" | sudo tee -a /etc/sysctl.d/ping_group.conf
    #echo "s3fs#eodata /root/cdse fuse _netdev,allow_other,nonempty,umask=000,uid=0,gid=0,profile=cdse,url=https://eodata.dataspace.copernicus.eu 0 0">> /etc/fstab
    sed -i '/user_allow_other/s/^#//g' /etc/fuse.conf
EOT

ENV CONDA_DEFAULT_ENV testbed
ENV PROJ_LIB /root/miniconda3/envs/testbed/share/proj
ENV CONDA_PREFIX /root/miniconda3/envs/testbed
ENV PATH /root/miniconda3/envs/testbed/bin:$PATH

#ENV ENV /root/.bashrc

ENTRYPOINT ["bash", "-l"]