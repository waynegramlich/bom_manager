BOM_MANAGER := .
BOM_DIGIKEY_PLUGIN := ../bom_digikey_plugin

# NOTE that the version number comes from the BOM_VERSION environment varaible.

all: pkg_install

REPO_URL := https://test.pypi.org/simple/ bom_manager_waynegramlich
PKG_BUILD := =pip install .
DIST_BUILD := =python setup.py sdist bdist_wheel
TWINE_UPLOAD := =twine upload --verbose -r testpypi dist/*
DO_ALL=echo "--PKG--";$(PKG_BUILD);echo "--DIST--";$(DIST_BUILD);echo "--TWINE--";$(TWINE_UPOAD)

.PHONY: pbk_build dist_build upload download

upload: dist_build
	(cd $(BOM_MANAGER);        twine upload --verbose -r testpypi dist/*)
	(cd $(BOM_DIGIKEY_PLUGIN); twine upload --verbose -r testpypi dist/*)

dist_build: pkg_install
	(cd $(BOM_MANAGER);        rm -rf dist ; python setup.py sdist bdist_wheel )
	(cd $(BOM_DIGIKEY_PLUGIN); rm -rf dist ; python setup.py sdist bdist_wheel )

pkg_install:
	(cd $(BOM_MANAGER); pip install .)
	(cd $(BOM_DIGIKEY_PLUGIN); pip install .)

download:
        pip install --no-cache-dir --index-url $(REPO_URL) bom_manager_waynegramlich
        pip install --no-cache-dir --index-url $(REPO_URL) bom_digikey_plugin_waynegramlich
