@echo off
REM === Django Autostart Script ===
REM Pfad zu deinem Projekt
cd %USERPROFILE%\Documents\just-kanban

REM Virtuelle Umgebung aktivieren
call .venv\Scripts\activate

REM Django Development Server starten
python manage.py runserver 0.0.0.0:8000

REM Terminal offen halten (optional)
REM pause
