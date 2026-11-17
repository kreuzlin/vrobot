# Optional Caddy snippets

Every `*.caddy` file in this directory is imported into the site block of
`deploy/Caddyfile`. Real snippets are server-specific and not committed
(see `.gitignore`).

## Example: Basic Auth (currently not used)

`www2` runs without a password during the test phase (maintainer decision).
Should that change, protect the whole site like this:

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
