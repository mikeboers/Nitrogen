
python = bin/python

build:
	$(python) setup.py build
	
test:
	$(python) setup.py nosetests --verbosity=2

clean:
	- rm -rf build dist *.egg-info *.egg