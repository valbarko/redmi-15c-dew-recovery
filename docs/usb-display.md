# USB: падение снимков экрана и обрезанные часы

[Разбор](../README.ru.md) · [Источники](evidence.md)

Это два независимых исправления поверх уже загружающейся GSI. Оба проверены на Android 15 QPR2 `BP1A.250405.005.C1` / `13151952` и конкретной панели `dew`. Постоянные BOOT-области, root-политика и системные разделы ради них не менялись.

## Почему screencap перезапускал интерфейс

Два первоначальных запроса снимка дали `SIGSEGV` по нулевому адресу в `createScreenCaptureOutput(ScreenCaptureOutputArgs)+988`, далее `renderScreenImpl`. SurfaceFlinger имел BuildId `3c06727c25e244b283c8af816b313194`. На смещении `0x269c28` в исследованном бинарнике находился `BLR x8`, связанный с виртуальным вызовом `getSourceCrop`.

Сопоставление стека, дизассемблирования и [AOSP android-15.0.0_r20 SurfaceFlinger.cpp](https://android.googlesource.com/platform/frameworks/native/+/refs/tags/android-15.0.0_r20/services/surfaceflinger/SurfaceFlinger.cpp) указало на потерю времени жизни RenderArea в асинхронном захвате. Это вывод из нескольких свидетельств; отдельная инструментированная сборка для доказательства UAF на устройстве не устанавливалась.

Подходящий upstream-патч — [TrebleDroid commit 37973d9](https://github.com/TrebleDroid/platform_frameworks_native/commit/37973d9a8e812cf54c8fa017767003896e9737f5), bug `389887557`, Change-Id `I37035b34d55f4847db9722371ea492364f7706fe`. Он передаёт владение RenderArea в асинхронный путь вместо заимствования указателя. Патч принадлежит upstream; наш вклад — сопоставление симптома и проверенный обход на этой сборке.

## Runtime workaround

В `/vendor/build.prop` было `debug.renderengine.backend=skiagl`. Переключили тот же GL backend в threaded-вариант и перезапустили SurfaceFlinger. Команды ниже требуют уже работающего **root ADB**, явно выбранного и локально проверенного устройства. Перезапуск графики затрагивает UI/zygote; сначала сохраните текущие действия и разблокируйте телефон самостоятельно, когда потребуется.

```sh
# SERIAL is your own locally selected ADB target; do not publish it.
adb -s "$SERIAL" shell id -u
adb -s "$SERIAL" shell getprop ro.product.device
adb -s "$SERIAL" shell getprop ro.build.id
adb -s "$SERIAL" shell getprop debug.renderengine.backend

# Continue only for the root/build/device conditions described above.
adb -s "$SERIAL" shell setprop debug.renderengine.backend skiaglthreaded
adb -s "$SERIAL" shell setprop ctl.restart surfaceflinger
```

Сначала дождались восстановления root ADB и SystemUI. Затем подтвердили свойство и отдельный поток RenderEngine. Текущие потоки могут исчезнуть между перечислением и чтением — ENOENT одного `/proc`-файла не доказывает отказ ADB:

```sh
adb -s "$SERIAL" shell \
  'for t in /proc/$(pidof surfaceflinger)/task/*/comm; do cat "$t" 2>/dev/null || true; done'
```

Терпимость к исчезнувшим потокам не отменяет проверки: список должен действительно содержать `RenderEngine`, а root, build и устройство — совпадать. Если условие не выполнено, захват останавливается.

После этого прошли скриншоты с сохранением PID SurfaceFlinger, headless scrcpy H.264 `460×1024` за 8 секунд с 61 кадром и отдельный 5-секундный тест UHID-клавиатуры/мыши с видео. Это проверенные короткие сценарии, а не нагрузочный тест на дни. Сам бинарник SurfaceFlinger не заменяли.

Полный reboot сбросил свойство. Приватный USB-launcher повторно проверяет и применяет workaround при запуске; загрузочного сервиса для этого нет. Откат runtime-значения — вернуть сохранённый исходный backend и перезапустить графику; в этом опыте исходным был `skiagl`. Это также возвращает известный риск падения снимка.

Для scrcpy использовали официальный macOS ARM64 release `5.0.1`, сверив digest архива с релизом. Получайте актуальный совместимый выпуск у [Genymobile/scrcpy](https://github.com/Genymobile/scrcpy/releases). В приватном launcher отключены audio и clipboard autosync; PID/видеофайлы и личные экраны не публикуются.

Пример обычной видимой сессии после отдельной проверки устройства и графики:

```sh
scrcpy --serial="$SERIAL" --no-audio --no-clipboard-autosync \
  --keyboard=uhid --mouse=sdk --max-size=1280 --max-fps=30
```

У headless-проверки SDK mouse требовал video playback; для неё использовали `--mouse=uhid`. Работающая запись видео, показ окна и конкретный метод ввода — разные условия.

<a id="display-geometry"></a>

## Display geometry

Физическая панель: `720×1600`, density `320`. GSI сообщал пустой `config_mainBuiltInDisplayCutout`, radius `0`, status bar `24dp`, content padding `0` и небольшие start/end-отступы. Это не соответствовало скруглению и вырезу дисплея; часы попадали под верхний угол.

Родные значения извлекли из `DevicesAndroidOverlay` / `DevicesOverlay` конкретной stock `OS2.0.216.0.VBNMIXM`. Безопасный боковой отступ добавили отдельно:

| Target | Resource | Значение в PX | Происхождение |
|---|---|---|---|
| `android` | `rounded_corner_radius` | `86` | Stock overlay |
| `android` | `rounded_corner_radius_top` | `86` | Stock overlay |
| `android` | `rounded_corner_radius_bottom` | `86` | Stock overlay |
| `android` | `status_bar_height_default` | `74` | Stock overlay |
| `android` | `status_bar_height_portrait` | `74` | Stock overlay |
| `android` | `rounded_corner_content_padding` | `40` | Подобранный безопасный отступ для обеих сторон |
| `com.android.systemui` | `status_bar_padding_top`, config `port` | `16` | Stock SystemUI overlay |

Строковый ресурс выреза:

```text
android:string/config_mainBuiltInDisplayCutout
M 0,0 H -41 V 74 H 41 V 0 H 0 Z
```

Это центральный вырез шириной 82 и высотой 74 px. Значения заданы **в пикселях**, не в dp. Они не подходят автоматически другому разрешению, плотности, панели, ландшафтному режиму или другой версии SystemUI. Книжную ориентацию и видимость часов/правых значков проверили на экране Chrome; все ориентации и экраны не сертифицировали.

`cmd overlay fabricate` в исследованной сборке принимал ограниченный диапазон integer resource types и не позволял нужный dimension тем же способом. Поэтому [RedmiDisplay.java](../tools/RedmiDisplay.java) использует reflection к `FabricatedOverlay.setResourceValue(String, float, int, String)` с единицей PX (`0`). Два overlay принадлежат `com.android.shell` и атомарно регистрируются/включаются через `OverlayManagerTransaction` для user `0`:

- `Redmi15CDisplay` → `android`;
- `Redmi15CStatusBar` → `com.android.systemui`.

Помощник требует root, проверяет codename/build/размер/плотность и поддерживает `check`, `apply`, `remove`. `check` проверяет совместимость API/устройства, а не включённость всех ресурсов. Это исходник runtime-помощника, а не установленное приложение и не RRO-пакет для любой прошивки. Инструкции сборки и запуска: [tools/README.md](../tools/README.md).

После применения проверили lookup ресурсов и видимость часов/значков. После полного reboot fabricated-настройки в этом опыте сбросились даже при сохранённом overlays state. Для повторного применения private launcher проверяет оба overlay; пользовательский opt-out хранит отдельно и уважает. `remove` снимает именно эти два overlay. Исходный [AOSP механизм вырезов](https://source.android.com/docs/core/display/display-cutouts) описывает, почему SystemUI нужны данные физической геометрии.

## Проверки UI без чтения личных данных

Перед действием использовали свежий layout и проверку текущего пакета. На этой сборке `mCurrentFocus` находился в `dumpsys window displays` / полном выводе, но не в использованном кратком `windows`. Во время анимации UI-tree мог возвращать null root; нужно дождаться стабильного экрана, а не нажимать по старым координатам.

Владелец сам вводил Google/Instagram-данные и PIN. Для Gmail проверяли запуск Activity/процесса, без inbox dump и чтения писем. Успех запуска не означает, что все возможности приложения проверены. Для публикации не использовались реальные скриншоты с аккаунтами, уведомлениями или домашней сетью.
