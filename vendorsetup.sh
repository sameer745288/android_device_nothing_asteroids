# Apply the Asteroids Android Version Banner V7
# when the full LineageOS source environment is available.

if command -v gettop >/dev/null 2>&1; then
    _asteroids_top="$(gettop)"

    if [ -n "$_asteroids_top" ] &&
       [ -f "$_asteroids_top/packages/apps/Settings/src/com/android/settings/deviceinfo/firmwareversion/FirmwareVersionSettings.java" ] &&
       [ -f "$_asteroids_top/packages/apps/Updater/app/src/main/java/org/lineageos/updater/deviceinfo/UpdaterCard.kt" ]; then
        (
            cd "$_asteroids_top" &&
            python3 device/nothing/asteroids/customizations/android-version-card/apply.py
        ) || return 1
    fi

    unset _asteroids_top
fi
