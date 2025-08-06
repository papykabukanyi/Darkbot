@echo off
echo Fixing Flask/Werkzeug compatibility issue...

pip uninstall -y flask werkzeug
pip install flask==2.0.1 werkzeug==2.0.2

echo Done! Flask and Werkzeug have been updated to compatible versions.
