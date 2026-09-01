

PATH := podman/${ENV}/Containerfile
PATHDEV := $(call ENV=dev)
PATHPROD := $(call ENV=prod)
BUILD_ID := $(shell cat version)
BUILD_ID += 1



${PATHPROD} ${PATHDEV}:
	podman-compose-build --build-arg IMAGE_PATH=$@ --build-arg BUILD_ID=${BUILD_ID}
	echo ${BUILD_ID} > version

compose.yaml: ${PATHPROD} ${PATHDEV} 
	podman compose up -d
	podman compose logs -f
