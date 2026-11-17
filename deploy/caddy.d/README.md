# Optional Caddy snippets

Every `*.caddy` file in this directory is imported into the site block of
`deploy/Caddyfile`. Real snippets are server-specific and not committed
(see `.gitignore`).

## Basic Auth (test phase)

Protect the whole site with a password, e.g. on `www2` before go-live:

```bash
docker compose -f compose.prod.yaml exec caddy caddy hash-password
# paste the hash into deploy/caddy.d/basic-auth.caddy:
```

```caddy
basic_auth {
	vrobot <hash>
}
```

Then reload: `docker compose -f compose.prod.yaml restart caddy`.
Remove the file again at go-live.
