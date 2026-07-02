# Roadmap проекта vpn-platform

Этот roadmap фиксирует текущее состояние архитектуры `vpn-platform`, уже закрытые слои и следующие этапы. Документ является checkpoint после реализации `Device Registry`, `Device Activation`, `Device Ownership` и `Device VPN Assignment`.

## Правило работы с внешними материалами

Сторонние прошивки, скрипты, пакеты, бинарные файлы, изображения, тексты, конфигурации и другие assets можно использовать как источники знаний и ссылок, но нельзя копировать в репозиторий, пока не проверены лицензия, условия использования и явное разрешение на хранение или модификацию.

## Общая цель проекта

`vpn-platform` - это managed VPN-router platform.

Целевой пользовательский сценарий:

1. Клиент получает заранее подготовленный роутер.
2. Клиент подключает питание и интернет-кабель.
3. Устройство активируется и привязывается к аккаунту.
4. Платформа назначает VPN-доступ.
5. Позже `router agent` получает assigned VPN profile/config, применяет его на OpenWrt и отправляет heartbeat/status/diagnostics.

Для пользователя продукт должен выглядеть как готовый роутер, который работает без ручной настройки WireGuard, WG-Easy, DNS, routing и fallback profiles. Внутри архитектуры эти слои должны оставаться разделенными, чтобы платформу можно было развивать без переписывания домена.

## Ключевые архитектурные принципы

- `Device` - физический роутер, а не WireGuard peer.
- `Device` нельзя жестко связывать с WG-Easy.
- WG-Easy может быть текущим provider-ом, но только за абстракцией `VPNProvider`.
- Платформа должна поддерживать multi-protocol направление через `ProtocolProfile`.
- WireGuard - MVP/default profile.
- AmneziaWG и OpenVPN TCP/443 - возможные fallback-кандидаты, но не обещанное поведение MVP.
- Нельзя обещать пользователю "неблокируемый VPN". Блокировки зависят от ISP, региона, DPI rules, портов, traffic profile и времени.
- OpenWrt - основная router platform для MVP.
- Xiaomi Mi Router 4A Gigabit Edition - primary budget MVP hardware target, но backend не должен быть hardcoded только под Xiaomi.
- Activation token не хранится в plain text. Хранится только hash, а plain token возвращается только один раз при генерации.
- Текущие repositories являются process-local. DB/migrations и persistent storage должны быть отдельным будущим решением.

## Уже закрытые слои

### Research / Protocol Strategy

Назначение: описать стратегию VPN-протоколов и избежать жесткой привязки продукта к одному протоколу.

Что сделано:

- зафиксирован MVP/default profile на WireGuard;
- описаны fallback-кандидаты AmneziaWG и OpenVPN TCP/443;
- введена идея `ProtocolProfile`;
- зафиксировано, что блокировки протоколов являются изменяющимся сетевым риском.

Что не входило в scope:

- реализация fallback logic;
- router-side автоматическое переключение;
- обещание, что какой-либо VPN protocol является unblockable.

### ISP Compatibility Database research

Назначение: описать будущую базу знаний по совместимости ISP, router models, firmware, protocol profiles и performance.

Что сделано:

- описаны поля будущей совместимости;
- зафиксированы источники данных: lab testing, support cases, onboarding diagnostics, будущая router agent telemetry;
- описано, как эти данные помогут выбирать protocol profile и hardware.

Что не входило в scope:

- база данных;
- сбор telemetry;
- автоматические рекомендации backend.

### Device Registry Architecture

Назначение: отделить физический роутер от VPN peer/client.

Что сделано:

- зафиксировано, что `Device` - физическое устройство;
- описаны статусы устройства и activation status;
- описаны OpenWrt metadata и hardware fields;
- зафиксировано, что Device Registry не должен знать детали WG-Easy API.

Что не входило в scope:

- DB/migrations;
- router agent;
- heartbeat;
- VPN config delivery.

### Device Registry Backend CRUD v1

Назначение: дать backend-основу для учета физических роутеров.

Что сделано:

- добавлен CRUD для `Device`;
- добавлены поля статуса, activation status, owner placeholder и hardware metadata;
- `DELETE /devices/{device_id}` переводит устройство в `retired`, а не удаляет физически;
- storage реализован как временный process-local repository.

Что не входило в scope:

- база данных;
- authentication/authorization;
- router agent;
- subscription checks;
- WG-Easy integration.

### Device Activation Architecture

Назначение: описать безопасный допуск физического роутера в управляемую платформу.

Что сделано:

- отделена activation от VPN profile assignment;
- описаны activation token, future device secret и activation attempts;
- зафиксировано, что activation не должна зависеть от WG-Easy, WireGuard или billing.

Что не входило в scope:

- backend implementation;
- router-agent activation endpoint;
- heartbeat;
- VPN config delivery.

### Device Activation Backend v1

Назначение: добавить минимальный backend flow для активации устройства.

Что сделано:

- добавлены activation tokens;
- plain token не хранится;
- хранится только token hash;
- plain token возвращается только один раз при генерации;
- добавлены endpoints для генерации, revoke, manual activation и activation by token;
- storage реализован как process-local repository.

