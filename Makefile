PYINSTALLER := build_env/bin/pyinstaller
APP_BIN := dist/RealSynth/RealSynth

.PHONY: build run clean

build:
	$(PYINSTALLER) --noconfirm --onedir --windowed \
		--name RealSynth \
		--icon=logo.png \
		--add-data "assets:assets" \
		--add-data "logo.png:." \
		--exclude-module PyQt6.QtWebEngineCore \
		--exclude-module PyQt6.QtWebEngineWidgets \
		--exclude-module PyQt6.QtQml \
		--exclude-module PyQt6.QtQuick \
		--exclude-module PyQt6.QtSql \
		--exclude-module PyQt6.QtNetwork \
		--exclude-module PyQt6.QtBluetooth \
		--exclude-module PyQt6.QtDBus \
		--exclude-module PyQt6.QtDesigner \
		--exclude-module PyQt6.QtHelp \
		--exclude-module PyQt6.QtOpenGL \
		--exclude-module PyQt6.QtPdf \
		--exclude-module PyQt6.QtPositioning \
		--exclude-module PyQt6.QtPrintSupport \
		--exclude-module PyQt6.QtSensors \
		--exclude-module PyQt6.QtSerialPort \
		--exclude-module PyQt6.QtTest \
		--exclude-module PyQt6.QtXml \
		RealSynth.py

run:
	./$(APP_BIN)

clean:
	rm -rf build dist RealSynth.spec
