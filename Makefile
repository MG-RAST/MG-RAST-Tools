
default:
	python2 setup.py build

install:
	python2 setup.py install 

clean:
	python2 setup.py clean

test: 
	./setup.py develop
	py.test -m 'not known_failing and not huge'

coverage:
	coverage run  -m pytest --junitxml=pytests.xml -m 'not known_failing and not huge'
