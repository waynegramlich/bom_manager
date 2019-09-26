BOM_DIGIKEY_PLUGIN := ../bom_digikey_plugin
BOM_FINDCHIPS_PLUGIN := ../bom_findchips_plugin
BOM_KICAD_PLUGIN := ../bom_kicad_plugin
BOM_MANAGER := .

# NOTE that the version number comes from the BOM_VERSION environment varaible.

all: pkg_install

REPO_URL := https://test.pypi.org/simple/ bom_manager_waynegramlich
PKG_BUILD := =pip install .
DIST_BUILD := =python setup.py sdist bdist_wheel
TWINE_UPLOAD := =twine upload --verbose -r testpypi dist/*
DO_ALL=echo "--PKG--";$(PKG_BUILD);echo "--DIST--";$(DIST_BUILD);echo "--TWINE--";$(TWINE_UPOAD)

.PHONY: dist_build download lint pkg_build upload 

dist_build: pkg_install
	(cd $(BOM_MANAGER);          rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_DIGIKEY_PLUGIN);   rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_FINDCHIPS_PLUGIN); rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_KICAD_PLUGIN);     rm -rf dist ; python setup.py sdist bdist_wheel )

download:
	pip install --no-cache-dir --index-url $(REPO_URL) bom_manager_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_digikey_plugin_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_findchips_plugin_waynegramlich
	pip install --no-cache-dir --index-url $(REPO_URL) bom_kicad_plugin_waynegramlich

lint:
	flake8 --max-line-length=100 $(BOM_MANAGER)/bom_manager/bom.py
	flake8 --max-line-length=100 $(BOM_MANAGER)/bom_manager/bom_gui.py
	flake8 --max-line-length=100 $(BOM_MANAGER)/bom_manager/tracing.py
	flake8 --max-line-length=100 $(BOM_MANAGER)/bom_manager/__init__.py
	flake8 --max-line-length=100 $(BOM_MANAGER)/setup.py
	flake8 --max-line-length=100 $(BOM_DIGIKEY_PLUGIN)/bom_digikey_plugin/digikey.py
	flake8 --max-line-length=100 $(BOM_DIGIKEY_PLUGIN)/bom_digikey_plugin/__init__.py
	flake8 --max-line-length=100 $(BOM_DIGIKEY_PLUGIN)/setup.py
	flake8 --max-line-length=100 $(BOM_FINDCHIPS_PLUGIN)/bom_findchips_plugin/findchips.py
	flake8 --max-line-length=100 $(BOM_FINDCHIPS_PLUGIN)/bom_findchips_plugin/__init__.py
	flake8 --max-line-length=100 $(BOM_FINDCHIPS_PLUGIN)/setup.py
	flake8 --max-line-length=100 $(BOM_KICAD_PLUGIN)/bom_kicad_plugin/kicad.py
	flake8 --max-line-length=100 $(BOM_KICAD_PLUGIN)/bom_kicad_plugin/__init__.py
	flake8 --max-line-length=100 $(BOM_KICAD_PLUGIN)/setup.py

pkg_install:
	(cd $(BOM_MANAGER);          pip install .)
	(cd $(BOM_DIGIKEY_PLUGIN);   pip install .)
	(cd $(BOM_FINDCHIPS_PLUGIN); pip install .)
	(cd $(BOM_KICAD_PLUGIN);     pip install .)

upload: dist_build
	(cd $(BOM_MANAGER);          twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_DIGIKEY_PLUGIN);   twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_FINDCHIPS_PLUGIN); twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_KICAD_PLUGIN);     twine upload --verbose -r testpypi dist/*)

