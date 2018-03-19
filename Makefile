
default: 
	python setup.py build

install: default
	python setup.py install 

clean:
	python setup.py clean

test: 
	python ./setup.py develop
	py.test -m 'not known_failing and not huge and not requires_auth'

#  Turns out omitting the tests for mg-inbox and mg-submit concealed a bug
test2:
	python ./setup.py develop
	py.test -m 'not known_failing and not huge'

testall: 
	python ./setup.py develop
	py.test -m 'not huge'

coverage:
	coverage run  -m pytest --junitxml=pytests.xml -m 'not huge'
