# Android 15 GSI: root, LK и несовпадение SELinux-политики

[Разбор](../README.ru.md) · [Хронология](timeline.md) · [Источники](evidence.md)

## Зачем меняли работающую инженерную систему

Сервисная `251006.1.VBNCNXM.FACTORY` уже загружалась и давала root ADB. Но обычные APK GMS/Play в `/data/app` не получали требуемые `signature|privileged`-права. Вызовы падали на `MANAGE_USERS` / `CREATE_USERS`; одно development-разрешение не решало системную интеграцию.

Вариант с системными каталогами и раздельными permission allowlist подготовили офлайн, но не применяли и не называли рабочим решением. Выбранный переход использовал Google GSI ARM64 с GMS: Android 15 QPR2 `BP1A.250405.005.C1`, build `13151952`. Это образ для разработки с патчем безопасности `2025-04-05`; условия получения и использования указаны на [официальной странице GSI](https://developer.android.com/topic/generic-system-image/releases).

Правила системных привилегий описаны в [AOSP permission allowlist](https://source.android.com/docs/core/permissions/perms-allowlist). Обычный `adb install` не превращает приложение в системное privileged-приложение.

## LK: два разных кандидата, разные смещения

Во время отдельной подготовки root-пути разобрали wrapper, который сопоставлял аппаратный seccfg с дополнительным custom-состоянием. Четырёхбайтовая ветка делегировала вызов существующему getter seccfg, сохраняя его результат и обработку ошибки. Проверяли ARM control flow, стек, callee-saved регистры и отсутствие custom/RPMB-вызовов.

| Кандидат | SHA-256 исходного LK | Wrapper offset | Getter offset | Новая Thumb-ветка |
|---|---|---|---|---|
| Сервисный Android 15 | `59c265629b72c46e6d806e68313c9ce4a8732d059325820e35045c7c459b22f5` | `0x3e6e8` | `0x84014` | `45f094bc` |
| Global `2.0.216` | `fe9552f58f0fd12109ef9016112765805bd8ee1b745a0a993da4b724e0e91db3` | `0x3deb8` | `0x818d0` | `43f00abd` |

Для каждого кандидата прошёл 21 сценарий: 9 исходных комбинаций seccfg/custom, 9 после делегации и 3 отказа getter. Изменялись ровно 4 байта. Эмуляция сама по себе не доказывала принятие образа загрузочной цепочкой.

В сохранённой рабочей GSI-капсуле LK A совпадает с **Global 2.0.216-кандидатом** по полной длине кандидата. Это проверено при подготовке публикации по сохранённому файлу, без обращения к телефону. Сервисный offset `0x3e6e8` нельзя переносить в глобальный файл.

В Android A наблюдались `flash.locked=0`, orange и seccfg state `3`. Отдельная инженерная цепочка Recovery B могла сообщать locked/green. Это разные загрузочные пути; B проверен как Recovery, а не как обычный второй Android. Ранние LK-пробы до исправления DRAM не устраняли EMI ASSERT.

## Симптом GSI: init не смог создать property area

Свежий `last_kmsg` после первой попытки показывал second-stage init около 3,747 с, `invalid_context`, `Failed to initialize property area`, затем `InitFatalReboot` с signal `6`.

OEM debug platform CIL компилировался с vendor-политикой. Но объявления типов в этом debug CIL отставали от property contexts GSI. Отсутствовали 20 имён:

```text
adbd_tradeinmode_prop
bionic_linker_16kb_app_compat_prop
bluetooth_finder_prop
ctl_artd_pre_reboot_prop
ctl_prefetch_prop
ctl_uprobestats_prop
debug_tracing_desktop_mode_visible_tasks_prop
device_config_mmd_native_prop
high_barometer_quality_prop
mmd_prop
page_size_prop
pm_16kb_app_compat_prop
prefetch_boot_prop
prefetch_service_prop
remote_prov_cert_prop
system_service_enable_prop
trusty_security_vm_sys_prop
trusty_security_vm_sys_vendor_prop
virtual_face_prop
virtual_fingerprint_prop
```

Проверить ссылки property contexts на объявления типов можно [публичным офлайн-аудитором](../tools/README.md). Он дополняет компиляцию, но не заменяет `secilc`, проверку загруженной политики и реальный boot.

## Исправление: точная платформа GSI плюс отладочный su

Взяли platform CIL **установленного GSI**, затем добавили подходящие AOSP debug-атрибуты `su`, разрешение `adbd → su`, permissive только для `su` и соответствующие `dontaudit`-формы. Использованные 54 атрибута перечислены в [машиночитаемом техническом резюме](../evidence/verified-facts.json).

Общая форма существенных дополнений:

```lisp
; Each ATTR must exist in the exact platform policy.
(typeattributeset ATTR (su))
(allow adbd su (process (dyntransition)))
(typepermissive su)
```

`ATTR` выше — обозначение в объяснении, не готовый CIL. Список выводился из точных AOSP `su.te` и platform declarations; app/net-domain macros также учитывались. Имена атрибутов другой версии могут отличаться. За основу служили [AOSP QPR2 adbd.te](https://android.googlesource.com/platform/system/sepolicy/+/refs/heads/android15-qpr2-release/private/adbd.te) и [su.te](https://android.googlesource.com/platform/system/sepolicy/+/refs/heads/android15-qpr2-release/private/su.te).

Готовый точно совпадающий публичный CI-артефакт debug policy для build `13151952` получить не удалось. Поэтому результат — проверенная адаптация конкретного GSI, а не загруженная «универсальная debug policy».

## Проверки до и после записи

1. Положительный контроль `secilc` на согласованных OEM platform/vendor inputs.
2. Сравнение OEM debug CIL и точной GSI platform CIL с теми же vendor/system_ext/product/mapping inputs.
3. Проверка всех **630 различных типов** из использованных property contexts: после исправления отсутствующих типов нет. Это число типов, а не количество всех строк/свойств Android.
4. Компиляция кандидата `secilc 3.11` с выбранными входами и policy version `30`; конкретная проверочная команда использовала `-m -M true -G -N`. Поэтому она **не является доказательством прохождения neverallow**, CTS/VTS или сертификации.
5. В vendor_boot v4 заменили ровно один cpio-member: `userdebug_plat_sepolicy.cil`. Сверили остальные файлы/метаданные cpio, DTB, recovery fragment, command line и board IDs. Из-за перепаковки могли измениться контейнерные размеры/смещения; «один файл» не означает «один диапазон байтов».
6. Подготовленный vendor_boot payload имел размер 30 973 952 байта; записанный раздел — 64 МиБ. Холодное обратное чтение проверяло весь раздел, включая предусмотренное заполнение.
7. Реальная загрузка: `sys.boot_completed=1` примерно за 41,4 с, root ADB `uid=0` / `u:r:su:s0`, глобальный `Enforcing`, рабочие Activity/Wi-Fi/Locale и native boot HAL. Исправленные аппаратные BOOT-копии не изменились.

Обзор механизма debug ramdisk: [AOSP VTS with debug ramdisk](https://source.android.com/docs/core/tests/vts/vts-on-gsi). Документация описывает различия версий и современные пути выбора политики; фактическую загрузку старого OEM debug CIL в нашей конфигурации установили по собственным входам и журналам. Нельзя считать, что всякий Android 15 GSI обязательно читает именно этот файл из vendor_boot.

Глобальный `setenforce 0` не был окончательным решением. Permissive `su` здесь — намеренная отладочная возможность; она не равна обычной пользовательской политике безопасности.

## Восстановление доступа и Recovery B

Когда GSI зациклился, физический Recovery/Fastboot не появился. Рабочее upstream-рукопожатие mtkclient перехватило Preloader USB. Он отклонил прямые SRAM/BOOT_MISC-запросы, но принял загрузку RAM-кода с проверенной контрольной суммой. Минимальный код перевёл аппарат в BROM; eMMC этим не записывалась.

После чтения свежих GPT/журналов отдельно проверенный путь задал Recovery и заранее полученную native-HAL запись слота B в двух служебных секторах `misc`. Полные `misc` и seccfg сверили. Root Recovery загрузился новым ядром примерно за 32 с. Точные секторные записи относятся к этому GPT и состоянию HAL; копировать их на другой аппарат нельзя.

После успешного GSI программный переход A → Recovery B → A повторно проверили. Состояние слота меняли штатным boot HAL, а не подстановкой произвольных байтов slot metadata. FRP не стирали, eFuse/RPMB-key не программировали, PIN и Google-подтверждение проходил владелец.
