FROM mambaorg/micromamba:1.4.3

USER root
WORKDIR /app

COPY environment.yml .

RUN micromamba install -y -n base -f environment.yml && \
    micromamba clean --all --yes

COPY . .

EXPOSE 5000

CMD ["micromamba", "run", "-n", "base", "python", "-m", "src.field_health.app"]