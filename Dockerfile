FROM python:3.6


# put our running code as a non-root user

RUN groupadd -g __GID__ user && useradd -g __GID__ -u __UID__ user -d /code

USER user

# Where will we find the code
WORKDIR /code

# npm expects to use home to locate files
ENV HOME /code

ENV PATH $PATH:/code/.virtualenv/bin
ENV PATH $PATH:/code/dev_tools/cbin

EXPOSE 27017 27017/tcp
