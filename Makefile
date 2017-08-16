
default:
	python2 setup.py build

build: 
	python2 setup.py build

install:
	python2 setup.py develop  
#  Normal setup install causes problems with running the scripts while in the source tree

clean:
	python2 setup.py clean

test: 
	./setup.py develop
	py.test -m 'not known_failing and not huge'

coverage:
	coverage run  -m pytest --junitxml=pytests.xml -m 'not known_failing and not huge'
