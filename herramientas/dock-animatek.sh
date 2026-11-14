#!/bin/sh
# Pone en el FM-1 nuestro FM1 Dock (rama din-clock: el reloj MIDI a tiempo, PR joakimeriksson/fm1-dock#90)
# con ATEK303 (CLK OFFSET, -16 ms de serie) y AMB-1, y deja sonando el ATEK303. Vale desde cualquier firmware
# que acepte el actualizador de M-VAVE (SHRUB, el oficial, otro Dock...).
#
#   herramientas/dock-animatek.sh            todo: instala el Dock y añade los dos módulos
#   herramientas/dock-animatek.sh modulos    solo los módulos (el FM-1 ya tiene nuestro Dock)
#
# Antes: Bitwig cerrado (o sin el puerto Felucca), ninguna pestaña del navegador con el FM-1, cable de datos directo.
# Los archivos están en firmwares/propios/dock-animatek/ (fuera de Git); se rehacen compilando fm1-dock de la rama
# din-clock con atek303/app/app.c copiado en modules/atek303/atek303/ (ver CHANGELOG, 14/11/2026).
set -e
cd "$(dirname "$0")/.."
RAIZ=$(pwd)
PY="$RAIZ/terceros/rescate/MvaveFM1Unbricker/.venv/bin/python"
DOCK="$RAIZ/terceros/fm1-dock"
F="$RAIZ/firmwares/propios/dock-animatek"
export PYTHONWARNINGS=ignore

for f in "$PY" "$DOCK/tools/fm1_install.py" "$DOCK/tools/dock.py" "$F/fm1-dock-din-clock.fwsc" "$F/atek303.dock" "$F/amb.dock"; do
    [ -e "$f" ] || { echo "Falta $f"; exit 1; }
done

cd "$DOCK"
if pgrep -f BitwigAudioEngine >/dev/null 2>&1; then
    echo "Ojo: Bitwig está abierto. Si tiene el puerto Felucca, ciérralo antes (si falla, es eso)."
fi

if [ "$1" != "modulos" ]; then
    echo "== 1/3 Instalando FM1 Dock (din-clock) en el FM-1: no toques el cable (unos 2 minutos)"
    "$PY" tools/fm1_install.py "$F/fm1-dock-din-clock.fwsc" --yes 2>&1 | tr '\r' '\n' | grep -vE "RuntimeWarning|^writing|^checking|^$" || true
    "$PY" tools/fm1_install.py --info 2>&1 | grep -q "FM-1_921" || {
        echo "El FM-1 no ha vuelto como FM1 Dock. Apágalo y enciéndelo, y vuelve a lanzar esto."
        echo "Si la pantalla se queda negra: OCT- y OCT+ al encender (recuperación) y otra vez este script."
        exit 1
    }
    sleep 4
fi

echo "== 2/3 Añadiendo ATEK303 y AMB-1"
for m in atek303 amb; do
    "$PY" tools/dock.py deploy "$F/$m.dock" 2>&1 | tr '\r' '\n' | grep -vE "RuntimeWarning|%$|^$" | tail -1
    sleep 2
done

echo "== 3/3 ATEK303 sonando"
"$PY" tools/dock.py select ATEK303 2>&1 | grep -v RuntimeWarning | tail -1 || true
"$PY" tools/dock.py modules 2>&1 | grep -v RuntimeWarning
echo "Listo. Si las OPTIONS del ATEK303 no dicen CLK OFFSET -16 MS, ponlo a mano (OCT- + HOME)."
