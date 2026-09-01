.PHONY: clean

all: /usr/bin/uv

uv:
	mkdir -p uv

uv/install.sh: uv
	curl -LsSf https://astral.sh/uv/install.sh > uv/install.sh
	chmod +x uv/install.sh

/usr/bin/uv: uv/install.sh
	$(shell uv/install.sh)

clean:
	rm -rf uv
