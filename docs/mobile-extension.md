# Mobile Extension Strategy — FlashLang

## Overview
The FlashLang backend is designed so that iOS, Android, and React Native clients can connect
without any backend changes. This document describes the path to a mobile app.

---

## Why No Backend Changes Are Needed

The REST API uses:
- `Authorization: Bearer <accessToken>` header — works identically in all HTTP clients
- HttpOnly `refresh_token` cookie — all native HTTP clients support cookie jars
- JSON request/response — universal
- Standard HTTP status codes — universal

Mobile apps simply set the `Authorization` header and enable cookie persistence on their HTTP
client (e.g., `URLSession` on iOS, `OkHttp` on Android, `axios` in React Native).

---

## React Native Implementation Path

### Navigation
Replace `react-router-dom` with `@react-navigation/native`:
```
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
```
Route mapping:
| Web (react-router) | Mobile (react-navigation) |
|---|---|
| `/login` | `AuthStack > LoginScreen` |
| `/sets` | `MainTab > SetsScreen` |
| `/sets/:id` | `MainStack > SetDetailScreen` |
| `/learn/session/:id` | `MainStack > SessionPlayScreen` |
| `/stats` | `MainTab > StatsScreen` |

### Card Flip Animation
Replace CSS 3D transform with `react-native-reanimated`:
```typescript
import Animated, { useSharedValue, withTiming, interpolate } from 'react-native-reanimated'

const rotateY = useSharedValue(0)
const flip = () => { rotateY.value = withTiming(rotateY.value === 0 ? 180 : 0, { duration: 500 }) }

// Front face style
const frontStyle = useAnimatedStyle(() => ({
  transform: [{ rotateY: `${interpolate(rotateY.value, [0, 180], [0, 180])}deg` }],
  backfaceVisibility: 'hidden',
}))
// Back face style
const backStyle = useAnimatedStyle(() => ({
  transform: [{ rotateY: `${interpolate(rotateY.value, [0, 180], [180, 360])}deg` }],
  backfaceVisibility: 'hidden',
}))
```

### State Management
Zustand and TanStack React Query are fully portable — they have no DOM dependencies:
```
npm install zustand @tanstack/react-query
```
The `auth.store.ts` and `session.store.ts` files can be copied directly.

### API Client
The `api/client.ts` fetch wrapper needs one change: replace `fetch` with a React Native
compatible client. `fetch` is available in React Native, so minimal changes are needed.
Replace `import.meta.env.VITE_API_URL` with a React Native config package:
```typescript
import Config from 'react-native-config'
const BASE_URL = Config.API_URL ?? 'http://10.0.2.2:3000' // Android emulator localhost
```

### Offline Support (Future)
For offline-first functionality:
```
npm install @tanstack/react-query-persist-client @tanstack/query-async-storage-persister
npm install @react-native-async-storage/async-storage
```
Cards due for review can be cached locally. Reviews submitted while offline queue in
AsyncStorage and sync when connectivity is restored.

---

## Flutter Implementation Path

Flutter communicates via `http` or `dio` package — the REST API is unchanged.

```dart
// pubspec.yaml
dependencies:
  http: ^1.2.0
  shared_preferences: ^2.2.2  // for token storage
  flutter_secure_storage: ^9.0.0  // for refresh token cookie equivalent
```

Card flip in Flutter uses `AnimationController` with `Transform`:
```dart
AnimationController(duration: Duration(milliseconds: 500), vsync: this)
Transform(
  transform: Matrix4.rotationY(animation.value * pi),
  child: frontFace,
)
```

---

## Shared Code Strategy (Future Monorepo)

When adding mobile, extract shared logic into a monorepo:

```
/packages
  /srs-engine          # SpacedRepetitionService as pure TS (no NestJS dependency)
    src/index.ts       # export { calculateNext, SRCard, SRResult }
  /shared-types        # API response interfaces (mirrors frontend/src/api/types.ts)
    src/index.ts       # export all types
/backend               # imports @flashlang/srs-engine, @flashlang/shared-types
/frontend              # imports @flashlang/shared-types
/mobile                # imports @flashlang/srs-engine, @flashlang/shared-types
```

The `SpacedRepetitionService.calculateNext` method is already a pure function — extracting
it to a shared package requires only removing the `@Injectable()` decorator.

---

## API Versioning for Mobile

Mobile apps cannot be force-updated immediately, so the API must remain stable.

Current approach (sufficient for v1):
- Base path `/` — no versioning prefix
- Additive changes only: new optional fields, new endpoints
- Never remove or rename existing fields

When breaking changes become necessary:
- Add `/v2/` prefix to new endpoints
- Keep `/v1/` (current) alive during deprecation window
- NestJS supports this via `app.setGlobalPrefix('v1')` or per-module prefix

---

## Push Notifications (Future)

Study reminders ("You have 12 cards due today") require a push notification service:

| Platform | Service |
|---|---|
| iOS + Android | Firebase Cloud Messaging (FCM) |
| Backend integration | `@nestjs/schedule` cron job runs daily, queries `dueToday` per user, sends via FCM |
| Token storage | Add `device_tokens` table: `user_id`, `token`, `platform`, `created_at` |

The cron job approach requires no changes to existing endpoints.
