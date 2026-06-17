# QWeather JWT keys

Place your Ed25519 key pair here for weather tools (`get_weather`, `get_region`).

| File | Commit to git? |
|------|----------------|
| `ed25519-private.pem` | **No** (gitignored) |
| `ed25519-public.pem` | Optional (register public key in QWeather console) |

Configure in `.env`:

```env
QWEATHER_HOST=your-api-host.qweatherapi.com
QWEATHER_KID=your-credential-id
QWEATHER_PROJECT_ID=your-project-id
QWEATHER_PRIVATE_KEY_PATH=./qweather_key/ed25519-private.pem
```
