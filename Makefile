.PHONY: test install clean


test:
	PYTHONPATH=src uv run python -m unittest discover tests/ 

install:
	uv tool uninstall taskdog
	uv cache clean
	uv build
	uv tool install .

clean:
	rm -rf build/ dist/ src/*.egg-info/
	uv cache clean
