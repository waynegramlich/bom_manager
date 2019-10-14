# MIT License
#
# Copyright (c) 2019 Wayne C. Gramlich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Define the directories for the main code and associated plugins:
BOM_DIGIKEY_PLUGIN_DIRECTORY := ../bom_digikey_plugin
BOM_FINDCHIPS_PLUGIN_DIRECTORY := ../bom_findchips_plugin
BOM_KICAD_PLUGIN_DIRECTORY := ../bom_kicad_plugin
BOM_MANAGER_DIRECTORY := .

# For each Python package define the Python files that matter:
BOM_DIGIKEY_PLUGIN_FILES := 							\
	$(BOM_DIGIKEY_PLUGIN_DIRECTORY)/bom_digikey_plugin/digikey.py		\
	$(BOM_DIGIKEY_PLUGIN_DIRECTORY)/bom_digikey_plugin/__init__.py		\
	$(BOM_DIGIKEY_PLUGIN_DIRECTORY)/setup.py
BOM_DIGIKEY_PLUGIN_LINTS := ${BOM_DIGIKEY_PLUGIN_FILES:%.py=%.pyl}
BOM_FINDCHIPS_PLUGIN_FILES :=							\
	$(BOM_FINDCHIPS_PLUGIN_DIRECTORY)/bom_findchips_plugin/findchips.py	\
	$(BOM_FINDCHIPS_PLUGIN_DIRECTORY)/bom_findchips_plugin/__init__.py	\
	$(BOM_FINDCHIPS_PLUGIN_DIRECTORY)/setup.py
BOM_DIGIKEY_PLUGIN_LINTS := ${BOM_FINDCHIPS_PLUGIN_FILES:%.py=%.pyl}
BOM_KICAD_PLUGIN_FILES :=                                                       \
	$(BOM_KICAD_PLUGIN_DIRECTORY)/bom_kicad_plugin/kicad.py			\
	$(BOM_KICAD_PLUGIN_DIRECTORY)/bom_kicad_plugin/__init__.py		\
	$(BOM_KICAD_PLUGIN_DIRECTORY)/setup.py
BOM_DIGIKEY_PLUGIN_LINTS := ${BOM_DIGIKEY_PLUGIN_FILES:%.py=%.pyl}
BOM_MANAGER_FILES :=								\
	$(BOM_MANAGER_DIRECTORY)/bom_manager/bom.py				\
	$(BOM_MANAGER_DIRECTORY)/bom_manager/bom_gui.py				\
	$(BOM_MANAGER_DIRECTORY)/bom_manager/tracing.py				\
	$(BOM_MANAGER_DIRECTORY)/bom_manager/__init__.py			\
	$(BOM_MANAGER_DIRECTORY)/setup.py
BOM_MANAGER_LINTS := ${BOM_MANAGER_FILES:%.py=%.pyl}
PYTHON_FILES :=									\
        ${BOM_DIGKEY_PLUGIN_FILES}						\
	${BOM_FINDCHIPS_PLUGIN_FILES}						\
	${BOM_KICAD_PLUGIN_FILES}						\
	${BOM_MANAGER_FILES}
PYTHON_LINTS := ${PYTHON_FILES:%.py=%.pyl}

# The `.pyp` file is touched to remember that a package has been installed:
PYP_FILES := 									\
	${BOM_DIGIKEY_PLUGIN_DIRECTORY}/.pyp					\
	${BOM_FINDCHIPS_PLUGIN_DIRECTORY}/.pyp					\
	${BOM_KICAD_PLUGIN_DIRECTORY}/.pyp					\
	${BOM_MANAGER_DIRECTORY}/.pyp


# NOTE that the version number comes from the BOM_VERSION environment varaible.

# Some string definitiaon
REPO_URL := https://test.pypi.org/simple/ bom_manager_waynegramlich
PKG_BUILD := pip install .
DIST_BUILD := python setup.py sdist bdist_wheel
TWINE_UPLOAD := twine upload --verbose -r testpypi dist/*
DO_ALL=echo "--PKG--";$(PKG_BUILD);echo "--DIST--";$(DIST_BUILD);echo "--TWINE--";$(TWINE_UPOAD)

.PHONY: all clean dist_build download lint upload

all: ${PYP_FILES}

clean:
	rm -f ${PYTHON_LINTS} ${PYP_FILES}

dist_build: pkg_install
	(cd $(BOM_MANAGER_DIRECTORY);          rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_DIGIKEY_PLUGIN_DIRECTORY);   rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_FINDCHIPS_PLUGIN_DIRECTORY); rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_KICAD_PLUGIN_DIRECTORY);     rm -rf dist ; python setup.py sdist bdist_wheel )

download:
	pip install --no-cache-dir --index-url $(REPO_URL) bom_manager_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_digikey_plugin_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_findchips_plugin_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_kicad_plugin_waynegramlich


lint: ${PYTHON_LINTS}

upload: dist_build
	(cd $(BOM_DIGIKEY_PLUGIN_DIRECTORY);   twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_FINDCHIPS_PLUGIN_DIRECOTRY); twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_KICAD_PLUGIN_DIRECTORY);     twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_MANAGER_DIRECTORY);          twine upload --verbose -r testpypi dist/*)

# The `.pyp` suffix is used to remember that package has been installed:
$(BOM_DIGIKEY_PLUGIN_DIRECTORY)/.pyp: ${BOM_DIGIKEY_PLUGIN_LINTS} \
    $(BOM_DIGIKEY_PLUGIN_DIRECTORY)/bom_digikey_plugin/ROOT
	(cd $(BOM_DIGIKEY_PLUGIN_DIRECTORY); pip install .)
	touch $@
$(BOM_FINDCHIPS_PLUGIN_DIRECTORY)/.pyp: ${BOM_FINDCHIPS_PLUGIN_LINTS}
	(cd $(BOM_FINDCHIPS_PLUGIN_DIRECTORY); pip install .)
	touch $@
$(BOM_KICAD_PLUGIN_DIRECTORY)/.pyp: ${BOM_KICAD_PLUGIN_LINTS}
	(cd $(BOM_KICAD_PLUGIN_DIRECTORY); pip install .)
	touch $@
$(BOM_MANAGER_DIRECTORY)/.pyp: ${BOM_MANAGER_LINTS}
	(cd $(BOM_MANAGER_DIRECTORY); pip install .)
	touch $@

# Pattern rule for running `mypy` and `flake8` over a `.py` Python file.  The `.pyl` suffix
# is used to remember that the linting has occured:
%.pyl: %.py
	mypy                         $<
	flake8 --max-line-length=100 $<
	touch $@

# [CI/CD Actions on GitHub](https://github.com/features/actions)
# [CI/CD Pipelines on GitHub]https://docs.gitlab.com/ee/ci/pipelines.html
# [Hugo on gitlab](https://gohugo.io/hosting-and-deployment/hosting-on-gitlab/)
