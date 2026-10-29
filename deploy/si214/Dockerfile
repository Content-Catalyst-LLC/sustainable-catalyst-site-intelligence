# Build on each target architecture from its verified immutable runtime base.
# No package installation or production environment files enter this image.
ARG RUNTIME_BASE
FROM ${RUNTIME_BASE}
ARG SOURCE_COMMIT
ARG BASE_IMAGE_ID
LABEL org.opencontainers.image.version="SI-2.1.4" \
      org.opencontainers.image.revision="${SOURCE_COMMIT}" \
      com.sustainablecatalyst.application-version="4.56.1" \
      com.sustainablecatalyst.base-image-id="${BASE_IMAGE_ID}"
ENV SC_SI_GIT_COMMIT=${SOURCE_COMMIT} SC_SI_RELEASE_ID=SI-2.1.4
COPY backend/app/ /app/app/
COPY backend/data/ /app/data/
