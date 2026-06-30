# Доменная модель VPN router platform

## Главная идея

Платформа продает физические роутеры с преднастроенным VPN-доступом и подпиской. Доменная модель должна строиться вокруг пользователя, устройства, подписки и выдачи доступа, а не вокруг конкретного VPN-провайдера.

WG-Easy, WireGuard, Amnezia или другой провайдер должны оставаться инфраструктурной деталью. Бизнес-домен должен описывать то, что важно для продукта: кто купил роутер, какое устройство активировано, есть ли действующая подписка, какой VPN-доступ выдан и на каком сервере он обслуживается.

```mermaid
erDiagram
    User ||--o{ Device : owns
    User ||--o{ Subscription : has
    Device ||--o{ ActivationToken : uses
    Device ||--o| VPNClient : assigned
    Subscription ||--o{ Device : covers
    VPNServer ||--o{ VPNClient : hosts

    User {
        uuid id
        string email
        string phone
        string status
        datetime created_at
    }

    Device {
        uuid id
        string serial_number
        string model
        string status
        uuid owner_user_id
        datetime activated_at
    }

    VPNClient {
        uuid id
        uuid device_id
        uuid vpn_server_id
        string provider_client_id
        string public_key
        string address
        string status
    }

    Subscription {
        uuid id
        uuid user_id
        string plan
        string status
        datetime starts_at
        datetime expires_at
    }

    ActivationToken {
        uuid id
        uuid device_id
        string token_hash
        string status
        datetime expires_at
    }

    VPNServer {
        uuid id
        string region
        string provider
        string status
        int capacity
    }
```

## User

`User` существует как владелец отношений с платформой: покупки, подписки, устройства, поддержка и биллинг.

Ответственность:

- хранить идентичность клиента;
- связывать устройства и подписки;
- быть владельцем бизнес-доступа, а не технического VPN-конфига.

Пользователь может иметь несколько роутеров, несколько подписок, семейные или бизнес-тарифы в будущем.

## Device

`Device` представляет физический роутер.

Ответственность:

- хранить серийный номер, модель и состояние устройства;
- знать, активирован ли роутер;
- быть точкой привязки VPN-доступа;
- отделять физический товар от пользователя и подписки.

Примеры статусов:

- `manufactured`
- `in_stock`
- `sold`
- `activated`
- `suspended`
- `revoked`

`Device` нужен отдельно от `VPNClient`, потому что роутер может быть продан, заменен, сброшен, переактивирован или переведен на другой VPN-сервер. VPN-клиент — это технический доступ, а устройство — бизнес-объект.

## VPNClient

`VPNClient` — доменная сущность, описывающая VPN-доступ, выданный устройству.

Ответственность:

- связать устройство с конкретным VPN-сервером;
- хранить техническую идентичность клиента у провайдера;
- управлять состоянием VPN-доступа;
- быть абстракцией над WG-Easy, WireGuard или другим провайдером.

Поле `provider_client_id` нужно, чтобы система могла работать с внешним провайдером, но не зависела от его модели напрямую.

Примеры статусов:

- `pending`
- `active`
- `disabled`
- `rotating`
- `deleted`

## Subscription

`Subscription` описывает право пользователя пользоваться сервисом.

Ответственность:

- хранить тариф, срок действия и состояние оплаты;
- определять, должен ли VPN-доступ быть активным;
- связывать коммерческую часть с устройствами.

Примеры статусов:

- `trial`
- `active`
- `past_due`
- `expired`
- `cancelled`

Подписка не должна быть просто флагом на устройстве. В будущем могут появиться один тариф на несколько устройств, семейный план, корпоративный аккаунт и разные лимиты скорости, регионов или серверов.

## ActivationToken

`ActivationToken` нужен для безопасной активации роутера пользователем.

Ответственность:

- подтвердить, что устройство действительно принадлежит покупателю или партии продажи;
- позволить активировать устройство без ручной настройки;
- ограничить срок и количество использований;
- предотвратить повторную или чужую активацию.

Типичный flow:

```mermaid
sequenceDiagram
    participant U as User
    participant API as Platform API
    participant D as Device
    participant VPN as VPN Provider

    U->>API: Вводит activation token
    API->>API: Проверяет токен
    API->>API: Привязывает Device к User
    API->>API: Проверяет Subscription
    API->>VPN: Создает VPNClient
    VPN-->>API: Возвращает VPN configuration
    API->>D: Передает конфигурацию или делает ее доступной
    API-->>U: Устройство активировано
```

## VPNServer

`VPNServer` представляет сервер или узел, на котором создаются VPN-клиенты.

Ответственность:

- хранить регион, провайдера, емкость и состояние;
- помогать выбирать сервер для нового устройства;
- отслеживать нагрузку и доступность;
- позволить масштабирование на несколько стран и дата-центров.

Примеры статусов:

- `active`
- `draining`
- `maintenance`
- `offline`

`VPNServer` не обязан быть физическим сервером. Это может быть logical node, endpoint, WG-Easy instance, кластер или региональный пул.

## Ключевые связи

```mermaid
flowchart TD
    User["User<br/>клиент платформы"]
    Subscription["Subscription<br/>право пользоваться сервисом"]
    Device["Device<br/>физический роутер"]
    ActivationToken["ActivationToken<br/>безопасная активация"]
    VPNClient["VPNClient<br/>технический VPN-доступ"]
    VPNServer["VPNServer<br/>сервер или пул VPN"]

    User --> Subscription
    User --> Device
    ActivationToken --> Device
    Subscription --> Device
    Device --> VPNClient
    VPNClient --> VPNServer
```

## Будущая масштабируемость

Для будущего важно держать границы домена:

- `VPNProvider` остается интерфейсом: WG-Easy сегодня, другой провайдер завтра.
- `Device` не зависит от конкретного VPN-протокола.
- `VPNClient` не должен быть равен WireGuard peer напрямую, это доменная абстракция доступа.
- `Subscription` управляет правом доступа, но не хранит техническую конфигурацию.
- `VPNServer` позволяет балансировать новых клиентов по регионам, нагрузке и тарифам.
- `ActivationToken` позволяет масштабировать продажи через маркетплейсы, партнеров и преднастроенные партии устройств.

В будущем можно добавить:

- `Order` для покупки;
- `Plan` для тарифов;
- `Invoice` или `Payment`;
- `DeviceModel`;
- `FirmwareVersion`;
- `RouterProvisioningJob`;
- `Region`;
- `ServerPool`;
- `SupportTicket`;
- `AuditLog`.

Главная архитектурная мысль: бизнес-модель должна строиться вокруг пользователя, устройства и подписки, а VPN-провайдер должен быть заменяемым механизмом выдачи доступа.
