include make/*.mk
.PHONY: clean rebuild


PATHPROD := Containerfile
PATHDEV  := dev.Containerfile
VERSION_FILE := version

# Read version or start at 0
CURRENT_VERSION := $(shell [ -f $(VERSION_FILE) ] && cat $(VERSION_FILE) || echo 0)
# Increment for next build
NEXT_VERSION := $(shell expr $(CURRENT_VERSION) + 1)

all: rebuild

version:
	echo $(NEXT_VERSION) > $(VERSION_FILE)


compose.yaml: ${PATHDEV} ${PATHPROD}
	podman compose up -d
	podman compose logs -f

${PATHDEV} ${PATHPROD}: version
	podman build -t ${CURRENT_VERSION} -f $@

clean:
	rm version

rebuild: ${PATHDEV}