Что не входило в scope:

- device secret;
- router agent;
- heartbeat;
- VPN config delivery;
- subscription/billing;
- persistent storage.

### MVP Hardware Target

Назначение: зафиксировать primary budget hardware target для MVP.

Что сделано:

- выбран Xiaomi Mi Router 4A Gigabit Edition как primary budget MVP hardware target;
- зафиксирована OpenWrt direction;
- описаны hardware risks, flashing risks, recovery path и performance validation;
- зафиксировано, что выбор нужно проверить перед bulk purchase/customer rollout.

Что не входило в scope:

- закупка устройств;
- прошивка устройств;
- хранение firmware files;
- hardcode backend только под Xiaomi.

### Device Ownership / Assignment v1

Назначение: назначать физическое устройство customer/account/user placeholder через существующее поле `owner_user_id`.

Что сделано:

- добавлены endpoints для assign owner и unassign owner;
- добавлен список устройств по `owner_user_id`;
- ownership не смешан с activation, subscription, billing или VPN assignment.

Что не входило в scope:

- `User`, `Customer` или `Account` model;
- authentication/authorization;
- subscription checks;
- billing.

### Device VPN Assignment Architecture

Назначение: описать слой, который связывает физический `Device` с VPN-доступом через `VPNProvider`.

Что сделано:

- зафиксирована цепочка `Device -> DeviceOwnership -> DeviceActivation -> DeviceVPNAssignment -> VPNProvider -> VPNClient / VPNProfile`;
- описаны `DeviceVPNAssignment`, `ProtocolProfile`, `VPNClientRef`;
- запрещено добавлять WG-Easy поля напрямую в `Device`;
- описаны rules create/revoke и будущий API-контур.

Что не входило в scope:

- backend implementation;
- raw VPN config delivery;
- router agent;
- heartbeat;
- billing/subscription;
- DB/migrations.

### Device VPN Assignment Backend v1

Назначение: реализовать минимальное назначение VPN-доступа физическому устройству.

Что сделано:

- добавлена отдельная сущность `DeviceVPNAssignment`;
- добавлены `ProtocolProfile` и `VPNClientRef`;
- добавлен process-local repository для assignments;
- добавлен `DeviceVPNAssignmentService`;
- сервис работает через `VPNProvider`, а не через WG-Easy client;
- добавлены endpoints:
  - `POST /devices/{device_id}/vpn-assignment`;
  - `GET /devices/{device_id}/vpn-assignment`;
  - `POST /devices/{device_id}/vpn-assignment/revoke`;
  - `GET /vpn-assignments/by-owner/{owner_user_id}`;
- responses возвращают только safe metadata.

Что не входило в scope:

- raw VPN config;
- private key;
- provider secrets;
- activation token;
- device secret;
- router agent;
- heartbeat;
- DB/migrations;
- billing/subscription.

### VPN Assignment Review / API Smoke Test

Назначение: проверить основной API flow для `Device VPN Assignment Backend v1`.

Что сделано:

- проверена компиляция backend;
- проверен `git diff --check`;
- через FastAPI `TestClient` проверен сценарий:
  - создание test device;
  - assign owner;
  - создание VPN assignment;
  - duplicate assignment error;
  - получение active assignment;
  - список по owner;
  - revoke assignment;
  - отсутствие active assignment после revoke;
  - сохранение `Device.owner_user_id`;
  - сохранение `Device.activation_status`;
  - сохранение физического `Device`;
  - ошибки для missing device, device without owner, disabled и retired devices.

Что не входило в scope:

- добавление постоянных test files в репозиторий;
- integration test с реальным WG-Easy;
- raw VPN config delivery.

## Текущая архитектурная цепочка

Текущая backend-цепочка:

```text
Device -> DeviceOwnership -> DeviceActivation -> DeviceVPNAssignment -> VPNProvider -> VPNClient / VPNProfile
```

Будущая router-side цепочка:

```text
Router Agent -> assigned VPN profile/config -> OpenWrt apply -> heartbeat/status/diagnostics
```

Эти цепочки связаны, но `router agent` пока не реализован. Backend уже может хранить физические устройства, owner assignment, activation state и VPN assignment metadata. Но устройство пока не умеет самостоятельно получать config, применять его на OpenWrt и отправлять heartbeat/status/diagnostics.

## Границы между слоями

### Device Registry

Хранит физические устройства, статусы, owner placeholder и hardware metadata. Не является WireGuard peer и не хранит WG-Easy fields.

### Device Activation

Отвечает за безопасный допуск устройства в платформу. Не создает VPN assignment автоматически и не выдает raw VPN config.

### Device Ownership

Связывает физическое устройство с customer/account/user placeholder через `owner_user_id`. Не является subscription и не проверяет billing.

### Device VPN Assignment

Связывает `Device` с VPN-доступом через `VPNProvider`. Не меняет `Device.activation_status`, не меняет `Device.owner_user_id` и не удаляет физический device.

### VPNProvider

