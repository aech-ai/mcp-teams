FROM postgres:15

# Install the pgvector extension
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-15-pgvector \
        postgresql-contrib-15 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy custom configuration
COPY postgresql.conf /etc/postgresql/postgresql.conf

# Set the default command to run when starting the container
CMD ["postgres", "-c", "config_file=/etc/postgresql/postgresql.conf"]