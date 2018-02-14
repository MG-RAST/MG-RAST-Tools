
default: 
	python setup.py build

install: default
	python setup.py install 

clean:
	python setup.py clean

test: 
	python ./setup.py develop
	py.test -m 'not known_failing and not huge and not requires_auth'

testall: 
	python ./setup.py develop
	py.test -m 'not huge'

coverage:
	coverage run  -m pytest --junitxml=pytests.xml -m 'not huge'