Абстракция над конкретным provider-ом. WG-Easy находится за этой границей и не должен протекать в Device domain.

### ProtocolProfile

Описывает выбранный VPN profile/protocol. Нужен для multi-protocol развития и будущих fallback profiles.

### Router Agent

Будущий компонент на роутере. Должен получать assigned VPN profile/config, применять его на OpenWrt и отправлять diagnostics. Пока отсутствует.

### Heartbeat

Будущий поток статуса устройства. Не должен смешиваться с assignment creation/revoke.

### Billing/Subscription

Будущий коммерческий слой права на VPN-доступ. Не участвует в текущем assignment backend v1 и не должен смешиваться с Device Registry.

### Persistence/DB

Будущий слой хранения. Текущие process-local repositories являются MVP-ограничением и не подходят для production.

## Текущий технический статус

- backend существует;
- Device Registry CRUD существует;
- Device Activation существует;
- Device Ownership существует;
- Device VPN Assignment существует;
- smoke test по VPN Assignment пройден;
- raw VPN config не выдается;
- private key и provider secrets не возвращаются;
- router agent отсутствует;
- heartbeat отсутствует;
- billing/subscription отсутствуют;
- DB/migrations отсутствуют;
- process-local repositories являются временным MVP-ограничением.

## Предлагаемые следующие этапы

### A. Router Agent Architecture

Цель: описать обязанности будущего `router agent` до реализации.

Нужно зафиксировать:

- что agent делает на OpenWrt;
- как agent получает assigned VPN profile/config;
- как применяет конфигурацию;
- какие операции входят в MVP;
- какие операции считаются опасными и требуют отдельного решения.

Критерий готовности:

- есть отдельный architecture document;
- agent не смешан с Device Registry, Activation, Assignment и Billing;
- описаны MVP-ограничения.

### B. Device Secret / Agent Authentication Architecture

Цель: отделить activation token от long-lived device secret.

Нужно зафиксировать:

- activation token используется для первичного допуска;
- device secret используется для дальнейшей авторизации agent;
- secrets не хранятся в plain text;
- нужны rotation/revoke сценарии;
- raw secret возвращается только в контролируемый момент.

Критерий готовности:

- описана модель device secret;
- описаны hash, rotation и revoke;
- понятна связь с будущим router agent.

### C. Router Agent Heartbeat Architecture

Цель: описать heartbeat/status/diagnostics без смешивания с VPN assignment.

Нужно зафиксировать:

- online/offline;
- `last_seen_at`;
- firmware/openwrt version;
- diagnostics;
- network status;
- связь с support flow.

Критерий готовности:

- heartbeat не создает assignment;
- heartbeat не проверяет billing;
- heartbeat не выдает raw VPN config.

### D. Persistence / DB Architecture

Цель: подготовить переход от process-local repositories к persistent storage.

Нужно описать перенос:

- `Device`;
- `DeviceActivationToken`;
- `DeviceVPNAssignment`;
- future `DeviceSecret`;
- future `ProtocolProfile`;
- future audit/events.

Нужно зафиксировать atomic operations:

- activation token validation и marking as used;
- assignment creation и active assignment uniqueness;
- assignment revoke и provider operation reconciliation.

Критерий готовности:

- выбрана storage strategy;
- описаны migrations;
- описаны uniqueness constraints и transaction boundaries.

### E. Subscription / Billing Architecture

Цель: описать будущую проверку права на VPN-доступ.

Нужно зафиксировать:

- subscription не является Device Registry;
- billing не является Device Activation;
- billing не должен напрямую зависеть от WG-Easy;
- subscription может влиять на право создавать или сохранять active VPN assignment;
- grace period, cancel и failed payment должны быть отдельными бизнес-сценариями.

Критерий готовности:

- описана доменная модель subscription;
- описана связь с assignment policy;
- не смешаны технический VPN client и коммерческая оплата.

## Anti-goals

Сейчас нельзя:

- делать `Device = WireGuard peer`;
- добавлять WG-Easy поля в `Device`;
- добавлять `wireguard_peer_id`, `wg_easy_client_id` или `vpn_config` в `Device`;
- выдавать raw VPN config по `device_id`;
- смешивать activation и assignment;
- смешивать assignment и billing;
- добавлять `router agent` без отдельной архитектуры;
- добавлять heartbeat без отдельной архитектуры;
- добавлять DB/migrations без отдельного решения;
- хардкодить backend только под Xiaomi Mi Router 4A Gigabit Edition;
- обещать "неблокируемый VPN";
- копировать сторонние firmware, scripts, packages или assets без проверки лицензии и разрешения.

## Общий принцип

Backend, provisioning и router-side logic должны развиваться независимо. Продуктовая модель должна оставаться устойчивой при замене WG-Easy, WireGuard, конкретной модели роутера, OpenWrt package set или способа прошивки.

Следующий архитектурный шаг должен быть `Router Agent Architecture` или `Device Secret / Agent Authentication Architecture`, потому что backend уже умеет создать assignment metadata, но роутер пока не имеет безопасного канала для получения и применения assigned VPN profile/config.
